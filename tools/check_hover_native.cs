// Native product-gate fixture. Run only through check_hover_native.py.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Linq;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Forms;

namespace NfsSkinSupport
{
    public sealed class HoverVlcRequest
    {
        public int scale;
        public string executable, installed, arguments, log, skin;
        public Dictionary<string, string> environment;
    }
    internal sealed class HoverFixtureWindow : NativeWindow, IDisposable
    {
        private readonly bool child;
        internal HoverFixtureWindow(int x, int y, int width, int height, IntPtr parent)
        {
            child = parent != IntPtr.Zero;
            CreateHandle(new CreateParams { Caption = "NFS private exposure fixture",
                X = x, Y = y, Width = width, Height = height, Parent = parent,
                Style = parent == IntPtr.Zero ? unchecked((int)0x80000000) : 0x40000000,
                ExStyle = parent == IntPtr.Zero ? 0x08000080 : 0 });
        }
        internal void Place(int x, int y, int width, int height)
        {
            if (!Native.SetWindowPos(Handle, child ? IntPtr.Zero : new IntPtr(-1), x, y, width, height, 0x0010 | 0x0040))
                throw new InvalidOperationException("Fixture positioning failed.");
            HoverFixtureApi.ShowWindow(Handle, 4);
            Application.DoEvents();
        }
        internal void Hide() { HoverFixtureApi.ShowWindow(Handle, 0); Application.DoEvents(); }
        protected override void WndProc(ref Message message)
        {
            if (message.Msg == 0x0084) { message.Result = new IntPtr(1); return; }
            base.WndProc(ref message);
        }
        public void Dispose() { if (Handle != IntPtr.Zero) DestroyHandle(); }
    }

    internal static class HoverFixtureApi
    {
        [DllImport("user32.dll")] internal static extern bool ShowWindow(IntPtr window, int command);
        [DllImport("user32.dll", SetLastError = true)] internal static extern bool GetLayeredWindowAttributes(IntPtr window, out uint colorKey, out byte alpha, out uint flags);
        [DllImport("user32.dll")] internal static extern IntPtr GetThreadDesktop(uint thread);
        [DllImport("kernel32.dll")] internal static extern uint GetCurrentThreadId();
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] internal static extern bool GetUserObjectInformation(IntPtr handle, int index, StringBuilder text, int length, out int needed);
        internal static bool PrivateDesktop()
        {
            var text = new StringBuilder(256); int needed;
            return GetUserObjectInformation(GetThreadDesktop(GetCurrentThreadId()), 2, text, 512, out needed)
                && text.ToString().StartsWith("NfsLoad_", StringComparison.Ordinal);
        }
        internal static bool SameDesktop(uint thread)
        {
            var own = new StringBuilder(256); var other = new StringBuilder(256); int needed;
            return GetUserObjectInformation(GetThreadDesktop(GetCurrentThreadId()), 2, own, 512, out needed)
                && GetUserObjectInformation(GetThreadDesktop(thread), 2, other, 512, out needed)
                && own.ToString().StartsWith("NfsLoad_", StringComparison.Ordinal) && own.ToString() == other.ToString();
        }
    }

    internal static class HoverNativeFixture
    {
        private static readonly List<object> cases = new List<object>();
        private static readonly List<object> actualResults = new List<object>();
        private static readonly List<object> opacityReadbacks = new List<object>();
        private static readonly List<object> coverageReadbacks = new List<object>();
        private static Point point;
        private static void Check(int scale, string name, bool condition)
        {
            cases.Add(new { scale = scale, name = name, passed = condition });
            if (!condition) throw new InvalidOperationException("Native exposure assertion failed: " + name);
        }
        private static bool Read(IntPtr video, IntPtr bar, bool barOpen, int pid, out bool onVideo, out bool onBar, out IntPtr root)
        {
            return HoverDecision.ReadExposure(pid, video, bar, barOpen, point, out root, out onVideo, out onBar);
        }
        private static void CheckOpacity(int scale, string prefix, IntPtr bar)
        {
            // Exercise the product implementation, not a copied alpha constant
            // or a fixture-only SetLayeredWindowAttributes call.
            for (int pass = 0; pass < 2; pass++)
            {
                Native.SetBarOpacity(bar);
                uint colorKey, flags; byte alpha;
                bool read = HoverFixtureApi.GetLayeredWindowAttributes(bar, out colorKey, out alpha, out flags);
                bool layered = (Native.ReadStyle(bar, -20) & 0x80000) != 0;
                opacityReadbacks.Add(new { scale = scale, bar = prefix, reassert = pass != 0,
                    readSucceeded = read, alpha = alpha, flags = flags, layered = layered });
                Check(scale, prefix + (pass == 0 ? "-opaque-alpha255" : "-opaque-alpha255-reassert"),
                    read && flags == 2 && alpha == 255 && layered);
            }
        }
        private static void Scale(int scale)
        {
            int x = point.X - 150, y = point.Y - 120, width = 708 * scale, height = 440 * scale;
            int pid = Process.GetCurrentProcess().Id;
            using (var video = new HoverFixtureWindow(x, y, width, height, IntPtr.Zero))
            using (var child = new HoverFixtureWindow(140, 110, 40, 40, video.Handle))
            using (var bar = new HoverFixtureWindow(point.X-20, point.Y-20, 361, 64, IntPtr.Zero))
            using (var blocker = new HoverFixtureWindow(point.X-30, point.Y-30, 100, 100, IntPtr.Zero))
            {
                bool onVideo, onBar; IntPtr root;
                video.Place(x, y, width, height);
                bool exposed = Read(video.Handle, bar.Handle, false, pid, out onVideo, out onBar, out root);
                Check(scale, "exposed-video-root", exposed && onVideo && !onBar && root == video.Handle);
                Check(scale, "exposed-video-show", HoverDecision.Show(exposed, false, onVideo, onBar, 0));
                child.Place(140, 110, 40, 40);
                Native.Rect childBounds;
                Check(scale, "child-is-visible", Native.IsWindowVisible(child.Handle));
                Check(scale, "child-contains-test-point", Native.GetWindowRect(child.Handle, out childBounds) && childBounds.Contains(point));
                Check(scale, "child-parent-is-video", Native.GetAncestor(child.Handle, 2) == video.Handle);
                exposed = Read(video.Handle, bar.Handle, false, pid, out onVideo, out onBar, out root);
                Check(scale, "vout-child-hit", Native.WindowFromPoint(point) == child.Handle);
                Check(scale, "vout-child-root", exposed && onVideo && root == video.Handle);
                exposed = Read(video.Handle, bar.Handle, false, pid == 1 ? 2 : 1, out onVideo, out onBar, out root);
                Check(scale, "foreign-pid-rejected", !exposed && !onVideo && !onBar);
                child.Hide();
                bar.Place(point.X-20, point.Y-20, 361, 64);
                CheckOpacity(scale, "synthetic-framed-bar", bar.Handle);
                exposed = Read(video.Handle, bar.Handle, true, pid, out onVideo, out onBar, out root);
                Check(scale, "open-bar-root", exposed && !onVideo && onBar && root == bar.Handle);
                Check(scale, "stationary-open-bar-retained", HoverDecision.Show(exposed, false, false, onBar, 10000));
                exposed = Read(video.Handle, bar.Handle, false, pid, out onVideo, out onBar, out root);
                Check(scale, "closed-bar-not-retained", !exposed && !onBar);
                bar.Hide();
                blocker.Place(point.X-30, point.Y-30, 100, 100);
                exposed = Read(video.Handle, bar.Handle, false, pid, out onVideo, out onBar, out root);
                Check(scale, "occluded-video-root", !exposed && !onVideo && !onBar && root == blocker.Handle);
                Check(scale, "covered-stale-rect-no-show", !HoverDecision.Show(exposed, false, true, true, 0));
                blocker.Hide();
                video.Hide();
                exposed = Read(video.Handle, bar.Handle, false, pid, out onVideo, out onBar, out root);
                Check(scale, "hidden-video-no-show", !exposed && !HoverDecision.Show(exposed, false, true, true, 0));
                video.Place(x, y, width, height);
                HoverFixtureApi.ShowWindow(video.Handle, 7); Application.DoEvents();
                Check(scale, "native-minimized-state", Native.IsIconic(video.Handle));
                exposed = Read(video.Handle, bar.Handle, false, pid, out onVideo, out onBar, out root);
                Check(scale, "minimized-video-no-show", !exposed && !HoverDecision.Show(exposed, false, true, true, 0));
                HoverFixtureApi.ShowWindow(video.Handle, 4); Application.DoEvents();
                video.Place(x+width+100, y, width, height);
                exposed = Read(video.Handle, bar.Handle, false, pid, out onVideo, out onBar, out root);
                Check(scale, "moved-video-old-rect-rejected", !exposed && !HoverDecision.Show(exposed, false, true, true, 0));
                video.Place(x, y, width, height);
                exposed = Read(video.Handle, bar.Handle, false, pid, out onVideo, out onBar, out root);
                Check(scale, "exposed-video-idle-expiry", exposed && !HoverDecision.Show(exposed, false, onVideo, false, 1800));
            }
        }
        private static string Log(string path)
        {
            if (!File.Exists(path)) return "";
            using (var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
            using (var reader = new StreamReader(stream)) return reader.ReadToEnd();
        }
        private static void Pause() { Application.DoEvents(); System.Threading.Thread.Sleep(60); }
        private static void Move(Target target, IntPtr window, int x, int y)
        {
            if (!target.Owns(window) || !Native.SetWindowPos(window, new IntPtr(-1), x, y, 0, 0, 0x0010 | 0x0001 | 0x0040))
                throw new InvalidOperationException("Owned test window positioning failed.");
            Pause();
        }
        private static void Show(Target target, IntPtr window, int command)
        {
            if (!target.Owns(window)) throw new InvalidOperationException("Test window ownership lost.");
            HoverFixtureApi.ShowWindow(window, command); Pause();
        }
        private static IntPtr Sized(Target target, List<IntPtr> windows, int width, int height)
        {
            var found = windows.Where(window => {
                Native.Rect rect;
                return target.Owns(window) && Native.GetWindowRect(window, out rect) && rect.Width == width && rect.Height == height;
            }).ToArray();
            if (found.Length != 1) return IntPtr.Zero;
            return found[0];
        }
        private static IntPtr TooltipWindow(Target target)
        {
            int found = 0;
            IntPtr result = IntPtr.Zero;
            foreach (IntPtr window in target.Windows())
            {
                var name = new StringBuilder(128);
                Native.GetClassName(window, name, name.Capacity);
                long style = Native.ReadStyle(window, -16), extended = Native.ReadStyle(window, -20);
                bool owned = Native.GetWindow(window, 4) != IntPtr.Zero;
                if (!TooltipDecision.Structural(target.Owns(window), name.ToString(), style, extended, owned)) continue;
                // Only structurally identified tooltips receive this bounded
                // fixed-caption check. Never inspect media-window captions.
                var caption = new StringBuilder(9);
                Native.GetWindowText(window, caption, caption.Capacity);
                if (TooltipDecision.Identity(true, name.ToString(), caption.ToString(), style, extended, owned)) { found++; result = window; }
            }
            return found == 1 ? result : IntPtr.Zero;
        }
        private static void Actual(HoverVlcRequest request)
        {
            Process process = null;
            bool cleanup = false, initialized = false, childObserved = false, tooltipTimerVisible = false;
            string discovery = "none";
            try
            {
                var start = new ProcessStartInfo(request.executable, request.arguments) {
                    UseShellExecute = false, CreateNoWindow = true, WorkingDirectory = Path.GetDirectoryName(request.executable) };
                foreach (string name in new[] { "VLC_PLUGIN_PATH", "VLC_DATA_PATH", "VLC_LIB_PATH" }) start.EnvironmentVariables.Remove(name);
                foreach (var entry in request.environment) start.EnvironmentVariables[entry.Key] = entry.Value;
                process = Process.Start(start);
                if (process == null) throw new InvalidOperationException("Owned test VLC did not start.");
                using (var target = new Target(process.Id, request.executable, request.installed, process.StartTime.ToUniversalTime().Ticks))
                {
                    int scale = request.scale;
                    var watch = Stopwatch.StartNew();
                    IntPtr video = IntPtr.Zero, bar = IntPtr.Zero, command = IntPtr.Zero;
                    while (watch.ElapsedMilliseconds < 120000)
                    {
                        if (!target.Alive()) throw new InvalidOperationException("Owned test VLC exited before ready.");
                        var windows = target.Windows();
                        video = target.FindVideo(windows, new Dimensions { width = 708*scale, height = 440*scale });
                        bar = Sized(target, windows, 362, 1);
                        command = Sized(target, windows, 133, 17);
                        string text = Log(request.log);
                        initialized = text.Contains("using interface module \"skins2\"") && text.Contains("requested skins " + request.skin + " is  accessible");
                        if (video != IntPtr.Zero && bar != IntPtr.Zero && command != IntPtr.Zero && initialized && target.VideoDiscovery == "child") break;
                        Pause();
                    }
                    Check(scale, "actual-owned-window-discovery-private-desktop", video != IntPtr.Zero && bar != IntPtr.Zero && command != IntPtr.Zero && initialized);
                    uint ownerPid;
                    Check(scale, "actual-vlc-thread-on-private-desktop", HoverFixtureApi.SameDesktop(Native.GetWindowThreadProcessId(video, out ownerPid)) && ownerPid == (uint)target.Pid);
                    Check(scale, "actual-native-tooltip-created", TooltipWindow(target) != IntPtr.Zero);
                    discovery = target.VideoDiscovery;
                    int x = point.X-150, y = point.Y-120;
                    Show(target, video, 4); Move(target, video, x, y);
                    bool onVideo, onBar; IntPtr root;
                    bool exposed = Read(video, bar, false, target.Pid, out onVideo, out onBar, out root);
                    Check(scale, "actual-exposed-video", exposed && onVideo && root == video);
                    Check(scale, "actual-video-show-decision", HoverDecision.Show(exposed, false, onVideo, false, 0));
                    IntPtr under = Native.WindowFromPoint(point);
                    childObserved = under != video && Native.GetAncestor(under, 2) == video;
                    Check(scale, "actual-embedded-vout-child", childObserved);
                    using (var blocker = new HoverFixtureWindow(point.X-30, point.Y-30, 100, 100, IntPtr.Zero))
                    {
                        // VLC can asynchronously raise its video after creating
                        // the vout. Establish actual native coverage before
                        // testing the product rejection, rather than assuming a
                        // cross-process SetWindowPos has settled immediately.
                        watch.Restart();
                        int placements = 0;
                        IntPtr nativeRoot = IntPtr.Zero;
                        do
                        {
                            blocker.Place(point.X-30, point.Y-30, 100, 100);
                            Pause(); placements++;
                            nativeRoot = Native.GetAncestor(Native.WindowFromPoint(point), 2);
                        } while (nativeRoot != blocker.Handle && watch.ElapsedMilliseconds < 3000);
                        Check(scale, "actual-occluder-native-coverage-established", nativeRoot == blocker.Handle);
                        exposed = Read(video, bar, false, target.Pid, out onVideo, out onBar, out root);
                        coverageReadbacks.Add(new { scale = scale, placements = placements,
                            nativeCoverageEstablished = nativeRoot == blocker.Handle,
                            productRoot = root == blocker.Handle ? "fixture-occluder" : root == video ? "selected-video" : root == bar ? "selected-bar" : "other",
                            exposed = exposed, pointerOnVideo = onVideo, pointerOnBar = onBar });
                        Check(scale, "actual-covered-video-no-show", !exposed && root == blocker.Handle && !HoverDecision.Show(exposed, false, true, true, 0));
                        blocker.Hide();
                    }
                    Show(target, video, 0);
                    exposed = Read(video, bar, false, target.Pid, out onVideo, out onBar, out root);
                    Check(scale, "actual-hidden-video-no-show", !exposed && !HoverDecision.Show(exposed, false, true, true, 0));
                    Show(target, video, 4); Move(target, video, x, y);
                    Show(target, video, 7);
                    Check(scale, "actual-native-minimized-state", Native.IsIconic(video));
                    exposed = Read(video, bar, false, target.Pid, out onVideo, out onBar, out root);
                    Check(scale, "actual-minimized-video-no-show", !exposed && !HoverDecision.Show(exposed, false, true, true, 0));
                    Show(target, video, 4); Move(target, video, x+708*scale+100, y);
                    exposed = Read(video, bar, false, target.Pid, out onVideo, out onBar, out root);
                    Check(scale, "actual-moved-video-stale-rect-rejected", !exposed && !HoverDecision.Show(exposed, false, true, true, 0));
                    Move(target, video, x, y);
                    exposed = Read(video, bar, false, target.Pid, out onVideo, out onBar, out root);
                    Check(scale, "actual-restored-exposed-video", exposed && onVideo);
                    if (!target.Owns(command) || !Native.PostMessage(command, 0x0203, new IntPtr(1), new IntPtr((2 << 16) | 2)))
                        throw new InvalidOperationException("Owned product hover command failed.");
                    watch.Restart();
                    Native.Rect bounds;
                    while (watch.ElapsedMilliseconds < 3000)
                    {
                        if (target.Owns(bar) && Native.GetWindowRect(bar, out bounds) && bounds.Width == 361 && bounds.Height == 64) break;
                        Pause();
                    }
                    Check(scale, "actual-bar-open-layout", target.Owns(bar) && Native.GetWindowRect(bar, out bounds) && bounds.Width == 361 && bounds.Height == 64);
                    CheckOpacity(scale, "actual-framed-bar", bar);
                    Move(target, bar, point.X-100, point.Y-40);
                    exposed = Read(video, bar, true, target.Pid, out onVideo, out onBar, out root);
                    Check(scale, "actual-open-bar-idle-retention", exposed && onBar && HoverDecision.Show(exposed, false, false, onBar, 10000));
                    Show(target, bar, 0);
                    Move(target, video, x+708*scale+100, y);
                    exposed = Read(video, bar, true, target.Pid, out onVideo, out onBar, out root);
                    Check(scale, "actual-hidden-bar-stale-rect-rejected", !exposed && !onBar && !HoverDecision.Show(exposed, false, true, true, 0));
                    IntPtr main = Sized(target, target.Windows(), 300*scale, 298*scale);
                    if (main != IntPtr.Zero)
                    {
                        Move(target, main, point.X-74*scale, point.Y-62*scale);
                        // Optional native timer observation on known Open media
                        // artwork. This is only an owned private window message,
                        // never a physical pointer move or action-button click.
                        if (target.Owns(main)) Native.PostMessage(main, 0x0200, IntPtr.Zero, new IntPtr(((62*scale) << 16) | (74*scale)));
                        watch.Restart();
                        while (watch.ElapsedMilliseconds < 1800)
                        {
                            IntPtr tooltip = TooltipWindow(target);
                            if (tooltip != IntPtr.Zero && Native.IsWindowVisible(tooltip)) { tooltipTimerVisible = true; break; }
                            Pause();
                        }
                    }
                    string finalLog = Log(request.log);
                    Check(scale, "actual-no-theme-error-or-fallback", !finalLog.Contains("skins2 error:") && !finalLog.Contains("xml error:")
                        && !finalLog.Contains("trying default skin") && !finalLog.Contains("trying the default skin")
                        && !finalLog.Contains("using default skin") && !finalLog.Contains("failed to load the skin"));
                }
            }
            finally
            {
                if (process != null)
                {
                    if (!process.HasExited) process.Kill();
                    cleanup = process.WaitForExit(10000);
                    process.Dispose();
                }
                actualResults.Add(new { scale = request.scale, initialized = initialized, discovery = discovery,
                    realEmbeddedChildObserved = childObserved, nativeTooltipVisibleAfterMotion = tooltipTimerVisible,
                    tooltipTimerScope = "Optional private WM_MOUSEMOVE observation; false is an unverified timer/display result, never a creation/exposure pass.", ownedProcessClosed = cleanup });
                if (!cleanup) throw new InvalidOperationException("Owned test VLC cleanup failed.");
            }
        }
        [STAThread]
        private static int Main(string[] args)
        {
            if ((args.Length != 3 && args.Length != 4) || !HoverFixtureApi.PrivateDesktop()) return 2;
            point = new Point(int.Parse(args[1]), int.Parse(args[2]));
            string error = null;
            try
            {
                Scale(1); Scale(2);
                if (args.Length == 4)
                {
                    var permit = Stopwatch.StartNew();
                    while (!File.Exists(args[3]+".ready") && permit.ElapsedMilliseconds < 10000) Pause();
                    if (!File.Exists(args[3]+".ready")) throw new InvalidOperationException("Owner job cleanup guard was not armed.");
                    foreach (var request in new JavaScriptSerializer().Deserialize<HoverVlcRequest[]>(File.ReadAllText(args[3]))) Actual(request);
                }
            }
            catch (Exception problem) { error = problem.GetType().Name + ": " + problem.Message; }
            var report = new { schemaVersion = 1, passed = error == null, error = error, cases = cases, actualVlc = actualResults, opacityReadbacks = opacityReadbacks, coverageReadbacks = coverageReadbacks,
                fixedTestPoint = true, pointerInputInjected = false, privateDesktop = true,
                scope = "Shared ReadExposure native topology and Show decision; optional actual VLT idle/playing windows, foreground-independent predicate. No complete helper timer/audio or user-input end-to-end certification.",
                cleanup = "All fixture windows disposed before report; desktop/process cleanup verified by Python owner." };
            using (var stream = new FileStream(args[0], FileMode.CreateNew, FileAccess.Write))
            using (var writer = new StreamWriter(stream)) writer.Write(new JavaScriptSerializer().Serialize(report));
            return error == null ? 0 : 1;
        }
    }
}
