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
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

namespace NfsSkinSupport
{
    public sealed class Dimensions { public int width; public int height; }
    public sealed class HoverSpec { public int width; public int height; public int closedWidth; public int closedHeight; }
    public sealed class CommandSpec { public int width; public int height; public int showX; public int hideX; public int y; }
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
            Require(schemaVersion == 1 && (scale == 1 || scale == 2), "Unsupported effects manifest version or scale.");
            Require(sounds != null && sounds.Length == 5, "Exactly five original sound signals are required.");
            var ids = new HashSet<string>(); var widths = new HashSet<int>();
            foreach (var sound in sounds)
            {
                string file;
                Require(sound != null && sound.id != null && Allowed.TryGetValue(sound.id, out file), "Unknown sound signal.");
                Require(sound.file == Allowed[sound.id] && ids.Add(sound.id), "Sound files must use the original whitelist once each.");
                Require(sound.height == 17 && sound.width >= 51 && sound.width <= 55 && sound.readyWidth == sound.width - 10 && widths.Add(sound.width), "Sound ready/trigger geometry must be unique.");
            }
            Require(command != null && command.width == 67 && command.height == 17 && command.showX == 2 && command.hideX == 35 && command.y == 2, "Invalid hover command geometry.");
            Require(hover != null && hover.width == 426 * scale && hover.height == 146 * scale, "Invalid framed hover geometry.");
            Require(hover.closedWidth == 427 * scale && hover.closedHeight == scale, "Invalid transparent closed hover geometry.");
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
        internal delegate bool EnumCallback(IntPtr hwnd, IntPtr argument);
        [DllImport("user32.dll")] internal static extern bool EnumWindows(EnumCallback callback, IntPtr argument);
        [DllImport("user32.dll")] internal static extern bool EnumChildWindows(IntPtr parent, EnumCallback callback, IntPtr argument);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] internal static extern int GetClassName(IntPtr hwnd, System.Text.StringBuilder name, int count);
        [DllImport("user32.dll")] internal static extern IntPtr GetWindow(IntPtr hwnd, uint command);
        [DllImport("user32.dll")] internal static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
        [DllImport("user32.dll")] internal static extern bool GetWindowRect(IntPtr hwnd, out Rect rect);
        [DllImport("user32.dll")] internal static extern bool IsWindowVisible(IntPtr hwnd);
        [DllImport("user32.dll")] internal static extern bool IsWindow(IntPtr hwnd);
        [DllImport("user32.dll")] internal static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] internal static extern bool GetCursorPos(out Point point);
        [DllImport("user32.dll")] internal static extern IntPtr GetAncestor(IntPtr hwnd, uint flags);
        [DllImport("user32.dll")] internal static extern IntPtr MonitorFromWindow(IntPtr hwnd, uint flags);
        [DllImport("user32.dll", CharSet = CharSet.Auto)] internal static extern bool GetMonitorInfo(IntPtr monitor, ref MonitorInfo info);
        [DllImport("user32.dll")] internal static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int width, int height, uint flags);
        [DllImport("user32.dll")] internal static extern bool PostMessage(IntPtr hwnd, uint message, IntPtr wParam, IntPtr lParam);
        [DllImport("user32.dll")] internal static extern bool SetProcessDPIAware();
    }

    internal sealed class Target : IDisposable
    {
        internal readonly Process Process;
        internal readonly int Pid;
        private readonly long startTime;
        internal Target(int pid)
        {
            Process = Process.GetProcessById(pid); Pid = pid;
            string actual = Path.GetFullPath(Process.MainModule.FileName);
            var roots = new[] { Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), Environment.GetEnvironmentVariable("ProgramW6432") };
            bool known = roots.Where(p => !String.IsNullOrEmpty(p)).Any(p => String.Equals(actual, Path.GetFullPath(Path.Combine(p, "VideoLAN", "VLC", "vlc.exe")), StringComparison.OrdinalIgnoreCase));
            Manifest.Require(known && String.Equals(Process.ProcessName, "vlc", StringComparison.OrdinalIgnoreCase), "The supplied PID must be the installed VideoLAN VLC executable.");
            startTime = Process.StartTime.ToUniversalTime().Ticks;
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

    internal static class HoverDecision
    {
        internal static bool BorderlessCandidate(bool visible, bool hasOwner, string windowClass) { return visible && !hasOwner && windowClass == "SkinWindowClass"; }
        internal static uint PositionFlags(bool alreadyPositioned) { return 0x0001u | 0x0010u | 0x0200u | (alreadyPositioned ? 0x0002u : 0u); }
        internal static bool IsOpen(int width, int height, HoverSpec spec) { return width == spec.width && height == spec.height; }
        internal static bool Suppress(bool suppressed, bool moved, bool manuallyClosed) { return manuallyClosed || (suppressed && !moved); }
        internal static bool Show(bool videoVisible, bool foregroundVlc, bool nativeFullscreen, bool insideVideo, bool insideVisibleBar, long idleMilliseconds, bool suppressed = false)
        {
            return !suppressed && videoVisible && foregroundVlc && !nativeFullscreen && (insideVisibleBar || (insideVideo && idleMilliseconds < 1800));
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

    internal sealed class SoundState
    {
        internal SoundSpec Spec;
        internal IntPtr Window;
        internal bool Handling;
        internal bool SeenReady;
        internal long Due;
        internal long ResetAfter;
    }

    internal sealed class EffectsContext : ApplicationContext
    {
        private readonly Target target;
        private readonly Assets assets;
        private readonly Dimensions videoFallback;
        private readonly Diagnostics diagnostics;
        private readonly Dictionary<string, SoundPlayer> players = new Dictionary<string, SoundPlayer>();
        private readonly List<MemoryStream> soundStreams = new List<MemoryStream>();
        private readonly List<SoundState> signals = new List<SoundState>();
        private readonly System.Windows.Forms.Timer timer;
        private readonly NotifyIcon tray;
        private readonly Stopwatch clock = Stopwatch.StartNew();
        private IntPtr video, hover, command;
        private List<IntPtr> ownedWindows = new List<IntPtr>();
        private Point previousCursor;
        private bool hadCursor, wasInsideVideo, muted, disposed;
        private bool hadBarObservation, previousBarOpen, lastRequestedShow, closeSuppressed;
        private long movedAt = -10000, commandAt = -10000, discoveryAt = -10000;
        private long lastButtonTriggered = -10000;
        internal EffectsContext(Target target, Assets assets, Dimensions videoFallback = null, Diagnostics diagnostics = null)
        {
            this.target = target; this.assets = assets;
            this.videoFallback = videoFallback ?? assets.Manifest.video;
            this.diagnostics = diagnostics;
            foreach (var spec in assets.Manifest.sounds)
            {
                // Keep original WAV bytes in memory and retain each input stream
                // until its player is disposed; runtime Play needs no file load.
                var stream = new MemoryStream(File.ReadAllBytes(assets.Files[spec.id]), false);
                soundStreams.Add(stream);
                var player = new SoundPlayer(stream);
                player.Load();
                players.Add(spec.id, player);
                signals.Add(new SoundState { Spec = spec, Due = -1 });
            }
            var menu = new ContextMenuStrip();
            var mute = new ToolStripMenuItem("Mute skin sounds") { CheckOnClick = true };
            mute.CheckedChanged += delegate { muted = mute.Checked; if (muted) foreach (var player in players.Values) player.Stop(); };
            menu.Items.Add(mute);
            menu.Items.Add("Exit helper", null, delegate { ExitThread(); });
            tray = new NotifyIcon { Icon = SystemIcons.Application, Text = "NFS Underground skin effects", ContextMenuStrip = menu, Visible = true };
            timer = new System.Windows.Forms.Timer { Interval = 30 };
            timer.Tick += Tick; timer.Start();
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
            return target.Owns(hwnd) && Native.PostMessage(hwnd, 0x0203, new IntPtr(1), new IntPtr((y << 16) | (x & 0xffff)));
        }
        private void Discover(long now)
        {
            if (now - discoveryAt < 200) return;
            discoveryAt = now;
            var windows = target.Windows();
            ownedWindows = windows;
            foreach (var signal in signals) if (!target.Owns(signal.Window)) signal.Window = UniquePair(windows, signal.Spec.width, signal.Spec.height, signal.Spec.readyWidth, signal.Spec.height, true);
            if (!target.Owns(command)) command = Unique(windows, assets.Manifest.command.width, assets.Manifest.command.height, true);
            IntPtr foundVideo = target.FindVideo(windows, videoFallback);
            if (diagnostics != null) diagnostics.Change("discovery", new { source = target.VideoDiscovery, found = foundVideo != IntPtr.Zero });
            if (foundVideo != IntPtr.Zero) video = foundVideo;
            else if (!target.Owns(video)) video = IntPtr.Zero;
            if (!target.Owns(hover)) hover = UniquePair(windows, assets.Manifest.hover.width, assets.Manifest.hover.height, assets.Manifest.hover.closedWidth, assets.Manifest.hover.closedHeight, false);
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
                if (bounds.Width == signal.Spec.readyWidth) { signal.SeenReady = true; signal.Handling = false; signal.Due = -1; continue; }
                if (!signal.Handling)
                {
                    signal.Handling = true;
                    // A stale trigger restored on attachment is cleared. Fresh
                    // signals arm from their persistent, observable ready layout.
                    if (signal.SeenReady && signal.Spec.id == "button") lastButtonTriggered = now;
                    signal.Due = SignalDecision.Due(signal.SeenReady, signal.Spec.id, now, lastButtonTriggered);
                    signal.ResetAfter = now;
                    if (diagnostics != null) diagnostics.Change("sound-" + signal.Spec.id, new { id = signal.Spec.id, played = false, muted = muted, phase = "trigger" });
                }
                if (signal.Spec.id == "info" && signal.Due >= 0) signal.Due = Math.Max(signal.Due, lastButtonTriggered + 100);
                if (signal.Due >= 0 && now >= signal.Due)
                {
                    bool played = false;
                    if (!muted) try { players[signal.Spec.id].Play(); played = true; } catch (Exception error) { Trace.WriteLine(error.Message); }
                    if (diagnostics != null) diagnostics.Change("sound-" + signal.Spec.id, new { id = signal.Spec.id, played = played, muted = muted, phase = "dispatch" });
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
        private void HoverCommand(bool show, long now)
        {
            Native.Rect bounds;
            if (now - commandAt < 200 || !Rect(command, out bounds) || bounds.Left > -30000 || bounds.Width != 67 || bounds.Height != 17 || !Native.IsWindowVisible(command)) return;
            if (DoubleClick(command, show ? assets.Manifest.command.showX : assets.Manifest.command.hideX, assets.Manifest.command.y)) { commandAt = now; lastRequestedShow = show; }
        }
        private void PollHover(long now)
        {
            Native.Rect bounds, bar;
            bool videoVisible = Rect(video, out bounds) && Native.IsWindowVisible(video);
            if (diagnostics != null) diagnostics.Change("video", new { found = target.Owns(video), width = bounds.Width, height = bounds.Height, visible = videoVisible });
            bool barKnown = Rect(hover, out bar) && Native.IsWindowVisible(hover);
            bool barVisible = barKnown && HoverDecision.IsOpen(bar.Width, bar.Height, assets.Manifest.hover);
            Point cursor;
            if (!Native.GetCursorPos(out cursor)) return;
            bool inside = videoVisible && bounds.Contains(cursor);
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
            bool desired = HoverDecision.Show(videoVisible, foregroundOwn, fullscreenDetected, inside, barVisible && bar.Contains(cursor), now - movedAt, closeSuppressed);
            if (diagnostics != null) diagnostics.Change("hover", new { open = barVisible, desired = desired, inside = inside, foregroundOwn = foregroundOwn, fullscreenDetected = fullscreenDetected, suppressed = closeSuppressed });
            if (desired && barVisible)
            {
                int width = assets.Manifest.hover.width, height = assets.Manifest.hover.height;
                int x = bounds.Left + (bounds.Width - width) / 2;
                int y = bounds.Bottom - 30 * assets.Manifest.scale - height - 6 * assets.Manifest.scale;
                // Playback can reorder native skin/vout windows without moving
                // this bar. Reassert stacking even when its position is current.
                Native.SetWindowPos(hover, new IntPtr(-1), x, y, width, height, HoverDecision.PositionFlags(bar.Left == x && bar.Top == y));
            }
            if (desired != barVisible) HoverCommand(desired, now);
        }
        private void Tick(object sender, EventArgs arguments)
        {
            if (!target.Alive()) { ExitThread(); return; }
            try { long now = clock.ElapsedMilliseconds; Discover(now); PollSounds(now); PollHover(now); }
            catch (Exception error) { Trace.WriteLine(error.Message); ExitThread(); }
        }
        protected override void ExitThreadCore()
        {
            if (!disposed)
            {
                disposed = true; timer.Stop();
                if (target.Alive())
                {
                    HoverCommand(false, clock.ElapsedMilliseconds + 200);
                    foreach (var signal in signals)
                    {
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
        private static int SelfTest()
        {
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
            Check(HoverDecision.Show(true, true, false, true, false, 0));
            Check(!HoverDecision.Show(true, true, false, true, false, 1800));
            Check(HoverDecision.Show(true, true, false, false, true, 10000));
            Check(!HoverDecision.Show(false, true, false, true, true, 0));
            Check(!HoverDecision.Show(true, false, false, true, true, 0));
            Check(!HoverDecision.Show(true, true, true, true, true, 0));
            Check(!HoverDecision.Show(true, true, false, false, false, 0));
            bool suppressed = HoverDecision.Suppress(false, true, true);
            Check(suppressed); // Closing wins even if the click's motion was sampled now.
            Check(!HoverDecision.Show(true, true, false, true, false, 0, suppressed));
            suppressed = HoverDecision.Suppress(suppressed, false, false);
            Check(suppressed); // A stationary cursor must not reopen a manually closed bar.
            suppressed = HoverDecision.Suppress(suppressed, true, false);
            Check(!suppressed && HoverDecision.Show(true, true, false, true, false, 0, suppressed));
            Check(!HoverDecision.Suppress(false, false, false)); // Helper hide is not a manual close.
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
                int pid = 0; string skin = null, videoSize = null, diagnosticPath = null;
                for (int i = 0; i < arguments.Length; i += 2)
                {
                    if (i + 1 >= arguments.Length) throw new ArgumentException("Use --pid N --skin path.vlt [--video-size WIDTHxHEIGHT].");
                    if (arguments[i] == "--pid" && pid == 0) pid = Int32.Parse(arguments[i + 1]);
                    else if (arguments[i] == "--skin" && skin == null) skin = Path.GetFullPath(arguments[i + 1]);
                    else if (arguments[i] == "--video-size" && videoSize == null) videoSize = arguments[i + 1];
                    else if (arguments[i] == "--diagnostic-log" && diagnosticPath == null) diagnosticPath = arguments[i + 1];
                    else throw new ArgumentException("Use --pid N --skin path.vlt [--video-size WIDTHxHEIGHT].");
                }
                if (pid <= 0 || skin == null) throw new ArgumentException("Use --pid N --skin path.vlt [--video-size WIDTHxHEIGHT].");
                using (var target = new Target(pid))
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
