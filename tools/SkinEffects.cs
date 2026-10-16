// Optional product companion. Self-test does not access Win32, audio or VLC.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Media;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

namespace NfsSkinSupport
{
    public sealed class Dimensions { public int width; public int height; }
    public sealed class HoverSpec { public int width; public int height; public int closedWidth; public int closedHeight; }
    public sealed class CommandSpec { public int width; public int height; public int showX; public int hideX; public int y; public int volumeShowX; public int volumeHideX; }
    public sealed class SoundSpec { public string id; public string file; public int width; public int readyWidth; public int height; }
    public sealed class Manifest
    {
        public int schemaVersion;
        public int scale;
        public SoundSpec[] sounds;
        public CommandSpec command;
        public HoverSpec hover;
        public Dimensions video;
        internal static readonly Dictionary<string, string> Allowed = new Dictionary<string, string> {
            {"button", "sounds/button.wav"}, {"shutter", "sounds/shutter.wav"},
            {"intro", "sounds/intro4.wav"}, {"info", "sounds/imode.wav"}, {"logo", "sounds/eagames.wav"}
        };
        public void Validate()
        {
            Require((schemaVersion == 1 || schemaVersion == 2) && (scale == 1 || scale == 2), "Unsupported effects manifest version or scale.");
            Require(sounds != null && sounds.Length == 5, "Exactly five original sound signals are required.");
            var ids = new HashSet<string>(); var widths = new HashSet<int>();
            foreach (var sound in sounds)
            {
                string file;
                Require(sound != null && sound.id != null && Allowed.TryGetValue(sound.id, out file), "Unknown sound signal.");
                Require(sound.file == Allowed[sound.id] && ids.Add(sound.id), "Sound files must use the original whitelist once each.");
                Require(sound.height == 17 && sound.width >= 51 && sound.width <= 55 && sound.readyWidth == sound.width - 10 && widths.Add(sound.width), "Sound ready/trigger geometry must be unique.");
            }
            Require(command != null && command.width == (schemaVersion == 2 ? 133 : 67) && command.height == 17 && command.showX == 2 && command.hideX == 35 && command.y == 2, "Invalid hover command geometry.");
            Require(schemaVersion == 1 ? command.volumeShowX == 0 && command.volumeHideX == 0 : command.volumeShowX == 68 && command.volumeHideX == 101, "Invalid volume hover commands.");
            Require(hover != null && hover.width == (schemaVersion == 2 ? 361 : 426 * scale) && hover.height == (schemaVersion == 2 ? 64 : 146 * scale), "Invalid framed hover geometry.");
            Require(hover.closedWidth == (schemaVersion == 2 ? 362 : 427 * scale) && hover.closedHeight == (schemaVersion == 2 ? 1 : scale), "Invalid transparent closed hover geometry.");
            Require(video != null && video.width == 708 * scale && video.height == 440 * scale, "Invalid initial video geometry.");
        }
        internal static void Require(bool condition, string message) { if (!condition) throw new InvalidDataException(message); }
    }

    internal sealed class Assets : IDisposable
    {
        internal Manifest Manifest;
        internal readonly Dictionary<string, string> Files = new Dictionary<string, string>();
        private string directory;
        internal static Assets Open(string path)
        {
            var result = new Assets();
            try
            {
                using (var archive = ZipFile.OpenRead(path))
                {
                    var entries = archive.Entries.Where(e => e.FullName == "nfs-effects.json").ToArray();
                    Manifest.Require(entries.Length == 1 && entries[0].Length <= 65536, "Missing or oversized effects manifest.");
                    string json;
                    using (var reader = new StreamReader(entries[0].Open())) json = reader.ReadToEnd();
                    result.Manifest = new JavaScriptSerializer { MaxJsonLength = 65536 }.Deserialize<Manifest>(json);
                    Manifest.Require(result.Manifest != null, "Invalid effects manifest.");
                    result.Manifest.Validate();
                    result.directory = Path.Combine(Path.GetTempPath(), "NfsSkinEffects-" + Guid.NewGuid().ToString("N"));
                    Directory.CreateDirectory(result.directory);
                    foreach (var spec in result.Manifest.sounds)
                    {
                        var matches = archive.Entries.Where(e => e.FullName == spec.file).ToArray();
                        Manifest.Require(matches.Length == 1 && matches[0].Length >= 12 && matches[0].Length <= 4 * 1024 * 1024, "Missing, duplicate or oversized original sound.");
                        // Destination uses a fixed whitelist ID, never an archive path.
                        string destination = Path.Combine(result.directory, spec.id + ".wav");
                        result.Files.Add(spec.id, destination);
                        using (var input = matches[0].Open())
                        using (var output = new FileStream(destination, FileMode.CreateNew, FileAccess.Write))
                        {
                            var buffer = new byte[8192]; int count; long total = 0;
                            while ((count = input.Read(buffer, 0, buffer.Length)) > 0)
                            {
                                total += count;
                                Manifest.Require(total <= 4 * 1024 * 1024, "Sound exceeded extraction limit.");
                                output.Write(buffer, 0, count);
                            }
                            Manifest.Require(total == matches[0].Length, "Truncated original sound.");
                        }
                        using (var input = File.OpenRead(destination))
                        {
                            var header = new byte[12]; Manifest.Require(input.Read(header, 0, 12) == 12, "Truncated WAV header.");
                            Manifest.Require(System.Text.Encoding.ASCII.GetString(header, 0, 4) == "RIFF" && System.Text.Encoding.ASCII.GetString(header, 8, 4) == "WAVE", "Original sound is not a WAV file.");
                        }
                    }
                }
                return result;
            }
            catch { result.Dispose(); throw; }
        }
        public void Dispose()
        {
            // No recursive deletion: remove only the five files this instance wrote.
            foreach (string file in Files.Values) try { File.Delete(file); } catch (IOException) { } catch (UnauthorizedAccessException) { }
            if (directory != null) try { Directory.Delete(directory, false); } catch (IOException) { } catch (UnauthorizedAccessException) { }
        }
    }

    internal static class Native
    {
        [StructLayout(LayoutKind.Sequential)] internal struct Rect { internal int Left, Top, Right, Bottom; internal int Width { get { return Right - Left; } } internal int Height { get { return Bottom - Top; } } internal bool Contains(Point p) { return p.X >= Left && p.X < Right && p.Y >= Top && p.Y < Bottom; } }
        [StructLayout(LayoutKind.Sequential)] internal struct MonitorInfo { internal int Size; internal Rect Monitor; internal Rect Work; internal uint Flags; }
        [StructLayout(LayoutKind.Sequential)] internal struct GuiThreadInfo
        {
            internal int Size; internal uint Flags;
            internal IntPtr Active, Focus, Capture, MenuOwner, MoveSize, Caret;
            internal Rect CaretRect;
        }
        internal delegate bool EnumCallback(IntPtr hwnd, IntPtr argument);
        [DllImport("user32.dll")] internal static extern bool EnumWindows(EnumCallback callback, IntPtr argument);
        [DllImport("user32.dll")] internal static extern bool EnumChildWindows(IntPtr parent, EnumCallback callback, IntPtr argument);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] internal static extern int GetClassName(IntPtr hwnd, System.Text.StringBuilder name, int count);
        [DllImport("user32.dll")] internal static extern IntPtr GetWindow(IntPtr hwnd, uint command);
        [DllImport("user32.dll")] internal static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
        [DllImport("user32.dll")] internal static extern bool GetGUIThreadInfo(uint thread, ref GuiThreadInfo info);
        [DllImport("user32.dll")] internal static extern bool GetWindowRect(IntPtr hwnd, out Rect rect);
        [DllImport("user32.dll")] internal static extern bool IsWindowVisible(IntPtr hwnd);
        [DllImport("user32.dll")] internal static extern bool IsIconic(IntPtr hwnd);
        [DllImport("user32.dll")] internal static extern IntPtr WindowFromPoint(Point point);
        [DllImport("user32.dll")] internal static extern bool IsWindow(IntPtr hwnd);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] internal static extern bool SetProp(IntPtr hwnd, string name, IntPtr value);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] internal static extern IntPtr GetProp(IntPtr hwnd, string name);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] internal static extern IntPtr RemoveProp(IntPtr hwnd, string name);
        [DllImport("user32.dll")] internal static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] internal static extern bool GetCursorPos(out Point point);
        [DllImport("user32.dll")] internal static extern IntPtr GetAncestor(IntPtr hwnd, uint flags);
        [DllImport("user32.dll")] internal static extern IntPtr MonitorFromWindow(IntPtr hwnd, uint flags);
        [DllImport("user32.dll")] internal static extern IntPtr MonitorFromPoint(Point point, uint flags);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] internal static extern int GetWindowText(IntPtr hwnd, System.Text.StringBuilder text, int count);
        [DllImport("user32.dll", CharSet = CharSet.Auto)] internal static extern bool GetMonitorInfo(IntPtr monitor, ref MonitorInfo info);
        [DllImport("user32.dll")] internal static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int width, int height, uint flags);
        [DllImport("user32.dll")] internal static extern bool PostMessage(IntPtr hwnd, uint message, IntPtr wParam, IntPtr lParam);
        [DllImport("user32.dll")] internal static extern bool SetProcessDPIAware();
        [DllImport("user32.dll")] internal static extern int GetWindowRgn(IntPtr hwnd, IntPtr region);
        [DllImport("gdi32.dll")] internal static extern IntPtr CreateRectRgn(int left, int top, int right, int bottom);
        [DllImport("gdi32.dll")] internal static extern bool PtInRegion(IntPtr region, int x, int y);
        [DllImport("gdi32.dll")] internal static extern bool DeleteObject(IntPtr value);
        [DllImport("user32.dll", EntryPoint = "GetWindowLongW")] private static extern int GetWindowLong32(IntPtr hwnd, int index);
        [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW")] private static extern IntPtr GetWindowLong64(IntPtr hwnd, int index);
        [DllImport("user32.dll", EntryPoint = "SetWindowLongW")] private static extern int SetWindowLong32(IntPtr hwnd, int index, int value);
        [DllImport("user32.dll", EntryPoint = "SetWindowLongPtrW")] private static extern IntPtr SetWindowLong64(IntPtr hwnd, int index, IntPtr value);
        [DllImport("user32.dll")] private static extern bool SetLayeredWindowAttributes(IntPtr hwnd, uint key, byte alpha, uint flags);
        [DllImport("user32.dll")] private static extern bool GetLayeredWindowAttributes(IntPtr hwnd, out uint key, out byte alpha, out uint flags);
        internal static long ReadStyle(IntPtr hwnd, int index) { return IntPtr.Size == 8 ? GetWindowLong64(hwnd, index).ToInt64() : GetWindowLong32(hwnd, index); }
        internal static bool SetOwner(IntPtr hwnd, IntPtr owner)
        {
            if (IntPtr.Size == 8) SetWindowLong64(hwnd, -8, owner);
            else SetWindowLong32(hwnd, -8, owner.ToInt32());
            return GetWindow(hwnd, 4) == owner;
        }
        internal static bool SetBarOpacity(IntPtr hwnd)
        {
            long style = IntPtr.Size == 8 ? GetWindowLong64(hwnd, -20).ToInt64() : GetWindowLong32(hwnd, -20);
            if ((style & 0x80000) == 0)
            {
                if (IntPtr.Size == 8) SetWindowLong64(hwnd, -20, new IntPtr(style | 0x80000));
                else SetWindowLong32(hwnd, -20, (int)(style | 0x80000));
            }
            uint key, flags; byte alpha;
            if ((style & 0x80000) != 0 && GetLayeredWindowAttributes(hwnd, out key, out alpha, out flags) && alpha == 255 && flags == 2) return false;
            SetLayeredWindowAttributes(hwnd, 0, 255, 2);
            return true;
        }
    }

    internal static class RuntimeTrust
    {
        internal static string Absolute(string path)
        {
            Manifest.Require(Diagnostics.IsAbsolute(path), "VLC executable paths must be explicit and absolute.");
            return Path.GetFullPath(path);
        }
        internal static bool SamePath(string first, string second) { return String.Equals(first, second, StringComparison.OrdinalIgnoreCase); }
        internal static bool Installed(string path)
        {
            var roots = new[] { Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), Environment.GetEnvironmentVariable("ProgramW6432") };
            return roots.Where(p => !String.IsNullOrEmpty(p)).Any(p => SamePath(path, Path.GetFullPath(Path.Combine(p, "VideoLAN", "VLC", "vlc.exe"))));
        }
        internal static string Hash(string path)
        {
            using (var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
            using (var hash = SHA256.Create()) return BitConverter.ToString(hash.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
        }
        internal static bool Layout(string executable, string hash)
        {
            if (hash == null || hash.Length != 64 || hash.Any(c => !(c >= '0' && c <= '9') && !(c >= 'a' && c <= 'f'))) return false;
            var directory = Path.GetDirectoryName(executable);
            return String.Equals(Path.GetFileName(executable), "vlc.exe", StringComparison.OrdinalIgnoreCase) &&
                String.Equals(Path.GetFileName(directory), hash, StringComparison.OrdinalIgnoreCase) &&
                String.Equals(Path.GetFileName(Path.GetDirectoryName(directory)), "VlcRuntime", StringComparison.OrdinalIgnoreCase);
        }
        internal static void Identity(string actual, string expected, long actualStart, long expectedStart, string installedHash, string runtimeHash)
        {
            Manifest.Require(SamePath(actual, expected), "The VLC PID does not belong to the supplied private runtime.");
            Manifest.Require(expectedStart > 0 && actualStart == expectedStart, "The VLC PID start time does not match this launch.");
            Manifest.Require(Layout(expected, installedHash) && String.Equals(installedHash, runtimeHash, StringComparison.Ordinal), "Private VLC must match the installed executable and its SHA256 directory.");
        }
        internal static void Validate(string actual, long actualStart, string runtime, string installed, long expectedStart)
        {
            runtime = Absolute(runtime); installed = Absolute(installed);
            Manifest.Require(Installed(installed) && !SamePath(runtime, installed), "The reference must be standard installed VideoLAN VLC and the runtime must be a private copy.");
            Manifest.Require(SamePath(actual, runtime) && expectedStart > 0 && actualStart == expectedStart, "The private VLC PID path/start time does not match this launch.");
            string hash = Hash(installed);
            Identity(actual, runtime, actualStart, expectedStart, hash, Hash(runtime));
            Manifest.Require(Directory.Exists(Path.Combine(Path.GetDirectoryName(runtime), "portable")), "Private VLC requires its adjacent portable settings directory.");
        }
    }

    internal sealed class Target : IDisposable
    {
        internal readonly Process Process;
        internal readonly int Pid;
        private readonly long startTime;
        internal Target(int pid, string trustedRuntime = null, string installedVlc = null, long expectedStart = 0)
        {
            Process = Process.GetProcessById(pid); Pid = pid;
            try
            {
                string actual = Path.GetFullPath(Process.MainModule.FileName);
                startTime = Process.StartTime.ToUniversalTime().Ticks;
                Manifest.Require(String.Equals(Process.ProcessName, "vlc", StringComparison.OrdinalIgnoreCase), "The supplied PID must be VLC.");
                if (trustedRuntime == null && installedVlc == null && expectedStart == 0)
                    Manifest.Require(RuntimeTrust.Installed(actual), "The supplied PID must be the installed VideoLAN VLC executable.");
                else
                {
                    Manifest.Require(trustedRuntime != null && installedVlc != null && expectedStart > 0, "Private runtime validation requires all three trust options.");
                    RuntimeTrust.Validate(actual, startTime, trustedRuntime, installedVlc, expectedStart);
                }
                Manifest.Require(Alive(), "The VLC process exited during validation.");
            }
            catch { Process.Dispose(); throw; }
        }
        internal bool Alive()
        {
            try { return !Process.HasExited && Process.StartTime.ToUniversalTime().Ticks == startTime; }
            catch (InvalidOperationException) { return false; }
            catch (System.ComponentModel.Win32Exception) { return false; }
        }
        internal bool Owns(IntPtr hwnd)
        {
            if (hwnd == IntPtr.Zero || !Alive() || !Native.IsWindow(hwnd)) return false;
            uint pid; Native.GetWindowThreadProcessId(hwnd, out pid); return pid == (uint)Pid;
        }
        internal List<IntPtr> Windows()
        {
            var result = new List<IntPtr>();
            if (!Alive()) return result;
            Native.EnumWindows(delegate(IntPtr hwnd, IntPtr unused) { uint pid; Native.GetWindowThreadProcessId(hwnd, out pid); if (pid == (uint)Pid) result.Add(hwnd); return true; }, IntPtr.Zero);
            return result;
        }
        internal static IntPtr ChooseVideo(List<IntPtr> children, List<IntPtr> initialSizes)
        {
            if (children.Count == 1) return children[0];
            if (children.Count > 1) return IntPtr.Zero;
            return initialSizes.Count == 1 ? initialSizes[0] : IntPtr.Zero;
        }
        internal string VideoDiscovery = "none";
        internal IntPtr FindVideo(List<IntPtr> windows, Dimensions initial)
        {
            var children = new List<IntPtr>(); var initialSizes = new List<IntPtr>();
            foreach (IntPtr hwnd in windows)
            {
                // Normal skin panes are owned; the native borderless vout root
                // is unowned. Its SkinWindowClass child must not select it.
                if (!Owns(hwnd) || Native.GetWindow(hwnd, 4) == IntPtr.Zero) continue;
                bool childFound = false;
                Native.EnumChildWindows(hwnd, delegate(IntPtr child, IntPtr unused) {
                    if (Owns(child))
                    {
                        var name = new System.Text.StringBuilder(128);
                        Native.GetClassName(child, name, name.Capacity);
                        if (name.ToString() == "SkinWindowClass") childFound = true;
                    }
                    return true;
                }, IntPtr.Zero);
                if (childFound) children.Add(hwnd);
                Native.Rect rect;
                if (Native.GetWindowRect(hwnd, out rect) && rect.Width == initial.width && rect.Height == initial.height) initialSizes.Add(hwnd);
            }
            VideoDiscovery = children.Count == 1 ? "child" : children.Count > 1 ? "ambiguous-child" : initialSizes.Count == 1 ? "fallback" : initialSizes.Count > 1 ? "ambiguous-fallback" : "none";
            return ChooseVideo(children, initialSizes);
        }
        public void Dispose() { Process.Dispose(); }
    }

    internal sealed class Diagnostics : IDisposable
    {
        private readonly TextWriter writer;
        private readonly JavaScriptSerializer serializer = new JavaScriptSerializer();
        private readonly Dictionary<string, string> states = new Dictionary<string, string>();
        internal Diagnostics(TextWriter writer) { this.writer = writer; }
        internal static bool IsAbsolute(string path)
        {
            if (String.IsNullOrEmpty(path) || !Path.IsPathRooted(path)) return false;
            string root = Path.GetPathRoot(path);
            return root.Length > 1 && !(root.Length == 2 && root[1] == ':');
        }
        internal static Diagnostics Open(string path)
        {
            Manifest.Require(IsAbsolute(path), "Diagnostic path must be explicit and absolute.");
            path = Path.GetFullPath(path);
            return new Diagnostics(new StreamWriter(new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read), new System.Text.UTF8Encoding(false)) { AutoFlush = true });
        }
        internal void Change(string category, object state)
        {
            string json = serializer.Serialize(state), previous;
            if (states.TryGetValue(category, out previous) && previous == json) return;
            states[category] = json;
            writer.WriteLine("{\"utc\":" + serializer.Serialize(DateTime.UtcNow.ToString("o", System.Globalization.CultureInfo.InvariantCulture)) + ",\"category\":" + serializer.Serialize(category) + ",\"state\":" + json + "}");
        }
        public void Dispose() { writer.Dispose(); }
    }

    internal static class TooltipDecision
    {
        internal static bool Structural(bool selectedPid, string windowClass, long style, long extendedStyle, bool ownedParent)
        {
            return selectedPid && windowClass == "SkinWindowClass" && ownedParent &&
                (style & 0x88000000L) == 0x88000000L && (extendedStyle & 0x80L) != 0;
        }
        internal static bool Identity(bool selectedPid, string windowClass, string caption, long style, long extendedStyle, bool ownedParent)
        {
            return Structural(selectedPid, windowClass, style, extendedStyle, ownedParent) && caption == "tooltip";
        }
        private static int Clamp(long value, int lower, long upper) { return (int)Math.Min(Math.Max(value, lower), Math.Max(lower, upper)); }
        internal static Point Place(Point cursor, int width, int height, Native.Rect work)
        {
            if (width <= 0 || height <= 0 || work.Right <= work.Left || work.Bottom <= work.Top) throw new ArgumentException("Invalid tooltip or work-area dimensions.");
            long y = (long)cursor.Y - height - 8;
            if (y < work.Top) y = (long)cursor.Y + 8;
            // Oversized native text cannot fit without changing VLC's size;
            // align that dimension to the work-area origin instead of resizing.
            return new Point(Clamp((long)cursor.X - width / 2, work.Left, (long)work.Right - width), Clamp(y, work.Top, (long)work.Bottom - height));
        }
    }

    internal static class HoverDecision
    {
        internal static bool BorderlessCandidate(bool visible, bool hasOwner, string windowClass) { return visible && !hasOwner && windowClass == "SkinWindowClass"; }
        internal static uint PositionFlags(bool alreadyPositioned) { return 0x0001u | 0x0010u | 0x0200u | (alreadyPositioned ? 0x0002u : 0u); }
        internal static bool VolumeRegion(int x, int y) { return x >= 232 && x < 312 && y >= 25 && y < 60; }
        internal static bool Exposed(bool visible, bool minimized, bool pointerOnVideo, bool pointerOnOpenBar)
        {
            return visible && !minimized && (pointerOnVideo || pointerOnOpenBar);
        }
        internal static bool ReadExposure(int selectedPid, IntPtr video, IntPtr hover, bool barVisible, Point cursor, out IntPtr pointerRoot, out bool pointerOnVideo, out bool pointerOnBar)
        {
            IntPtr underPointer = Native.WindowFromPoint(cursor);
            pointerRoot = underPointer == IntPtr.Zero ? IntPtr.Zero : Native.GetAncestor(underPointer, 2);
            uint pid = 0;
            if (pointerRoot != IntPtr.Zero) Native.GetWindowThreadProcessId(pointerRoot, out pid);
            bool selected = pointerRoot != IntPtr.Zero && pid == (uint)selectedPid;
            pointerOnVideo = selected && pointerRoot == video;
            pointerOnBar = barVisible && ((selected && pointerRoot == hover && FirstVisibleRootBelow(hover, cursor) == video) ||
                PopupKeepsBar(selectedPid, video, hover, pointerRoot));
            return Exposed(Native.IsWindowVisible(video), Native.IsIconic(video), pointerOnVideo, pointerOnBar);
        }
        internal static bool PopupKeepsBar(int selectedPid, IntPtr video, IntPtr hover, IntPtr popup)
        {
            uint videoPid, barPid;
            Native.Rect bounds;
            if (popup == IntPtr.Zero || popup == hover || popup == video ||
                Native.GetWindowThreadProcessId(video, out videoPid) == 0 || videoPid != (uint)selectedPid ||
                Native.GetWindowThreadProcessId(hover, out barPid) == 0 || barPid != (uint)selectedPid ||
                Native.GetWindow(hover, 4) != video || !Native.IsWindowVisible(hover) ||
                !Native.GetWindowRect(hover, out bounds)) return false;
            var seen = new HashSet<IntPtr>();
            for (int count = 0; count < 16 && popup != IntPtr.Zero; count++, popup = Native.GetWindow(popup, 4))
            {
                if (popup == hover)
                    return FirstVisibleRootBelow(hover, new Point(bounds.Left + bounds.Width / 2, bounds.Top + bounds.Height / 2)) == video;
                if (!seen.Add(popup) || !Native.IsWindowVisible(popup) || Native.IsIconic(popup) || Native.GetAncestor(popup, 2) != popup) return false;
            }
            return false;
        }
        internal static IntPtr FirstVisibleRootBelow(IntPtr window, Point point)
        {
            var visited = new HashSet<IntPtr>();
            for (int count = 0; count < 256; count++)
            {
                window = Native.GetWindow(window, 2); // GW_HWNDNEXT, downward in z order.
                if (window == IntPtr.Zero || !visited.Add(window)) return IntPtr.Zero;
                Native.Rect bounds;
                if (!Native.IsWindowVisible(window) || Native.IsIconic(window) || Native.GetAncestor(window, 2) != window ||
                    !Native.GetWindowRect(window, out bounds) || !bounds.Contains(point)) continue;
                IntPtr region = Native.CreateRectRgn(0, 0, 0, 0);
                if (region == IntPtr.Zero) return IntPtr.Zero;
                try
                {
                    int kind = Native.GetWindowRgn(window, region);
                    // ERROR also means no custom window region: its rectangle applies.
                    if (kind == 0 || Native.PtInRegion(region, point.X - bounds.Left, point.Y - bounds.Top)) return window;
                }
                finally { Native.DeleteObject(region); }
            }
            return IntPtr.Zero;
        }
        internal static bool IsOpen(int width, int height, HoverSpec spec) { return width == spec.width && height == spec.height; }
        internal static bool Suppress(bool suppressed, bool moved, bool manuallyClosed) { return manuallyClosed || (suppressed && !moved); }
        internal static bool Show(bool videoVisible, bool nativeFullscreen, bool insideVideo, bool insideVisibleBar, long idleMilliseconds, bool suppressed = false)
        {
            return !suppressed && videoVisible && !nativeFullscreen && (insideVisibleBar || (insideVideo && idleMilliseconds < 1800));
        }
    }

    internal sealed class HoverStacking : IDisposable
    {
        private readonly int pid;
        private IntPtr bar, video, originalOwner;
        internal HoverStacking(int selectedPid) { pid = selectedPid; }
        private bool Owns(IntPtr window)
        {
            uint owner;
            return window != IntPtr.Zero && Native.IsWindow(window) && Native.GetWindowThreadProcessId(window, out owner) != 0 && owner == (uint)pid;
        }
        internal bool Bind(IntPtr selectedVideo, IntPtr selectedBar)
        {
            if (bar == selectedBar && video == selectedVideo && Owns(bar) && Owns(video) && Native.GetWindow(bar, 4) == video) return true;
            Dispose();
            if (selectedBar == selectedVideo || !Owns(selectedBar) || !Owns(selectedVideo) ||
                Native.GetAncestor(selectedBar, 2) != selectedBar || Native.GetAncestor(selectedVideo, 2) != selectedVideo) return false;
            uint owner;
            if (Native.GetWindowThreadProcessId(selectedBar, out owner) != Native.GetWindowThreadProcessId(selectedVideo, out owner)) return false;
            var seen = new HashSet<IntPtr>();
            IntPtr ancestor = selectedVideo;
            for (int count = 0; ancestor != IntPtr.Zero; count++, ancestor = Native.GetWindow(ancestor, 4))
                if (count == 128 || ancestor == selectedBar || !seen.Add(ancestor)) return false;
            IntPtr oldOwner = Native.GetWindow(selectedBar, 4);
            if (oldOwner != IntPtr.Zero && !Owns(oldOwner)) return false;
            if (!Native.SetOwner(selectedBar, selectedVideo)) return false;
            bar = selectedBar; video = selectedVideo; originalOwner = oldOwner;
            return true;
        }
        internal bool Place(IntPtr selectedVideo, IntPtr selectedBar, int x, int y)
        {
            if (!Bind(selectedVideo, selectedBar)) return false;
            bool videoTopmost = (Native.ReadStyle(video, -20) & 8) != 0;
            bool barTopmost = (Native.ReadStyle(bar, -20) & 8) != 0;
            if (videoTopmost != barTopmost && !Native.SetWindowPos(bar, new IntPtr(videoTopmost ? -1 : -2), 0, 0, 0, 0, 0x0213)) return false;
            IntPtr previous = Native.GetWindow(video, 3); // GW_HWNDPREV.
            uint flags = HoverDecision.PositionFlags(false);
            if (previous == bar) flags |= 0x0004; // Already immediately above its video.
            else if (previous == IntPtr.Zero || (!videoTopmost && (Native.ReadStyle(previous, -20) & 8) != 0)) previous = IntPtr.Zero;
            // NOACTIVATE + NOOWNERZORDER: placing a bar must never raise its video.
            return Owns(bar) && Owns(video) && Native.SetWindowPos(bar, previous, x, y, 0, 0, flags);
        }
        public void Dispose()
        {
            if (Owns(bar) && Native.GetWindow(bar, 4) == video)
                Native.SetOwner(bar, Owns(originalOwner) ? originalOwner : IntPtr.Zero);
            bar = video = originalOwner = IntPtr.Zero;
        }
    }

    internal static class SignalDecision
    {
        internal static long Due(bool seenReady, string id, long now, long lastButtonTriggered = -10000)
        {
            if (!seenReady && id != "intro") return -1;
            return id == "intro" ? now + 1500 : id == "info" ? Math.Max(now, lastButtonTriggered + 100) : now;
        }
    }

    internal static class SkinSnapping
    {
        internal static string SettingsPath
        {
            get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "NfsSkinEffects", "snapping-enabled.txt"); }
        }
        internal static bool Parse(string value)
        {
            // Invalid or missing settings preserve native snapping by default.
            return value == null || !String.Equals(value.Trim(), "false", StringComparison.Ordinal);
        }
        internal static bool Load(string path)
        {
            try { return Parse(File.ReadAllText(path)); }
            catch (IOException) { return true; }
            catch (UnauthorizedAccessException) { return true; }
        }
        internal static bool Save(string path, bool enabled)
        {
            string temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                File.WriteAllText(temporary, enabled ? "true" : "false");
                if (File.Exists(path)) File.Replace(temporary, path, null);
                else File.Move(temporary, path);
                return true;
            }
            catch (IOException) { return false; }
            catch (UnauthorizedAccessException) { return false; }
            finally
            {
                try { if (File.Exists(temporary)) File.Delete(temporary); }
                catch (IOException) { }
                catch (UnauthorizedAccessException) { }
            }
        }
    }

    internal sealed class SnappingRequest
    {
        private bool ready,handling;
        internal void Reset() { ready=false; handling=false; }
        internal bool Observe(int width,bool supported)
        {
            if(width==191) { ready=true; handling=false; return false; }
            if(width!=192 || handling)return false;
            handling=true;
            return ready && supported;
        }
    }

    internal static class SnappingProtocol
    {
        internal static bool Command(Native.Rect r) { return r.Left==-31000 && r.Top==-29800 && r.Height==17 && (r.Width==191 || r.Width==192); }
        internal static bool State(Native.Rect r) { return r.Left==-31000 && r.Top==-29700 && r.Height==1 && r.Width>=201 && r.Width<=203; }
        internal static int DesiredWidth(bool supported,bool enabled) { return !supported ? 201 : enabled ? 202 : 203; }
        internal static int StateCell(int width) { return width==202 ? 10 : width==203 ? 20 : 30; }
    }

    internal static class SkinSoundVolume
    {
        internal const int Default = 25;
        internal static string SettingsPath
        {
            get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "NfsSkinEffects", "sound-volume.txt"); }
        }
        internal static int Parse(string text)
        {
            int value;
            return text != null && Int32.TryParse(text.Trim(), System.Globalization.NumberStyles.None,
                System.Globalization.CultureInfo.InvariantCulture, out value) && value >= 0 && value <= 100 ? value : Default;
        }
        internal static int Load()
        {
            try { return Parse(File.ReadAllText(SettingsPath)); }
            catch (IOException) { return Default; }
            catch (UnauthorizedAccessException) { return Default; }
        }
        internal static void Save(int value)
        {
            Manifest.Require(value >= 0 && value <= 100, "Skin sound volume must be 0..100.");
            string path = SettingsPath, temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            try
            {
                File.WriteAllText(temporary, value.ToString(System.Globalization.CultureInfo.InvariantCulture));
                if (File.Exists(path)) File.Replace(temporary, path, null);
                else File.Move(temporary, path);
            }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }
        }
        private static bool Tag(byte[] bytes, int offset, string tag)
        {
            return System.Text.Encoding.ASCII.GetString(bytes, offset, 4) == tag;
        }
        internal static byte[] Apply(byte[] source, int percent)
        {
            Manifest.Require(percent >= 0 && percent <= 100, "Skin sound volume must be 0..100.");
            Manifest.Require(source != null && source.Length >= 12 && Tag(source, 0, "RIFF") && Tag(source, 8, "WAVE"), "Invalid skin WAV header.");
            Manifest.Require(BitConverter.ToUInt32(source, 4) == source.Length - 8, "Invalid skin WAV RIFF length.");
            int format = -1, data = -1, length = 0, bits = 0, channels = 0, block = 0;
            int position = 12;
            while (position < source.Length)
            {
                Manifest.Require(source.Length - position >= 8, "Truncated WAV chunk header.");
                uint size = BitConverter.ToUInt32(source, position + 4);
                long end = (long)position + 8 + size, padded = end + (size & 1);
                Manifest.Require(padded <= source.Length, "Truncated WAV chunk data or padding.");
                if (Tag(source, position, "fmt "))
                {
                    Manifest.Require(format < 0 && size >= 16, "Missing or duplicate PCM format.");
                    format = position + 8;
                    channels = BitConverter.ToUInt16(source, format + 2);
                    uint rate = BitConverter.ToUInt32(source, format + 4);
                    block = BitConverter.ToUInt16(source, format + 12);
                    bits = BitConverter.ToUInt16(source, format + 14);
                    Manifest.Require(BitConverter.ToUInt16(source, format) == 1 && channels >= 1 && channels <= 2 &&
                        (bits == 8 || bits == 16) && rate > 0 && block == channels * (bits / 8) &&
                        BitConverter.ToUInt32(source, format + 8) == (long)rate * block, "Unsupported or inconsistent PCM format.");
                }
                else if (Tag(source, position, "data"))
                {
                    Manifest.Require(data < 0, "Duplicate WAV data chunk.");
                    data = position + 8; length = (int)size;
                }
                position = (int)padded;
            }
            Manifest.Require(format >= 0 && data >= 0 && length % block == 0, "Missing or incomplete WAV PCM frames.");
            byte[] result = (byte[])source.Clone();
            if (percent == 100) return result;
            if (bits == 8)
            {
                for (int i = data; i < data + length; i++) result[i] = (byte)(128 + (source[i] - 128) * percent / 100);
            }
            else
            {
                for (int i = data; i < data + length; i += 2)
                {
                    int sample = BitConverter.ToInt16(source, i) * percent / 100;
                    result[i] = (byte)(sample & 255); result[i + 1] = (byte)((sample >> 8) & 255);
                }
            }
            return result;
        }
    }

    internal sealed class SoundState
    {
        internal SoundSpec Spec;
        internal IntPtr Window;
        internal bool Handling;
        internal bool SeenReady;
        internal long Due;
        internal long ResetAfter;
    }

    internal static class ClockRefreshDecision
    {
        internal static bool TooltipHover(bool selectedPid, bool visible, bool minimized, string windowClass, Native.Rect bounds)
        {
            return selectedPid && visible && !minimized && windowClass == "SkinWindowClass" &&
                !(bounds.Left <= -30000 && bounds.Top <= -30000);
        }
        internal static bool PointerOverSkin(int selectedPid, Point cursor)
        {
            IntPtr hit = Native.WindowFromPoint(cursor);
            IntPtr root = hit == IntPtr.Zero ? IntPtr.Zero : Native.GetAncestor(hit, 2);
            uint pid; Native.Rect bounds;
            if (root == IntPtr.Zero || Native.GetWindowThreadProcessId(root, out pid) == 0 ||
                pid != (uint)selectedPid || !Native.GetWindowRect(root, out bounds)) return false;
            var name = new System.Text.StringBuilder(128);
            Native.GetClassName(root, name, name.Capacity);
            return TooltipHover(true, Native.IsWindowVisible(root), Native.IsIconic(root), name.ToString(), bounds);
        }
        internal static bool MatchesCommand(Native.Rect r)
        {
            return r.Left == -31000 && r.Top == -29900 && r.Width == 181 && r.Height == 17;
        }
        internal static int CommandX(int stateWidth)
        {
            return stateWidth == 151 || stateWidth == 152 ? 0 : stateWidth == 153 || stateWidth == 154 ? 10 : -1;
        }
        internal static bool IsFixedCommand(int selectedPid, IntPtr window)
        {
            uint pid; Native.Rect bounds;
            if (window == IntPtr.Zero || Native.GetWindowThreadProcessId(window, out pid) == 0 || pid != (uint)selectedPid ||
                !Native.IsWindowVisible(window) || !Native.GetWindowRect(window, out bounds) || !MatchesCommand(bounds)) return false;
            var name = new System.Text.StringBuilder(128);
            Native.GetClassName(window, name, name.Capacity);
            return name.ToString() == "SkinWindowClass";
        }
        internal static bool Matches(Native.Rect r)
        {
            return r.Left == -31000 && r.Top == -30200 && r.Height == 17 && r.Width >= 151 && r.Width <= 154;
        }
    }

    // Correct only wheel messages already queued for this VLC thread and bar.
    internal sealed class WheelBridge : IDisposable
    {
        private const string Prefix = "NfsSkinWheelBridge.";
        private readonly Target target;
        private IntPtr window, hook, module;
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern IntPtr LoadLibraryEx(string path, IntPtr file, uint flags);
        [DllImport("kernel32.dll", CharSet = CharSet.Ansi, ExactSpelling = true)] private static extern IntPtr GetProcAddress(IntPtr library, string name);
        [DllImport("kernel32.dll")] private static extern bool FreeLibrary(IntPtr library);
        [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern bool SetProp(IntPtr hwnd, string name, IntPtr value);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr GetProp(IntPtr hwnd, string name);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr RemoveProp(IntPtr hwnd, string name);
        [DllImport("user32.dll", SetLastError = true)] private static extern IntPtr SetWindowsHookEx(int type, IntPtr procedure, IntPtr library, uint thread);
        [DllImport("user32.dll")] private static extern bool UnhookWindowsHookEx(IntPtr value);
        internal WheelBridge(Target target) { this.target = target; }
        private static bool MatchingArchitecture(string path)
        {
            try
            {
                using (var reader = new BinaryReader(File.OpenRead(path)))
                {
                    if (reader.BaseStream.Length < 64 || reader.ReadUInt16() != 0x5a4d) return false;
                    reader.BaseStream.Position = 60; int offset = reader.ReadInt32();
                    if (offset < 64 || offset > reader.BaseStream.Length - 6) return false;
                    reader.BaseStream.Position = offset;
                    return reader.ReadUInt32() == 0x4550 && reader.ReadUInt16() == (IntPtr.Size == 8 ? 0x8664 : 0x14c);
                }
            }
            catch (IOException) { return false; }
            catch (UnauthorizedAccessException) { return false; }
        }
        internal bool SnappingSupported
        {
            get { return hook != IntPtr.Zero && target.Owns(window) &&
                GetProp(window, Prefix + "Enabled").ToInt64() == 0x4E465357 &&
                GetProp(window, Prefix + "OwnerPid").ToInt64() == target.Pid &&
                GetProp(window, "NfsOcclusionBridge.SnappingSupported").ToInt64() == 1; }
        }
        internal bool SetSnapping(bool enabled)
        {
            if (!SnappingSupported) return false;
            if (enabled)
            {
                if (GetProp(window, Prefix + "SnappingOff") == IntPtr.Zero) return true;
                RemoveProp(window, Prefix + "SnappingOff");
                return GetProp(window, Prefix + "SnappingOff") == IntPtr.Zero;
            }
            return GetProp(window, Prefix + "SnappingOff").ToInt64() == 1 || SetProp(window, Prefix + "SnappingOff", new IntPtr(1));
        }
        internal void Attach(IntPtr hwnd)
        {
            if (window == hwnd && hook != IntPtr.Zero && target.Owns(hwnd)) return;
            Dispose();
            if (hook != IntPtr.Zero) return;
            if (!target.Owns(hwnd) || GetProp(hwnd, Prefix + "Enabled") != IntPtr.Zero) return;
            uint pid; uint thread = Native.GetWindowThreadProcessId(hwnd, out pid);
            var name = new System.Text.StringBuilder(128); Native.GetClassName(hwnd, name, name.Capacity);
            Native.Rect r;
            if (thread == 0 || pid != (uint)target.Pid || name.ToString() != "SkinWindowClass" || !Native.GetWindowRect(hwnd, out r) ||
                r.Left != -31000 || r.Top != -30800 ||
                !((r.Width == 361 && r.Height == 64) || (r.Width == 362 && r.Height == 1))) return;
            string path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, IntPtr.Size == 8 ? "NfsWheelBridge64.dll" : "NfsWheelBridge32.dll");
            if (!File.Exists(path)) return; // Older helper-only bundles remain usable.
            if (!MatchingArchitecture(path) || !MatchingArchitecture(target.Process.MainModule.FileName)) return;
            try
            {
                module = LoadLibraryEx(path, IntPtr.Zero, 0x900);
                if (module == IntPtr.Zero) return;
                IntPtr procedure = GetProcAddress(module, "CorrectWheel");
                if (procedure == IntPtr.Zero) { Dispose(); return; }
                window = hwnd;
                if (!SetProp(hwnd, Prefix + "OwnerPid", new IntPtr(target.Pid)) ||
                    !SetProp(hwnd, Prefix + "OriginX", new IntPtr(-31000)) || !SetProp(hwnd, Prefix + "OriginY", new IntPtr(-30800))) { Dispose(); return; }
                hook = SetWindowsHookEx(3, procedure, module, thread);
                if (hook == IntPtr.Zero || !SetProp(hwnd, Prefix + "Enabled", new IntPtr(0x4E465357))) Dispose();
            }
            catch (System.ComponentModel.Win32Exception) { Dispose(); }
        }
        public void Dispose()
        {
            if (window != IntPtr.Zero && target.Owns(window))
            {
                RemoveProp(window, Prefix + "SnappingOff");
                RemoveProp(window, Prefix + "Enabled");
                foreach (string name in new[] { "OwnerPid", "OriginX", "OriginY" }) RemoveProp(window, Prefix + name);
            }
            if (hook != IntPtr.Zero && !UnhookWindowsHookEx(hook) && target.Alive()) { window = IntPtr.Zero; return; }
            if (module != IntPtr.Zero) FreeLibrary(module);
            hook = module = window = IntPtr.Zero;
        }
    }

    internal sealed class EffectsContext : ApplicationContext
    {
        private readonly Target target;
        private readonly Assets assets;
        private readonly Dimensions videoFallback;
        private readonly Diagnostics diagnostics;
        private readonly WheelBridge wheelBridge;
        private readonly HoverStacking hoverStacking;
        private readonly Dictionary<string, SoundPlayer> players = new Dictionary<string, SoundPlayer>();
        private readonly List<MemoryStream> soundStreams = new List<MemoryStream>();
        private readonly Dictionary<string, byte[]> originalSounds = new Dictionary<string, byte[]>();
        private int soundVolume;
        private bool snappingEnabled;
        private readonly SnappingRequest snappingRequest=new SnappingRequest();
        private IntPtr snappingCommand, snappingState;
        private long snappingCommandAt=-10000;
        private readonly ToolStripMenuItem snappingMenu;
        private readonly List<SoundState> signals = new List<SoundState>();
        private readonly System.Windows.Forms.Timer timer;
        private readonly NotifyIcon tray;
        private readonly Stopwatch clock = Stopwatch.StartNew();
        private IntPtr video, hover, command, nativeHover, tooltip, clockRefresh, clockRefreshCommand;
        private List<IntPtr> ownedWindows = new List<IntPtr>();
        private Point previousCursor;
        private bool hadCursor, wasInsideVideo, muted, disposed;
        private bool hadBarObservation, previousBarOpen, lastRequestedShow, closeSuppressed;
        private bool volumeRequested, volumeRequestKnown;
        private long movedAt = -10000, commandAt = -10000, discoveryAt = -10000;
        private long lastButtonTriggered = -10000, clockRefreshAt = -10000;
        internal EffectsContext(Target target, Assets assets, Dimensions videoFallback = null, Diagnostics diagnostics = null)
        {
            this.target = target; this.assets = assets;
            wheelBridge = new WheelBridge(target);
            hoverStacking = new HoverStacking(target.Pid);
            this.videoFallback = videoFallback ?? assets.Manifest.video;
            this.diagnostics = diagnostics;
            soundVolume = SkinSoundVolume.Load();
            snappingEnabled = SkinSnapping.Load(SkinSnapping.SettingsPath);
            foreach (var spec in assets.Manifest.sounds)
            {
                originalSounds.Add(spec.id, File.ReadAllBytes(assets.Files[spec.id]));
                signals.Add(new SoundState { Spec = spec, Due = -1 });
            }
            LoadSoundPlayers(soundVolume);
            var menu = new ContextMenuStrip();
            var mute = new ToolStripMenuItem("Mute skin sounds") { CheckOnClick = true };
            mute.CheckedChanged += delegate { muted = mute.Checked; if (muted) foreach (var player in players.Values) player.Stop(); };
            var volumeMenu = new ToolStripMenuItem("Skin sound volume (" + soundVolume + "%)");
            foreach (int preset in new[] { 0, 10, 25, 50, 75, 100 })
            {
                int value = preset;
                var item = new ToolStripMenuItem(value == 0 ? "0% (silent)" : value + "%") { Checked = soundVolume == value, Tag = value };
                item.Click += delegate
                {
                    try
                    {
                        LoadSoundPlayers(value);
                        soundVolume = value;
                        foreach (ToolStripMenuItem option in volumeMenu.DropDownItems) option.Checked = (int)option.Tag == value;
                        volumeMenu.Text = "Skin sound volume (" + value + "%)";
                        SkinSoundVolume.Save(value);
                    }
                    catch (Exception error) { MessageBox.Show(error.Message, "Skin sound volume", MessageBoxButtons.OK, MessageBoxIcon.Warning); }
                };
                volumeMenu.DropDownItems.Add(item);
            }
            menu.Items.Add(volumeMenu);
            menu.Items.Add(mute);
            snappingMenu = new ToolStripMenuItem("Window snapping (unavailable)") { Checked=true, Enabled=false };
            snappingMenu.Click += delegate { ToggleSnapping(); };
            menu.Items.Add(snappingMenu);
            menu.Items.Add("Exit helper", null, delegate { ExitThread(); });
            tray = new NotifyIcon { Icon = SystemIcons.Application, Text = "NFS Underground skin effects", ContextMenuStrip = menu, Visible = true };
            timer = new System.Windows.Forms.Timer { Interval = 30 };
            timer.Tick += Tick; timer.Start();
        }
        private void LoadSoundPlayers(int percent)
        {
            var replacement = new Dictionary<string, SoundPlayer>();
            var streams = new List<MemoryStream>();
            try
            {
                foreach (var pair in originalSounds)
                {
                    var stream = new MemoryStream(SkinSoundVolume.Apply(pair.Value, percent), false);
                    streams.Add(stream);
                    var player = new SoundPlayer(stream); replacement.Add(pair.Key, player); player.Load();
                }
            }
            catch
            {
                foreach (var player in replacement.Values) player.Dispose();
                foreach (var stream in streams) stream.Dispose();
                throw;
            }
            foreach (var player in players.Values) { player.Stop(); player.Dispose(); }
            foreach (var stream in soundStreams) stream.Dispose();
            players.Clear(); soundStreams.Clear();
            foreach (var pair in replacement) players.Add(pair.Key, pair.Value);
            soundStreams.AddRange(streams);
        }
        private bool Rect(IntPtr hwnd, out Native.Rect rect)
        {
            rect = new Native.Rect(); return target.Owns(hwnd) && Native.GetWindowRect(hwnd, out rect);
        }
        private IntPtr Unique(List<IntPtr> windows, int width, int height, bool offscreen)
        {
            var found = new List<IntPtr>();
            foreach (var hwnd in windows)
            {
                Native.Rect rect;
                if (Rect(hwnd, out rect) && rect.Width == width && rect.Height == height && (!offscreen || rect.Left <= -30000)) found.Add(hwnd);
            }
            return found.Count == 1 ? found[0] : IntPtr.Zero;
        }
        private IntPtr UniquePair(List<IntPtr> windows, int width, int height, int alternateWidth, int alternateHeight, bool offscreen)
        {
            var found = new List<IntPtr>();
            foreach (var hwnd in windows)
            {
                Native.Rect rect;
                if (Rect(hwnd, out rect) && ((!offscreen || rect.Left <= -30000)) &&
                    ((rect.Width == width && rect.Height == height) || (rect.Width == alternateWidth && rect.Height == alternateHeight))) found.Add(hwnd);
            }
            return found.Count == 1 ? found[0] : IntPtr.Zero;
        }
        private bool DoubleClick(IntPtr hwnd, int x, int y)
        {
            if (!target.Owns(hwnd)) return false;
            uint pid; uint thread = Native.GetWindowThreadProcessId(hwnd, out pid);
            var info = new Native.GuiThreadInfo { Size = Marshal.SizeOf(typeof(Native.GuiThreadInfo)) };
            // VLC's double-click handler releases capture, including offscreen commands.
            if (thread == 0 || pid != (uint)target.Pid || !Native.GetGUIThreadInfo(thread, ref info) || info.Capture != IntPtr.Zero) return false;
            return Native.PostMessage(hwnd, 0x0203, new IntPtr(1), new IntPtr((y << 16) | (x & 0xffff)));
        }
        private bool IsTooltip(IntPtr hwnd)
        {
            // Inspect no captions until PID, class, styles and owned parent
            // already match VLC's exact native tooltip construction.
            if (!target.Owns(hwnd)) return false;
            var name = new System.Text.StringBuilder(128); Native.GetClassName(hwnd, name, name.Capacity);
            long style = Native.ReadStyle(hwnd, -16), extendedStyle = Native.ReadStyle(hwnd, -20);
            bool ownedParent = target.Owns(Native.GetWindow(hwnd, 4));
            if (!TooltipDecision.Structural(true, name.ToString(), style, extendedStyle, ownedParent)) return false;
            var caption = new System.Text.StringBuilder(9);
            int count = Native.GetWindowText(hwnd, caption, caption.Capacity);
            return count == 7 && TooltipDecision.Identity(true, name.ToString(), caption.ToString(), style, extendedStyle, ownedParent);
        }
        private bool IsSnappingWindow(IntPtr hwnd, bool isCommand)
        {
            Native.Rect bounds;
            if (!Rect(hwnd,out bounds) || !Native.IsWindowVisible(hwnd) || !(isCommand ? SnappingProtocol.Command(bounds) : SnappingProtocol.State(bounds))) return false;
            var name=new System.Text.StringBuilder(128); Native.GetClassName(hwnd,name,name.Capacity);
            return name.ToString()=="SkinWindowClass";
        }
        private void ToggleSnapping()
        {
            bool next=!snappingEnabled;
            if (!wheelBridge.SetSnapping(next)) return;
            snappingEnabled=next;
            if (!SkinSnapping.Save(SkinSnapping.SettingsPath,next))
                tray.ShowBalloonTip(4000,"Window snapping","Changed for this session, but the preference could not be saved.",ToolTipIcon.Warning);
        }
        private void PollSnapping(long now)
        {
            bool supported=wheelBridge.SnappingSupported && wheelBridge.SetSnapping(snappingEnabled);
            snappingMenu.Enabled=supported;
            snappingMenu.Checked=!supported || snappingEnabled;
            snappingMenu.Text=supported ? "Window snapping" : "Window snapping (unavailable)";
            if (!IsSnappingWindow(snappingCommand,true) || !IsSnappingWindow(snappingState,false)) return;
            Native.Rect cmd,state; if(!Rect(snappingCommand,out cmd)||!Rect(snappingState,out state))return;
            if(snappingRequest.Observe(cmd.Width,supported))ToggleSnapping();
            if(cmd.Width==192)
            {
                if(now-snappingCommandAt>=200 && DoubleClick(snappingCommand,0,0))snappingCommandAt=now;
                return;
            }
            int desired=SnappingProtocol.DesiredWidth(supported,snappingEnabled);
            if(state.Width!=desired && now-snappingCommandAt>=200 && DoubleClick(snappingCommand,SnappingProtocol.StateCell(desired),0))snappingCommandAt=now;
        }
        private void Discover(long now)
        {
            if (now - discoveryAt < 200) return;
            discoveryAt = now;
            var windows = target.Windows();
            ownedWindows = windows;
            var snapCommands=windows.Where(hwnd=>IsSnappingWindow(hwnd,true)).ToList();
            IntPtr foundSnap=snapCommands.Count==1 ? snapCommands[0] : IntPtr.Zero;
            if(foundSnap!=snappingCommand) snappingRequest.Reset();
            snappingCommand=foundSnap;
            var snapStates=windows.Where(hwnd=>IsSnappingWindow(hwnd,false)).ToList();
            snappingState=snapStates.Count==1 ? snapStates[0] : IntPtr.Zero;
            var clocks = windows.Where(hwnd => { Native.Rect r; return Rect(hwnd, out r) && ClockRefreshDecision.Matches(r) && Native.IsWindowVisible(hwnd); }).ToList();
            clockRefresh = clocks.Count == 1 ? clocks[0] : IntPtr.Zero;
            if (clockRefresh != IntPtr.Zero)
            {
                var name = new System.Text.StringBuilder(128);
                Native.GetClassName(clockRefresh, name, name.Capacity);
                if (name.ToString() != "SkinWindowClass") clockRefresh = IntPtr.Zero;
            }
            var fixedClocks = windows.Where(hwnd => ClockRefreshDecision.IsFixedCommand(target.Pid, hwnd)).ToList();
            clockRefreshCommand = fixedClocks.Count == 1 ? fixedClocks[0] : IntPtr.Zero;
            var tooltips = windows.Where(IsTooltip).ToList();
            tooltip = tooltips.Count == 1 ? tooltips[0] : IntPtr.Zero;
            foreach (var signal in signals) if (!target.Owns(signal.Window)) signal.Window = UniquePair(windows, signal.Spec.width, signal.Spec.height, signal.Spec.readyWidth, signal.Spec.height, true);
            if (!target.Owns(command)) command = Unique(windows, assets.Manifest.command.width, assets.Manifest.command.height, true);
            IntPtr foundVideo = target.FindVideo(windows, videoFallback);
            if (diagnostics != null) diagnostics.Change("discovery", new { source = target.VideoDiscovery, found = foundVideo != IntPtr.Zero });
            if (foundVideo != IntPtr.Zero) video = foundVideo;
            else if (!target.Owns(video)) video = IntPtr.Zero;
            if (!target.Owns(hover)) hover = UniquePair(windows, assets.Manifest.hover.width, assets.Manifest.hover.height, assets.Manifest.hover.closedWidth, assets.Manifest.hover.closedHeight, false);
            if (assets.Manifest.schemaVersion == 2) wheelBridge.Attach(hover);
            if (assets.Manifest.schemaVersion == 2 && !target.Owns(nativeHover)) nativeHover = Unique(windows, 360, 64, false);
        }
        private void PollSounds(long now)
        {
            // Observe the button before info even if a valid manifest reorders
            // entries: the original information view loads 100 ms after click.
            foreach (var signal in signals.OrderBy(s => s.Spec.id == "button" ? 0 : 1))
            {
                Native.Rect bounds;
                if (!Rect(signal.Window, out bounds) || bounds.Left > -30000 || (bounds.Width != signal.Spec.width && bounds.Width != signal.Spec.readyWidth) || bounds.Height != signal.Spec.height) { signal.Window = IntPtr.Zero; signal.Handling = false; signal.Due = -1; continue; }
                if (!Native.IsWindowVisible(signal.Window)) continue;
                if (bounds.Width == signal.Spec.readyWidth) {
                    signal.SeenReady = true; signal.Handling = false; signal.Due = -1;
                    // Advertise only after assets were loaded and the native
                    // ready signal was observed. The host can now replay the
                    // visual animation and trigger its sound in one action.
                    if (signal.Spec.id == "intro" && bounds.Left == -31000 && bounds.Top == -31000 &&
                        bounds.Width == 43 && bounds.Height == 17 && target.Owns(signal.Window))
                    {
                        var name = new System.Text.StringBuilder(128);
                        Native.GetClassName(signal.Window,name,name.Capacity);
                        if (name.ToString()=="SkinWindowClass" && Native.GetProp(signal.Window,"NfsSkinEffects.IntroReady")==IntPtr.Zero)
                            Native.SetProp(signal.Window,"NfsSkinEffects.IntroReady",new IntPtr(1));
                    }
                    continue;
                }
                if (!signal.Handling)
                {
                    signal.Handling = true;
                    // A stale trigger restored on attachment is cleared. Fresh
                    // signals arm from their persistent, observable ready layout.
                    if (signal.SeenReady && signal.Spec.id == "button") lastButtonTriggered = now;
                    signal.Due = SignalDecision.Due(signal.SeenReady, signal.Spec.id, now, lastButtonTriggered);
                    signal.ResetAfter = now;
                    if (diagnostics != null) diagnostics.Change("sound-" + signal.Spec.id, new { id = signal.Spec.id, played = false, muted = muted, phase = "trigger", observedAtMs=now, dueAtMs=signal.Due });
                }
                if (signal.Spec.id == "info" && signal.Due >= 0) signal.Due = Math.Max(signal.Due, lastButtonTriggered + 100);
                if (signal.Due >= 0 && now >= signal.Due)
                {
                    bool played = false;
                    if (!muted && soundVolume > 0) try { players[signal.Spec.id].Play(); played = true; } catch (Exception error) { Trace.WriteLine(error.Message); }
                    if (diagnostics != null) diagnostics.Change("sound-" + signal.Spec.id, new { id = signal.Spec.id, played = played, muted = muted, phase = "dispatch", dispatchedAtMs=now });
                    signal.Due = -1; signal.ResetAfter = now;
                }
                if (signal.Due < 0 && now >= signal.ResetAfter) { DoubleClick(signal.Window, 1, 1); signal.ResetAfter = now + 200; }
            }
        }
        private bool Borderless()
        {
            string blockerClass = ""; int blockerWidth = 0, blockerHeight = 0; bool blockerOwned = false;
            // Native fullscreen may keep the old framed window visible behind
            // it; its own controller can temporarily be the foreground HWND.
            foreach (IntPtr hwnd in ownedWindows)
            {
                if (hwnd == video || hwnd == hover || !target.Owns(hwnd)) continue;
                var name = new System.Text.StringBuilder(128); Native.GetClassName(hwnd, name, name.Capacity);
                bool hasOwner = Native.GetWindow(hwnd, 4) != IntPtr.Zero;
                if (!HoverDecision.BorderlessCandidate(Native.IsWindowVisible(hwnd), hasOwner, name.ToString())) continue;
                Native.Rect rect; if (!Rect(hwnd, out rect)) continue;
                var info = new Native.MonitorInfo { Size = Marshal.SizeOf(typeof(Native.MonitorInfo)) };
                if (Native.GetMonitorInfo(Native.MonitorFromWindow(hwnd, 2), ref info) && rect.Left <= info.Monitor.Left && rect.Top <= info.Monitor.Top && rect.Right >= info.Monitor.Right && rect.Bottom >= info.Monitor.Bottom)
                {
                    blockerClass = name.ToString(); blockerWidth = rect.Width; blockerHeight = rect.Height; blockerOwned = hasOwner;
                    if (diagnostics != null) diagnostics.Change("fullscreen-blocker", new { detected = true, windowClass = blockerClass, width = blockerWidth, height = blockerHeight, owned = blockerOwned });
                    return true;
                }
            }
            if (diagnostics != null) diagnostics.Change("fullscreen-blocker", new { detected = false, windowClass = blockerClass, width = blockerWidth, height = blockerHeight, owned = blockerOwned });
            return false;
        }
        private bool SendCommand(int x, long now)
        {
            Native.Rect bounds;
            if (now - commandAt < 200 || !Rect(command, out bounds) || bounds.Left > -30000 || bounds.Width != assets.Manifest.command.width || bounds.Height != assets.Manifest.command.height || !Native.IsWindowVisible(command)) return false;
            if (!DoubleClick(command, x, assets.Manifest.command.y)) return false;
            commandAt = now; return true;
        }
        private void HoverCommand(bool show, long now)
        {
            if (SendCommand(show ? assets.Manifest.command.showX : assets.Manifest.command.hideX, now)) lastRequestedShow = show;
        }
        private void VolumeCommand(bool expand, long now)
        {
            if (assets.Manifest.schemaVersion != 2 || (volumeRequestKnown && volumeRequested == expand)) return;
            if (SendCommand(expand ? assets.Manifest.command.volumeShowX : assets.Manifest.command.volumeHideX, now)) { volumeRequestKnown = true; volumeRequested = expand; }
        }
        private void PollHover(long now)
        {
            Native.Rect bounds, bar;
            bool videoVisible = Rect(video, out bounds) && Native.IsWindowVisible(video) && !Native.IsIconic(video);
            if (diagnostics != null) diagnostics.Change("video", new { found = target.Owns(video), width = bounds.Width, height = bounds.Height, visible = videoVisible });
            bool barKnown = Rect(hover, out bar) && Native.IsWindowVisible(hover);
            bool barVisible = barKnown && HoverDecision.IsOpen(bar.Width, bar.Height, assets.Manifest.hover);
            bool stackingReady = hoverStacking.Bind(video, hover);
            if (barVisible && videoVisible && stackingReady)
            {
                int x = bounds.Left + (bounds.Width - assets.Manifest.hover.width) / 2;
                int y = bounds.Bottom - 30 * assets.Manifest.scale - assets.Manifest.hover.height - 6 * assets.Manifest.scale;
                stackingReady = hoverStacking.Place(video, hover, x, y);
                Rect(hover, out bar);
                if (assets.Manifest.schemaVersion == 2 && target.Owns(hover)) Native.SetBarOpacity(hover);
            }
            Point cursor;
            if (!Native.GetCursorPos(out cursor)) return;
            // Rectangles survive hiding/occlusion. Only the exposed selected video
            // or its already-open bar may maintain hover, including vout children.
            IntPtr pointerRoot; bool pointerOnVideo, pointerOnBar;
            bool exposed = HoverDecision.ReadExposure(target.Pid, video, hover, barVisible, cursor, out pointerRoot, out pointerOnVideo, out pointerOnBar) && videoVisible && stackingReady;
            bool inside = exposed && pointerOnVideo && bounds.Contains(cursor);
            bool moved = !hadCursor || cursor != previousCursor || (inside && !wasInsideVideo);
            if (moved) movedAt = now;
            // A source close button switches the bar to its closed layout without
            // a helper hide request. Honor it until a later cursor motion/reentry.
            bool manuallyClosed = barKnown && hadBarObservation && previousBarOpen && !barVisible && lastRequestedShow;
            closeSuppressed = HoverDecision.Suppress(closeSuppressed, moved, manuallyClosed);
            if (barKnown)
            {
                if (!hadBarObservation && barVisible) lastRequestedShow = true;
                previousBarOpen = barVisible; hadBarObservation = true;
            }
            previousCursor = cursor; hadCursor = true; wasInsideVideo = inside;
            IntPtr foreground = Native.GetForegroundWindow();
            bool foregroundOwn = target.Owns(foreground), fullscreenDetected = videoVisible && Borderless();
            bool desired = HoverDecision.Show(exposed, fullscreenDetected, inside, pointerOnBar, now - movedAt, closeSuppressed);
            if (diagnostics != null) diagnostics.Change("hover", new { open = barVisible, desired = desired, inside = inside, foregroundOwn = foregroundOwn, fullscreenDetected = fullscreenDetected, suppressed = closeSuppressed });
            if (desired != barVisible) HoverCommand(desired, now);
            if (assets.Manifest.schemaVersion == 2)
            {
                Native.Rect nativeBar;
                bool framedVolume = desired && barVisible && pointerRoot == hover && HoverDecision.VolumeRegion(cursor.X - bar.Left, cursor.Y - bar.Top);
                bool nativeVolume = pointerRoot == nativeHover && target.Owns(nativeHover) && Rect(nativeHover, out nativeBar) && Native.IsWindowVisible(nativeHover) && nativeBar.Width == 360 && nativeBar.Height == 64 && HoverDecision.VolumeRegion(cursor.X - nativeBar.Left, cursor.Y - nativeBar.Top);
                VolumeCommand(framedVolume || nativeVolume, now);
            }
        }
        private void PollClock(long now)
        {
            Native.Rect bounds;
            if (now - clockRefreshAt < 500 || !Rect(clockRefresh, out bounds) || !ClockRefreshDecision.Matches(bounds) || !Native.IsWindowVisible(clockRefresh)) return;
            if (ClockRefreshDecision.IsFixedCommand(target.Pid, clockRefreshCommand))
            {
                // Persistent command Images retain native last-hit identity while
                // their synchronous macro refreshes only the separate state layouts.
                int x = ClockRefreshDecision.CommandX(bounds.Width);
                if (x >= 0 && DoubleClick(clockRefreshCommand, x, 0)) clockRefreshAt = now;
                return;
            }
            // Legacy clock commands enter a different Image after each layout switch.
            // VLC findHitControl hides the global tooltip before its 500ms timer
            // can display. Leave native tooltip lifetime intact during skin hover.
            Point cursor;
            if (!Native.GetCursorPos(out cursor) || ClockRefreshDecision.PointerOverSkin(target.Pid, cursor) ||
                (IsTooltip(tooltip) && Native.IsWindowVisible(tooltip))) return;
            // Paused-seek forced refresh resumes when the pointer leaves the skin.
            // Visibility refresh reads VLC's completed seek without seeking or resuming it.
            if (DoubleClick(clockRefresh, 0, 0)) clockRefreshAt = now;
        }
        private void Tick(object sender, EventArgs arguments)
        {
            if (!target.Alive()) { ExitThread(); return; }
            try { long now = clock.ElapsedMilliseconds; Discover(now); PollSounds(now); PollHover(now); PollSnapping(now); PollTooltip(); PollClock(now); }
            catch (Exception error) { Trace.WriteLine(error.Message); ExitThread(); }
        }
        private void PollTooltip()
        {
            Native.Rect bounds;
            if (!IsTooltip(tooltip) || !Native.IsWindowVisible(tooltip) || !Rect(tooltip, out bounds) || bounds.Width <= 0 || bounds.Height <= 0) return;
            Point cursor; if (!Native.GetCursorPos(out cursor)) return;
            IntPtr underPointer = Native.WindowFromPoint(cursor);
            if (underPointer == IntPtr.Zero || !target.Owns(Native.GetAncestor(underPointer, 2))) return;
            var monitor = new Native.MonitorInfo { Size = Marshal.SizeOf(typeof(Native.MonitorInfo)) };
            if (!Native.GetMonitorInfo(Native.MonitorFromPoint(cursor, 2), ref monitor) || monitor.Work.Right <= monitor.Work.Left || monitor.Work.Bottom <= monitor.Work.Top) return;
            Point position = TooltipDecision.Place(cursor, bounds.Width, bounds.Height, monitor.Work);
            if (target.Owns(tooltip)) Native.SetWindowPos(tooltip, new IntPtr(-1), position.X, position.Y, bounds.Width, bounds.Height, HoverDecision.PositionFlags(bounds.Left == position.X && bounds.Top == position.Y));
        }
        protected override void ExitThreadCore()
        {
            if (!disposed)
            {
                disposed = true; timer.Stop();
                if(IsSnappingWindow(snappingCommand,true))DoubleClick(snappingCommand,30,0);
                wheelBridge.Dispose(); hoverStacking.Dispose();
                if (target.Alive())
                {
                    VolumeCommand(false, clock.ElapsedMilliseconds + 200);
                    HoverCommand(false, clock.ElapsedMilliseconds + 400);
                    foreach (var signal in signals)
                    {
                        if (signal.Spec.id == "intro" && target.Owns(signal.Window))
                            Native.RemoveProp(signal.Window,"NfsSkinEffects.IntroReady");
                        Native.Rect rect;
                        if (Rect(signal.Window, out rect) && rect.Left <= -30000 && rect.Width == signal.Spec.width && rect.Height == signal.Spec.height && Native.IsWindowVisible(signal.Window)) DoubleClick(signal.Window, 1, 1);
                    }
                }
                foreach (var player in players.Values) { player.Stop(); player.Dispose(); }
                foreach (var stream in soundStreams) stream.Dispose();
                timer.Dispose(); tray.Visible = false; tray.ContextMenuStrip.Dispose(); tray.Dispose();
            }
            base.ExitThreadCore();
        }
    }

    internal static class Program
    {
        internal static Dimensions ParseVideoSize(string value, int scale)
        {
            string[] parts = (value ?? "").Split('x');
            int width = 0, height = 0;
            Manifest.Require((scale == 1 || scale == 2) && parts.Length == 2 &&
                Int32.TryParse(parts[0], System.Globalization.NumberStyles.None, System.Globalization.CultureInfo.InvariantCulture, out width) &&
                Int32.TryParse(parts[1], System.Globalization.NumberStyles.None, System.Globalization.CultureInfo.InvariantCulture, out height),
                "Video size must be decimal WIDTHxHEIGHT.");
            Manifest.Require(width >= 708 * scale && height >= 440 * scale && width <= 8192 && height <= 4320,
                "Video size is outside the skin's supported layout bounds.");
            return new Dimensions { width = width, height = height };
        }
        private static Manifest Example()
        {
            return new Manifest { schemaVersion = 1, scale = 1, sounds = Manifest.Allowed.Select((pair, index) => new SoundSpec { id = pair.Key, file = pair.Value, width = 51 + index, readyWidth = 41 + index, height = 17 }).ToArray(), command = new CommandSpec { width = 67, height = 17, showX = 2, hideX = 35, y = 2 }, hover = new HoverSpec { width = 426, height = 146, closedWidth = 427, closedHeight = 1 }, video = new Dimensions { width = 708, height = 440 } };
        }
        private static void Check(bool value) { if (!value) throw new Exception("Self-test assertion failed."); }
        private static void Invalid(Action action) { try { action(); } catch (InvalidDataException) { return; } throw new Exception("Unsafe manifest accepted."); }
        private static byte[] SoundFixture(int bits, byte[] samples)
        {
            using (var stream = new MemoryStream())
            using (var writer = new BinaryWriter(stream))
            {
                writer.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); writer.Write(0);
                writer.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt ")); writer.Write(16);
                writer.Write((short)1); writer.Write((short)1); writer.Write(44100); writer.Write(44100 * (bits / 8));
                writer.Write((short)(bits / 8)); writer.Write((short)bits);
                writer.Write(System.Text.Encoding.ASCII.GetBytes("JUNK")); writer.Write(3);
                writer.Write(new byte[] { 23, 42, 91, 0 }); // Odd-sized unknown chunk and its pad.
                writer.Write(System.Text.Encoding.ASCII.GetBytes("data")); writer.Write(samples.Length); writer.Write(samples);
                if (samples.Length % 2 != 0) writer.Write((byte)0);
                writer.Flush(); byte[] bytes = stream.ToArray();
                Array.Copy(BitConverter.GetBytes(bytes.Length - 8), 0, bytes, 4, 4); return bytes;
            }
        }
        private static void SoundVolumeTests()
        {
            Check(SkinSoundVolume.Parse(null) == 25 && SkinSoundVolume.Parse("") == 25);
            foreach (string invalid in new[] { "-1", "101", "25.0", "+50", "NaN", "2147483648", "1\n2" })
                Check(SkinSoundVolume.Parse(invalid) == 25);
            Check(SkinSoundVolume.Parse("0") == 0 && SkinSoundVolume.Parse("100\r\n") == 100 && SkinSoundVolume.Parse("10") == 10);
            byte[] original = SoundFixture(8, new byte[] { 0, 1, 127, 128, 129, 254, 255 });
            byte[] unchanged = (byte[])original.Clone();
            byte[] scaled = SkinSoundVolume.Apply(original, 25);
            Check(original.SequenceEqual(unchanged) && !Object.ReferenceEquals(original, scaled));
            Check(scaled.Take(56).SequenceEqual(original.Take(56)) && scaled.Last() == original.Last());
            Check(scaled.Skip(56).Take(7).SequenceEqual(new byte[] { 96, 97, 128, 128, 128, 159, 159 }));
            Check(SkinSoundVolume.Apply(original, 100).SequenceEqual(original));
            Check(SkinSoundVolume.Apply(original, 0).Skip(56).Take(7).All(value => value == 128));
            var signed = new MemoryStream();
            using (var writer = new BinaryWriter(signed))
                foreach (short sample in new short[] { -32768, -3, -1, 0, 1, 3, 32767 }) writer.Write(sample);
            original = SoundFixture(16, signed.ToArray()); unchanged = (byte[])original.Clone();
            scaled = SkinSoundVolume.Apply(original, 50);
            short[] expected = { -16384, -1, 0, 0, 0, 1, 16383 };
            for (int index = 0; index < expected.Length; index++) Check(BitConverter.ToInt16(scaled, 56 + index * 2) == expected[index]);
            Check(original.SequenceEqual(unchanged) && scaled.Take(56).SequenceEqual(original.Take(56)));
            Check(SkinSoundVolume.Apply(original, 0).Skip(56).All(value => value == 0));
            Check(SkinSoundVolume.Apply(original, 100).SequenceEqual(original));
            Invalid(delegate { SkinSoundVolume.Apply(original, -1); });
            Invalid(delegate { SkinSoundVolume.Apply(original, 101); });
            Invalid(delegate { SkinSoundVolume.Apply(null, 25); });
            Invalid(delegate { SkinSoundVolume.Apply(original.Take(original.Length - 1).ToArray(), 25); });
            byte[] broken = (byte[])original.Clone(); broken[16] = 255; // Oversized fmt chunk.
            Invalid(delegate { SkinSoundVolume.Apply(broken, 25); });
            broken = (byte[])original.Clone(); broken[20] = 3; // Float instead of PCM.
            Invalid(delegate { SkinSoundVolume.Apply(broken, 25); });
            broken = (byte[])original.Clone(); broken[32] = 1; // Bad block alignment.
            Invalid(delegate { SkinSoundVolume.Apply(broken, 25); });
            broken = SoundFixture(16, new byte[] { 1, 2, 3 }); // Partial sample/frame.
            Invalid(delegate { SkinSoundVolume.Apply(broken, 25); });
            broken = (byte[])original.Clone(); broken[36] = (byte)'d'; broken[37] = (byte)'a'; broken[38] = (byte)'t'; broken[39] = (byte)'a';
            Invalid(delegate { SkinSoundVolume.Apply(broken, 25); }); // Duplicate data, not an unknown chunk.
        }
        private static int SelfTest()
        {
            SoundVolumeTests();
            var snappingRequest=new SnappingRequest();
            Check(!snappingRequest.Observe(192,true)); // stale saved trigger
            Check(!snappingRequest.Observe(191,true));
            Check(snappingRequest.Observe(192,true));
            Check(!snappingRequest.Observe(192,true)); // delayed ACK cannot repeat
            Check(!snappingRequest.Observe(191,true));
            Check(snappingRequest.Observe(192,true)); // subsequent explicit click
            snappingRequest.Reset();
            Check(!snappingRequest.Observe(191,false) && !snappingRequest.Observe(192,false));
            Check(!snappingRequest.Observe(192,true)); // capability change is not a click
            Check(!snappingRequest.Observe(191,true) && snappingRequest.Observe(192,true));
            Check(SnappingProtocol.DesiredWidth(false,false)==201 && SnappingProtocol.DesiredWidth(true,true)==202 && SnappingProtocol.DesiredWidth(true,false)==203);
            Check(SnappingProtocol.StateCell(201)==30 && SnappingProtocol.StateCell(202)==10 && SnappingProtocol.StateCell(203)==20);
            Check(SnappingProtocol.Command(new Native.Rect {Left=-31000,Top=-29800,Right=-30809,Bottom=-29783}));
            Check(!SnappingProtocol.Command(new Native.Rect {Left=-31000,Top=-29801,Right=-30809,Bottom=-29784}));
            Check(SnappingProtocol.State(new Native.Rect {Left=-31000,Top=-29700,Right=-30797,Bottom=-29699}));
            Check(!SnappingProtocol.State(new Native.Rect {Left=-31000,Top=-29700,Right=-30796,Bottom=-29699}));
            Check(SkinSnapping.Parse(null) && SkinSnapping.Parse("") && SkinSnapping.Parse("true"));
            Check(!SkinSnapping.Parse("false") && !SkinSnapping.Parse(" false\r\n"));
            Check(SkinSnapping.Parse("False") && SkinSnapping.Parse("0") && SkinSnapping.Parse("corrupt"));
            Check(TooltipDecision.Identity(true, "SkinWindowClass", "tooltip", 0x88000000L, 0x80L, true));
            Check(!TooltipDecision.Identity(false, "SkinWindowClass", "tooltip", 0x88000000L, 0x80L, true));
            Check(!TooltipDecision.Identity(true, "OtherClass", "tooltip", 0x88000000L, 0x80L, true));
            Check(!TooltipDecision.Identity(true, "SkinWindowClass", "tooltip-other", 0x88000000L, 0x80L, true));
            Check(!TooltipDecision.Identity(true, "SkinWindowClass", "Tooltip", 0x88000000L, 0x80L, true));
            Check(!TooltipDecision.Identity(true, "SkinWindowClass", "tooltip", 0x80000000L, 0x80L, true));
            Check(!TooltipDecision.Identity(true, "SkinWindowClass", "tooltip", 0x08000000L, 0x80L, true));
            Check(!TooltipDecision.Identity(true, "SkinWindowClass", "tooltip", 0x88000000L, 0, true));
            Check(!TooltipDecision.Identity(true, "SkinWindowClass", "tooltip", 0x88000000L, 0x80L, false));
            Check(ClockRefreshDecision.CommandX(151)==0 && ClockRefreshDecision.CommandX(152)==0);
            Check(ClockRefreshDecision.CommandX(153)==10 && ClockRefreshDecision.CommandX(154)==10);
            Check(ClockRefreshDecision.CommandX(150)==-1 && ClockRefreshDecision.CommandX(155)==-1);
            Check(ClockRefreshDecision.MatchesCommand(new Native.Rect { Left=-31000,Top=-29900,Right=-30819,Bottom=-29883 }));
            Check(!ClockRefreshDecision.MatchesCommand(new Native.Rect { Left=-31000,Top=-29901,Right=-30819,Bottom=-29884 }));
            var skinBounds = new Native.Rect { Left=20, Top=20, Right=320, Bottom=318 };
            Check(ClockRefreshDecision.TooltipHover(true,true,false,"SkinWindowClass",skinBounds));
            Check(!ClockRefreshDecision.TooltipHover(false,true,false,"SkinWindowClass",skinBounds));
            Check(!ClockRefreshDecision.TooltipHover(true,false,false,"SkinWindowClass",skinBounds));
            Check(!ClockRefreshDecision.TooltipHover(true,true,true,"SkinWindowClass",skinBounds));
            Check(!ClockRefreshDecision.TooltipHover(true,true,false,"OtherClass",skinBounds));
            Check(!ClockRefreshDecision.TooltipHover(true,true,false,"SkinWindowClass",new Native.Rect { Left=-31000,Top=-30200,Right=-30849,Bottom=-30183 }));
            var tooltipWork = new Native.Rect { Left = 0, Top = 0, Right = 1920, Bottom = 1040 };
            Check(TooltipDecision.Place(new Point(600, 400), 200, 30, tooltipWork) == new Point(500, 362));
            Check(TooltipDecision.Place(new Point(1919, 400), 200, 30, tooltipWork) == new Point(1720, 362));
            Check(TooltipDecision.Place(new Point(0, 400), 200, 30, tooltipWork) == new Point(0, 362));
            Check(TooltipDecision.Place(new Point(600, 10), 200, 30, tooltipWork) == new Point(500, 18));
            Check(TooltipDecision.Place(new Point(600, 38), 200, 30, tooltipWork) == new Point(500, 0));
            Check(TooltipDecision.Place(new Point(600, 1039), 200, 30, tooltipWork) == new Point(500, 1001));
            tooltipWork = new Native.Rect { Left = -1920, Top = -1080, Right = 0, Bottom = 0 };
            Check(TooltipDecision.Place(new Point(-1800, -500), 200, 30, tooltipWork) == new Point(-1900, -538));
            Check(TooltipDecision.Place(new Point(-1919, -1079), 200, 30, tooltipWork) == new Point(-1920, -1071));
            tooltipWork = new Native.Rect { Left = -40, Top = -20, Right = 0, Bottom = 0 };
            Check(TooltipDecision.Place(new Point(-10, -10), 100, 30, tooltipWork) == new Point(-40, -20));
            Check(HoverDecision.VolumeRegion(232, 25));
            Check(HoverDecision.VolumeRegion(311, 59));
            Check(!HoverDecision.VolumeRegion(231, 25));
            Check(!HoverDecision.VolumeRegion(312, 25));
            Check(!HoverDecision.VolumeRegion(232, 24));
            Check(!HoverDecision.VolumeRegion(232, 60));
            foreach (int assetScale in new[] { 1, 2 })
            {
                var compact = Example(); compact.schemaVersion = 2; compact.scale = assetScale;
                compact.video.width = 708 * assetScale; compact.video.height = 440 * assetScale;
                compact.hover = new HoverSpec { width = 361, height = 64, closedWidth = 362, closedHeight = 1 };
                compact.command.width = 133; compact.command.volumeShowX = 68; compact.command.volumeHideX = 101;
                compact.Validate();
                Check(HoverDecision.IsOpen(361, 64, compact.hover));
                compact.hover.width = 722; Invalid(compact.Validate); compact.hover.width = 361;
                compact.command.volumeShowX = 67; Invalid(compact.Validate); compact.command.volumeShowX = 68;
                compact.command.width = 67; Invalid(compact.Validate); compact.command.width = 133;
                compact.hover.closedHeight = 2; Invalid(compact.Validate);
            }
            var legacyVolume = Example(); legacyVolume.command.volumeShowX = 68; Invalid(legacyVolume.Validate);
            string hash = new string('a', 64), otherHash = new string('b', 64);
            string runtime = Path.GetFullPath(@"C:\private\VlcRuntime\" + hash + @"\vlc.exe");
            RuntimeTrust.Identity(runtime, runtime.ToUpperInvariant(), 10, 10, hash, hash);
            Invalid(delegate { RuntimeTrust.Identity(runtime, runtime, 10, 11, hash, hash); });
            Invalid(delegate { RuntimeTrust.Identity(runtime, runtime, 0, 0, hash, hash); });
            Invalid(delegate { RuntimeTrust.Identity(runtime, runtime, 10, 10, hash, otherHash); });
            Invalid(delegate { RuntimeTrust.Identity(runtime, @"C:\other\vlc.exe", 10, 10, hash, hash); });
            Check(!RuntimeTrust.Layout(@"C:\private\" + hash + @"\vlc.exe", hash));
            Check(!RuntimeTrust.Layout(runtime.Replace("vlc.exe", "other.exe"), hash));
            Check(!RuntimeTrust.Layout(runtime, otherHash));
            Check(!RuntimeTrust.Layout(runtime, new string('z', 64)));
            Invalid(delegate { RuntimeTrust.Absolute("vlc.exe"); });
            Invalid(delegate { RuntimeTrust.Absolute(@"\private\vlc.exe"); });
            Invalid(delegate { RuntimeTrust.Absolute("C:vlc.exe"); });
            Check(Diagnostics.IsAbsolute("C:/owned/log.jsonl"));
            Check(Diagnostics.IsAbsolute(@"C:\owned\log.jsonl"));
            Check(!Diagnostics.IsAbsolute("log.jsonl"));
            Check(!Diagnostics.IsAbsolute(@"\owned\log.jsonl"));
            Check(!Diagnostics.IsAbsolute("C:log.jsonl"));
            Check(HoverDecision.BorderlessCandidate(true, false, "SkinWindowClass"));
            Check(!HoverDecision.BorderlessCandidate(true, true, "SkinWindowClass"));
            Check(!HoverDecision.BorderlessCandidate(true, false, "#32770"));
            Check(!HoverDecision.BorderlessCandidate(false, false, "SkinWindowClass"));
            Check(HoverDecision.PositionFlags(false) == (0x0001u | 0x0010u | 0x0200u));
            Check(HoverDecision.PositionFlags(true) == (0x0001u | 0x0010u | 0x0200u | 0x0002u));
            var diagnosticText = new StringWriter();
            using (var log = new Diagnostics(diagnosticText)) { log.Change("hover", new { open = false }); log.Change("hover", new { open = false }); log.Change("hover", new { open = true }); }
            Check(diagnosticText.ToString().Split(new[] { Environment.NewLine }, StringSplitOptions.RemoveEmptyEntries).Length == 2);
            var size = ParseVideoSize("708x440", 1); Check(size.width == 708 && size.height == 440);
            size = ParseVideoSize("1920x1080", 2); Check(size.width == 1920 && size.height == 1080);
            size = ParseVideoSize("8192x4320", 2); Check(size.width == 8192 && size.height == 4320);
            foreach (var invalid in new[] { "707x440", "708x439", "8193x440", "708x4321", "-708x440", "+708x440", "708X440", "708x440x1", "708 x440", "2147483648x440", "", null })
                Invalid(delegate { ParseVideoSize(invalid, 1); });
            Invalid(delegate { ParseVideoSize("1415x880", 2); });
            Invalid(delegate { ParseVideoSize("1416x879", 2); });
            Invalid(delegate { ParseVideoSize("708x440", 3); });
            Example().Validate(); var m = Example(); m.scale = 3; Invalid(m.Validate);
            m = Example(); m.sounds[0].file = "../button.wav"; Invalid(m.Validate);
            m = Example(); m.sounds[1].width = m.sounds[0].width; Invalid(m.Validate);
            m = Example(); m.sounds[0].readyWidth = 51; Invalid(m.Validate);
            m = Example(); m.sounds[1].id = m.sounds[0].id; Invalid(m.Validate);
            m = Example(); m.hover.width = 425; Invalid(m.Validate);
            m = Example(); m.hover.closedHeight = 146; Invalid(m.Validate);
            m = Example(); m.scale = 2; m.hover.width = 852; m.hover.height = 292; m.hover.closedWidth = 854; m.hover.closedHeight = 2; m.video.width = 1416; m.video.height = 880; m.Validate();
            Check(HoverDecision.Show(true, false, true, false, 0));
            Check(!HoverDecision.Show(true, false, true, false, 1800));
            Check(HoverDecision.Show(true, false, false, true, 10000));
            Check(!HoverDecision.Show(false, false, true, true, 0));
            Check(!HoverDecision.Show(true, true, true, true, 0));
            Check(!HoverDecision.Show(true, false, false, false, 0));
            bool suppressed = HoverDecision.Suppress(false, true, true);
            Check(suppressed); // Closing wins even if the click's motion was sampled now.
            Check(!HoverDecision.Show(true, false, true, false, 0, suppressed));
            suppressed = HoverDecision.Suppress(suppressed, false, false);
            Check(suppressed); // A stationary cursor must not reopen a manually closed bar.
            suppressed = HoverDecision.Suppress(suppressed, true, false);
            Check(!suppressed && HoverDecision.Show(true, false, true, false, 0, suppressed));
            Check(!HoverDecision.Suppress(false, false, false)); // Helper hide is not a manual close.
            Check(HoverDecision.Exposed(true, false, true, false));
            Check(HoverDecision.Exposed(true, false, false, true));
            Check(!HoverDecision.Exposed(true, false, false, false)); // Covered/stale rectangle.
            Check(!HoverDecision.Exposed(false, false, true, true)); // Hidden pane.
            Check(!HoverDecision.Exposed(true, true, true, true)); // Minimized pane.
            Check(!HoverDecision.Show(HoverDecision.Exposed(true, false, false, false), false, true, true, 0));
            Check(!HoverDecision.Show(HoverDecision.Exposed(false, false, false, true), false, false, true, 0));
            Check(HoverDecision.IsOpen(426, 146, Example().hover));
            Check(!HoverDecision.IsOpen(427, 1, Example().hover));
            Check(SignalDecision.Due(false, "button", 100) == -1);
            Check(SignalDecision.Due(true, "button", 100) == 100);
            Check(SignalDecision.Due(false, "intro", 100) == 1600);
            Check(SignalDecision.Due(true, "intro", 9000) == 10500);
            Check(SignalDecision.Due(true, "button", 1000) == 1000);
            Check(SignalDecision.Due(true, "info", 1000, 1000) == 1100);
            Check(SignalDecision.Due(true, "info", 1040, 1000) == 1100);
            Check(SignalDecision.Due(true, "info", 1100, 1000) == 1100);
            Check(SignalDecision.Due(true, "info", 1200, 1000) == 1200);
            Check(SignalDecision.Due(true, "info", 1000) == 1000);
            Check(SignalDecision.Due(false, "info", 1000, 1000) == -1);
            // Child-bearing owned video wins over stale initial-size matches;
            // multiple embedded outputs remain ambiguous and must be rejected.
            Check(Target.ChooseVideo(new List<IntPtr> {new IntPtr(9)}, new List<IntPtr> {new IntPtr(7)}) == new IntPtr(9));
            Check(Target.ChooseVideo(new List<IntPtr> {new IntPtr(8),new IntPtr(9)}, new List<IntPtr> {new IntPtr(7)}) == IntPtr.Zero);
            Check(Target.ChooseVideo(new List<IntPtr>(), new List<IntPtr> {new IntPtr(7)}) == new IntPtr(7));
            Check(Target.ChooseVideo(new List<IntPtr>(), new List<IntPtr> {new IntPtr(7),new IntPtr(8)}) == IntPtr.Zero);
            Check(Target.ChooseVideo(new List<IntPtr>(), new List<IntPtr>()) == IntPtr.Zero);
            for (int width = 150; width <= 155; width++)
                Check(ClockRefreshDecision.Matches(new Native.Rect { Left=-31000, Top=-30200, Right=-31000+width, Bottom=-30183 }) == (width >= 151 && width <= 154));
            Check(!ClockRefreshDecision.Matches(new Native.Rect { Left=0, Top=-30200, Right=151, Bottom=-30183 }));
            Check(!ClockRefreshDecision.Matches(new Native.Rect { Left=-31000, Top=-30201, Right=-30849, Bottom=-30184 }));
            Check(Marshal.SizeOf(typeof(Native.GuiThreadInfo)) == (IntPtr.Size == 8 ? 72 : 48));
            return 0;
        }
        [STAThread] private static int Main(string[] arguments)
        {
            bool selfTest = arguments.Length > 0 && arguments[0] == "--self-test";
            bool checkSkin = arguments.Length > 0 && arguments[0] == "--check-skin";
            try
            {
                if (selfTest) { if (arguments.Length != 1) throw new ArgumentException("Use --self-test."); return SelfTest(); }
                if (checkSkin) { if (arguments.Length != 2) throw new ArgumentException("Use --check-skin path.vlt."); using (var validated = Assets.Open(Path.GetFullPath(arguments[1]))) { } return 0; }
                int pid = 0; string skin = null, videoSize = null, diagnosticPath = null, trustedRuntime = null, installedVlc = null;
                long expectedStart = 0; bool hasExpectedStart = false;
                for (int i = 0; i < arguments.Length; i += 2)
                {
                    if (i + 1 >= arguments.Length) throw new ArgumentException("Use --pid N --skin path.vlt [--video-size WIDTHxHEIGHT].");
                    if (arguments[i] == "--pid" && pid == 0) pid = Int32.Parse(arguments[i + 1]);
                    else if (arguments[i] == "--skin" && skin == null) skin = Path.GetFullPath(arguments[i + 1]);
                    else if (arguments[i] == "--video-size" && videoSize == null) videoSize = arguments[i + 1];
                    else if (arguments[i] == "--diagnostic-log" && diagnosticPath == null) diagnosticPath = arguments[i + 1];
                    else if (arguments[i] == "--trusted-vlc-runtime" && trustedRuntime == null) trustedRuntime = RuntimeTrust.Absolute(arguments[i + 1]);
                    else if (arguments[i] == "--installed-vlc" && installedVlc == null) installedVlc = RuntimeTrust.Absolute(arguments[i + 1]);
                    else if (arguments[i] == "--pid-start-ticks" && !hasExpectedStart) { expectedStart = Int64.Parse(arguments[i + 1], System.Globalization.NumberStyles.None, System.Globalization.CultureInfo.InvariantCulture); hasExpectedStart = true; }
                    else throw new ArgumentException("Use --pid N --skin path.vlt [--video-size WIDTHxHEIGHT].");
                }
                if (pid <= 0 || skin == null) throw new ArgumentException("Use --pid N --skin path.vlt [--video-size WIDTHxHEIGHT].");
                Manifest.Require((trustedRuntime == null && installedVlc == null && !hasExpectedStart) ||
                    (trustedRuntime != null && installedVlc != null && hasExpectedStart && expectedStart > 0), "Supply --trusted-vlc-runtime, --installed-vlc and --pid-start-ticks together.");
                using (var target = new Target(pid, trustedRuntime, installedVlc, expectedStart))
                {
                    bool created;
                    using (var instance = new Mutex(true, "Local\\NfsSkinEffects-" + pid + "-" + target.Process.StartTime.ToUniversalTime().Ticks, out created))
                    {
                        if (!created) return 0;
                        using (var assets = Assets.Open(skin))
                        {
                            Dimensions fallback = videoSize == null ? null : ParseVideoSize(videoSize, assets.Manifest.scale);
                            Native.SetProcessDPIAware(); Application.EnableVisualStyles();
                            using (var log = diagnosticPath == null ? null : Diagnostics.Open(diagnosticPath))
                            using (var context = new EffectsContext(target, assets, fallback, log)) Application.Run(context);
                        }
                    }
                }
                return 0;
            }
            catch (Exception error)
            {
                if (selfTest || checkSkin) Console.Error.WriteLine(error.Message);
                if (!selfTest && !checkSkin) MessageBox.Show(error.Message, "NFS skin effects", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
        }
    }
}
