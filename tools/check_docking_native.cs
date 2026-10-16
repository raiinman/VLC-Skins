// Private-desktop native CtrlMove/WindowManager probe. Python owns job cleanup.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Windows.Forms;
using System.IO;
using System.Linq;
using System.Threading;
using System.Web.Script.Serialization;

namespace NfsSkinSupport
{
    public class DockRect { public int x, y, width, height; }
    public sealed class DockPane : DockRect { public string id; public int gripX, gripY; }
    public sealed class DockStep
    {
        public string name, pane, kind, cover;
        public int gripX, gripY, dx, dy;
        public Dictionary<string, DockRect> expected;
    }
    public sealed class DockRequest
    {
        public int scale;
        public bool occlusion, sharedInstalledPlugins, snappingToggle, addonVideoShow;
        public string executable, installed, arguments, log, skin, workingDirectory;
        public Dictionary<string, string> environment;
        public DockPane[] panes;
        public DockStep[] steps;
    }
    internal static class DockingNativeFixture
    {
        [DllImport("user32.dll", CharSet=CharSet.Unicode)] private static extern IntPtr GetProp(IntPtr window, string name);
        [DllImport("user32.dll", CharSet=CharSet.Unicode)] private static extern bool SetProp(IntPtr window,string name,IntPtr value);
        [DllImport("user32.dll", CharSet=CharSet.Unicode)] private static extern IntPtr RemoveProp(IntPtr window, string name);
        [DllImport("dwmapi.dll")] private static extern int DwmGetWindowAttribute(IntPtr window,int attribute,out int value,int size);
        private static readonly List<object> exposureCases = new List<object>();
        private static readonly List<object> filterCases = new List<object>();
        private static Dictionary<string,long> FilterReadback(IntPtr bar)
        {
            var result=new Dictionary<string,long>();
            foreach (string key in new[] { "Status", "RejectedFirst", "RejectedSecond", "CheckCalls", "CanCalls", "FirstCalls", "SecondCalls",
                "InvalidTarget", "InvalidMoving", "TargetMoving", "Exposed", "SnappingSupported", "SnapBypasses", "DependentBypasses" })
                result.Add(key,GetProp(bar,"NfsOcclusionBridge."+key).ToInt64());
            return result;
        }
        private static void Cover(Target target, IntPtr main, HoverFixtureWindow cover, string mode, int scale)
        {
            var r = Bounds(target, main);
            if (mode == "full") cover.Place(r.Left-10,r.Top-10,r.Width+20,r.Height+20);
            else if (mode == "partial") cover.Place(r.Left-10,r.Top-10,r.Width/2+10,r.Height+20);
            else { Require(mode == "none", "Unknown cover mode."); cover.Hide(); }
            Application.DoEvents();
            int exposed=0, covered=0;
            for (int y=r.Top+5; y<r.Bottom; y+=13)
                for (int x=r.Left+5; x<r.Right; x+=13)
                {
                    IntPtr root=Native.GetAncestor(Native.WindowFromPoint(new Point(x,y)),2);
                    if (root==main) exposed++;
                    if (root==cover.Handle) covered++;
                }
            Require(mode=="full" ? exposed==0 && covered>0 : mode=="partial" ? exposed>0 && covered>0 : exposed>0,
                "Independent WindowFromPoint cover topology is not established: "+mode);
            uint pid; Native.GetWindowThreadProcessId(cover.Handle,out pid);
            Require(pid==(uint)Process.GetCurrentProcess().Id && pid!=(uint)target.Pid, "Cover must be a foreign owned fixture root.");
            int targetCloak,coverCloak;
            int targetResult=DwmGetWindowAttribute(main,14,out targetCloak,4);
            int coverResult=DwmGetWindowAttribute(cover.Handle,14,out coverCloak,4);
            exposureCases.Add(new { scale=scale, mode=mode, exposedSamples=exposed, foreignCoverSamples=covered,
                targetCloak=targetCloak, coverCloak=coverCloak, targetDwmResult=targetResult, coverDwmResult=coverResult });
            Require(targetResult==0 && coverResult==0 && targetCloak==0 && coverCloak==0,
                "Private desktop roots are cloaked or DWM visibility is unknown, exposure evidence is inconclusive.");
        }
        private static IntPtr AttachFilter(Target target, Dictionary<string,IntPtr> windows, WheelBridge bridge)
        {
            var bars=target.Windows().Where(window => {
                Native.Rect r;
                return Native.GetWindowRect(window,out r) && r.Left==-31000 && r.Top==-30800 &&
                    ((r.Width==362 && r.Height==1) || (r.Width==361 && r.Height==64));
            }).ToArray();
            Require(bars.Length==1,"Exact canonical private bridge window missing.");
            Owned(target,bars[0]); bridge.Attach(bars[0]);
            var wait=Stopwatch.StartNew();
            while (GetProp(bars[0],"NfsOcclusionBridge.Status").ToInt64()!=1 && wait.ElapsedMilliseconds<5000)
            {
                Message(target,windows["main"],0,0,0,0); Thread.Sleep(30);
            }
            Require(GetProp(bars[0],"NfsOcclusionBridge.Status").ToInt64()==1,"Exact native occlusion filter did not report successful installation. Status="+GetProp(bars[0],"NfsOcclusionBridge.Status").ToInt64()+", enabled="+GetProp(bars[0],"NfsSkinWheelBridge.Enabled").ToInt64()+", fixtureBits="+(IntPtr.Size*8));
            return bars[0];
        }
        private static readonly List<object> cases = new List<object>();
        private static readonly List<object> moduleCases = new List<object>();
        private static void ValidateSharedModules(Target target, DockRequest request)
        {
            string root=Path.GetDirectoryName(request.installed);
            var expected=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase) {
                { "libvlc.dll",Path.Combine(root,"libvlc.dll") },
                { "libvlccore.dll",Path.Combine(root,"libvlccore.dll") },
                { "libskins2_plugin.dll",Path.Combine(root,"plugins","gui","libskins2_plugin.dll") }
            };
            var found=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);
            target.Process.Refresh();
            foreach (ProcessModule module in target.Process.Modules)
                if (expected.ContainsKey(module.ModuleName))
                {
                    Require(!found.ContainsKey(module.ModuleName),"Duplicate shared module.");
                    found.Add(module.ModuleName,Path.GetFullPath(module.FileName));
                }
            foreach (var pair in expected)
                Require(found.ContainsKey(pair.Key) && String.Equals(found[pair.Key],Path.GetFullPath(pair.Value),StringComparison.OrdinalIgnoreCase),
                    "Private test must load exact standard installed module: "+pair.Key);
            string hash;
            using (var input=File.OpenRead(found["libskins2_plugin.dll"]))
            using (var sha=SHA256.Create()) hash=BitConverter.ToString(sha.ComputeHash(input)).Replace("-","").ToLowerInvariant();
            Require(hash=="c88b5d37fd554a968508d2d20ce4cec2279134b9840c05adba989b25d84682c5","Loaded standard GUI plugin hash changed.");
            string copied=Path.GetDirectoryName(request.executable);
            Require(!File.Exists(Path.Combine(copied,"libvlc.dll")) && !File.Exists(Path.Combine(copied,"libvlccore.dll")) &&
                !Directory.Exists(Path.Combine(copied,"plugins")),"Shared-mapping runtime must remain EXE-only.");
            moduleCases.Add(new { scale=request.scale,passed=true,loadedPaths=found,guiPluginSha256=hash,copiedExecutableOnly=true });
        }
        private static readonly List<object> sessions = new List<object>();
        private static void Require(bool ok, string message) { if (!ok) throw new InvalidOperationException(message); }
        private static void Owned(Target target, IntPtr window)
        {
            uint pid;
            Require(target.Alive() && target.Owns(window) &&
                HoverFixtureApi.SameDesktop(Native.GetWindowThreadProcessId(window, out pid)) && pid == (uint)target.Pid,
                "Private test HWND identity changed.");
        }
        private static Native.Rect Bounds(Target target, IntPtr window)
        {
            Owned(target, window); Native.Rect bounds;
            Require(Native.GetWindowRect(window, out bounds), "Cannot read owned test rectangle."); return bounds;
        }
        private static void Message(Target target, IntPtr window, uint message, int flags, int x, int y)
        {
            Owned(target, window);
            Require(x >= short.MinValue && x <= short.MaxValue && y >= short.MinValue && y <= short.MaxValue, "Message coordinate out of range.");
            long packed = ((long)(ushort)y << 16) | (ushort)x;
            Require(Native.PostMessage(window, message, new IntPtr(flags), new IntPtr(packed)), "Owned drag message failed.");
        }
        private static bool Same(Native.Rect actual, DockRect wanted)
        { return actual.Left == wanted.x && actual.Top == wanted.y && actual.Width == wanted.width && actual.Height == wanted.height; }
        private static Dictionary<string, DockRect> Snapshot(Target target, Dictionary<string, IntPtr> windows)
        {
            var result = new Dictionary<string, DockRect>();
            foreach (var item in windows) { var r = Bounds(target, item.Value); result.Add(item.Key, new DockRect { x=r.Left, y=r.Top, width=r.Width, height=r.Height }); }
            return result;
        }
        private static bool Matches(Target target, Dictionary<string, IntPtr> windows, Dictionary<string, DockRect> expected)
        { return expected.All(item => Same(Bounds(target, windows[item.Key]), item.Value)); }
        private static void Step(Target target, Dictionary<string, IntPtr> windows, DockRequest request, DockStep step)
        {
            Require(windows.ContainsKey(step.pane) && step.expected.Count == windows.Count, "Incomplete docking expectation.");
            IntPtr window = windows[step.pane];
            bool released = false, matched = false;
            Message(target, window, 0x200, 0, step.gripX, step.gripY);
            Message(target, window, 0x201, 1, step.gripX, step.gripY);
            try
            {
                if (step.kind == "click")
                {
                    Message(target, window, 0x202, 0, step.gripX, step.gripY); released = true;
                    Thread.Sleep(200);
                }
                else
                {
                    Require(step.kind == "move" || step.kind == "resize", "Unknown docking step.");
                    Message(target, window, 0x200, 1, step.gripX + step.dx, step.gripY + step.dy);
                }
                var wait = Stopwatch.StartNew();
                while (wait.ElapsedMilliseconds < 5000)
                {
                    if (Matches(target, windows, step.expected)) { matched = true; break; }
                    Thread.Sleep(30);
                }
            }
            finally { if (!released) Message(target, window, 0x202, 0, step.gripX, step.gripY); }
            // UP rebuilds the native dependency graph. Give that queue entry time
            // before the next independent gesture; every gesture checks all panes.
            Thread.Sleep(120);
            matched = matched && Matches(target, windows, step.expected);
            cases.Add(new { scale=request.scale, name=step.name, passed=matched, expected=step.expected, actual=Snapshot(target, windows) });
            Require(matched, "Native docking mismatch: " + step.name);
        }
        private static IntPtr ProtocolWindow(Target target,bool command)
        {
            var found=target.Windows().Where(window => {
                Native.Rect r;
                return Native.IsWindowVisible(window) && Native.GetWindowRect(window,out r) &&
                    (command ? SnappingProtocol.Command(r) : SnappingProtocol.State(r));
            }).ToArray();
            Require(found.Length==1,"Unique native snapping protocol window missing."); Owned(target,found[0]); return found[0];
        }
        private static void WaitWidth(Target target,IntPtr window,int width)
        {
            var wait=Stopwatch.StartNew();
            while (Bounds(target,window).Width!=width && wait.ElapsedMilliseconds<5000) Thread.Sleep(30);
            Require(Bounds(target,window).Width==width,"Native snapping protocol width mismatch, wanted "+width);
        }
        private static void SetSnappingUi(Target target,IntPtr command,IntPtr state,int desired)
        {
            Message(target,command,0x203,1,0,0); WaitWidth(target,command,191);
            Message(target,command,0x203,1,SnappingProtocol.StateCell(desired),0); WaitWidth(target,state,desired);
        }
        private static void ToggleThroughFooter(Target target,Dictionary<string,IntPtr> windows,DockRequest request,
            WheelBridge bridge,IntPtr command,IntPtr state,bool enabled)
        {
            Require(bridge.SnappingSupported,"Shared helper does not report native toggle support.");
            Require(Bounds(target,command).Width==191,"Native command must begin ready.");
            Require(Bounds(target,state).Width==(enabled ? 203 : 202),"Footer state must precede toggle.");
            var observer=new SnappingRequest(); Require(!observer.Observe(191,true),"Ready state must not toggle.");
            var rect=Bounds(target,windows["tracks"]);
            int x=110*request.scale,y=rect.Height-17*request.scale;
            Message(target,windows["tracks"],0x200,0,x,y);
            Message(target,windows["tracks"],0x201,1,x,y);
            Message(target,windows["tracks"],0x202,0,x,y);
            WaitWidth(target,command,192);
            Require(observer.Observe(192,true) && !observer.Observe(192,true),"Native footer request must be handled exactly once.");
            Require(bridge.SetSnapping(enabled),"Shared native toggle setter failed.");
            SetSnappingUi(target,command,state,SnappingProtocol.DesiredWidth(true,enabled));
            Require(!observer.Observe(Bounds(target,command).Width,true),"ACK must return request to ready without another toggle.");
        }
        private static void AddonVideoShow(Target target,Dictionary<string,IntPtr> windows,DockRequest request)
        {
            var commands=target.Windows().Where(window => {
                Native.Rect r;return Native.IsWindowVisible(window) && Native.GetWindowRect(window,out r) &&
                    r.Left==-31000 && r.Top==-30600 && r.Height==17 && r.Width>=211 && r.Width<=213;
            }).ToArray();
            Require(commands.Length==1,"Addon native video command window missing.");
            IntPtr command=commands[0],video=windows["video"];Owned(target,command);
            foreach(bool show in new[] {false,true,true,false,true})
            {
                Message(target,command,0x203,1,show ? 100 : 110,0);
                var wait=Stopwatch.StartNew();
                while(Native.IsWindowVisible(video)!=show && wait.ElapsedMilliseconds<5000)Thread.Sleep(30);
                Require(Native.IsWindowVisible(video)==show,"Addon native video visibility failed.");
                Thread.Sleep(200);Require(Native.IsWindowVisible(video)==show,"Addon native video visibility did not remain stable.");
                cases.Add(new {scale=request.scale,name=show ? "addon-video-show-native-readback" : "fixture-only-video-hide-native-readback",passed=true,visible=show,
                    nativeCell=show ? 100 : 110,commandWidth=Bounds(target,command).Width,testOnlyHideCell=true});
            }
        }
        private static void Actual(DockRequest request)
        {
            Process process = null; bool cleaned = false;
            try
            {
                var start = new ProcessStartInfo(request.executable, request.arguments) {
                    UseShellExecute=false, CreateNoWindow=true, WorkingDirectory=request.workingDirectory ?? Path.GetDirectoryName(request.executable) };
                foreach (string name in new[] { "VLC_PLUGIN_PATH", "VLC_DATA_PATH", "VLC_LIB_PATH", "VLC_USERDATA_PATH" }) start.EnvironmentVariables.Remove(name);
                foreach (var item in request.environment) start.EnvironmentVariables[item.Key]=item.Value;
                process = Process.Start(start); Require(process != null, "Private VLC launch failed.");
                // Process.Start may return before its main module is available.
                // Wait only on this retained child, then perform normal full trust validation.
                bool moduleReady=false; var moduleWait=Stopwatch.StartNew();
                while (!process.HasExited && moduleWait.ElapsedMilliseconds<10000)
                {
                    process.Refresh();
                    try { if (process.MainModule!=null) { moduleReady=true; break; } }
                    catch (System.ComponentModel.Win32Exception) { }
                    Thread.Sleep(30);
                }
                Require(moduleReady,"Owned VLC main module did not initialize.");
                using (var target = new Target(process.Id, request.executable, request.installed, process.StartTime.ToUniversalTime().Ticks))
                {
                    var windows = new Dictionary<string, IntPtr>(); var wait = Stopwatch.StartNew();
                    while (wait.ElapsedMilliseconds < 120000)
                    {
                        Require(target.Alive(), "Private VLC exited before ready."); windows.Clear();
                        foreach (DockPane pane in request.panes)
                        {
                            var found = target.Windows().Where(window => { Native.Rect r; return Native.IsWindowVisible(window) && Native.GetWindowRect(window, out r) && Same(r,pane); }).ToArray();
                            if (found.Length == 1) windows.Add(pane.id, found[0]);
                        }
                        if (windows.Count == request.panes.Length) break;
                        Thread.Sleep(100);
                    }
                    Require(windows.Count == 5, "All five exact private pane rectangles must initialize.");
                    foreach (IntPtr window in windows.Values) Owned(target,window);
                    if (request.sharedInstalledPlugins) ValidateSharedModules(target,request);
                    Thread.Sleep(1000);
                    if (!request.occlusion)
                        foreach (DockStep step in request.steps) Step(target,windows,request,step);
                    else
                    {
                        using (var cover=new HoverFixtureWindow(0,0,1,1,IntPtr.Zero))
                        using (var bridge=new WheelBridge(target))
                        {
                            cover.Hide(); IntPtr bar=IntPtr.Zero, snapCommand=IntPtr.Zero, snapState=IntPtr.Zero;
                            foreach (DockStep step in request.steps)
                            {
                                Cover(target,windows["main"],cover,step.cover ?? "none",request.scale);
                                if (step.kind=="toggle-off" || step.kind=="toggle-on")
                                {
                                    Require(bar!=IntPtr.Zero,"Toggle needs an attached bridge."); Owned(target,bar);
                                    Require(GetProp(bar,"NfsOcclusionBridge.Status").ToInt64()==1 && GetProp(bar,"NfsOcclusionBridge.SnappingSupported").ToInt64()==1 &&
                                        GetProp(bar,"NfsSkinWheelBridge.Enabled").ToInt64()==0x4E465357,"Exact native snapping toggle is unsupported.");
                                    ToggleThroughFooter(target,windows,request,bridge,snapCommand,snapState,step.kind=="toggle-on");
                                    long wanted=step.kind=="toggle-off" ? 1 : 0;
                                    Require(GetProp(bar,"NfsSkinWheelBridge.SnappingOff").ToInt64()==wanted && Matches(target,windows,step.expected),"Toggle state/geometry readback failed.");
                                    cases.Add(new { scale=request.scale,name=step.name,passed=true,snappingOff=wanted,supported=1,footerRequestObserved=192,commandWidth=Bounds(target,snapCommand).Width,stateWidth=Bounds(target,snapState).Width,settingsIoUsed=false });
                                }
                                else if (step.kind=="disable")
                                {
                                    Require(bar!=IntPtr.Zero && RemoveProp(bar,"NfsSkinWheelBridge.Enabled").ToInt64()==0x4E465357,"Candidate enable marker missing before fallback test.");
                                    cases.Add(new { scale=request.scale,name=step.name,passed=Matches(target,windows,step.expected),markerRemoved=true });
                                    Require(Matches(target,windows,step.expected),"Marker removal changed pane geometry.");
                                }
                                else if (step.kind=="bridge")
                                {
                                    bar=AttachFilter(target,windows,bridge);
                                    if(request.snappingToggle)
                                    {
                                        Require(bridge.SnappingSupported,"Native toggle support missing.");
                                        snapCommand=ProtocolWindow(target,true);snapState=ProtocolWindow(target,false);
                                        Require(Bounds(target,snapCommand).Width==191 && Bounds(target,snapState).Width==201,"Protocol defaults changed.");
                                        Require(bridge.SetSnapping(true),"Cannot initialize supported ON state.");
                                        SetSnappingUi(target,snapCommand,snapState,202);
                                        cases.Add(new { scale=request.scale,name="native-snapping-default-unavailable-to-supported-on",passed=true,commandWidth=191,stateWidth=202 });
                                    }
                                    cases.Add(new { scale=request.scale,name=step.name,passed=Matches(target,windows,step.expected),status=GetProp(bar,"NfsOcclusionBridge.Status").ToInt64() });
                                    Require(Matches(target,windows,step.expected),"Filter attach changed pane geometry.");
                                }
                                else
                                {
                                    long before=bar==IntPtr.Zero ? 0 : GetProp(bar,"NfsOcclusionBridge.RejectedFirst").ToInt64()+GetProp(bar,"NfsOcclusionBridge.RejectedSecond").ToInt64();
                                    long bypassBefore=bar==IntPtr.Zero ? 0 : GetProp(bar,"NfsOcclusionBridge.SnapBypasses").ToInt64();
                                    long dependentBefore=bar==IntPtr.Zero ? 0 : GetProp(bar,"NfsOcclusionBridge.DependentBypasses").ToInt64();
                                    try { Step(target,windows,request,step); }
                                    finally { if (bar!=IntPtr.Zero) filterCases.Add(new { scale=request.scale,name=step.name,readback=FilterReadback(bar) }); }
                                    if (step.name.StartsWith("snapping-off-",StringComparison.Ordinal))
                                        Require(GetProp(bar,"NfsOcclusionBridge.SnapBypasses").ToInt64()>bypassBefore,"OFF native snap path was not exercised.");
                                    if (step.name=="snapping-off-main-does-not-carry-attached-child")
                                        Require(GetProp(bar,"NfsOcclusionBridge.DependentBypasses").ToInt64()>dependentBefore,"OFF attached-group bypass was not exercised.");
                                    if (step.name=="filtered-covered-target-does-not-attract" || step.name=="restored-on-covered-target-does-not-attract")
                                    {
                                        long after=GetProp(bar,"NfsOcclusionBridge.RejectedFirst").ToInt64()+GetProp(bar,"NfsOcclusionBridge.RejectedSecond").ToInt64();
                                        Require(after>before,"Covered rejection did not exercise the native filter.");
                                    }
                                }
                            }
                        }
                    }
                    if(request.addonVideoShow) AddonVideoShow(target,windows,request);
                }
            }
            finally
            {
                if (process != null) { if (!process.HasExited) process.Kill(); cleaned=process.WaitForExit(10000); process.Dispose(); }
                sessions.Add(new { scale=request.scale, ownedProcessClosed=cleaned });
                Require(cleaned,"Private VLC cleanup failed.");
            }
        }
        [STAThread] private static int Main(string[] args)
        {
            if (args.Length != 2 || !HoverFixtureApi.PrivateDesktop()) return 2;
            Native.SetProcessDPIAware();
            string error = null;
            try
            {
                var wait=Stopwatch.StartNew();
                while (!File.Exists(args[1]+".ready") && wait.ElapsedMilliseconds<10000) Thread.Sleep(30);
                Require(File.Exists(args[1]+".ready"),"Owner cleanup job not armed.");
                foreach (var request in new JavaScriptSerializer().Deserialize<DockRequest[]>(File.ReadAllText(args[1]))) Actual(request);
            }
            catch (Exception problem) { error=problem.GetType().Name+": "+problem.Message+"\n"+problem.StackTrace; }
            var report=new { passed=error==null, error=error, cases=cases, exposureCases=exposureCases, filterCases=filterCases, moduleCases=moduleCases, sessions=sessions, privateDesktop=true,
                physicalInputInjected=false, syntheticOwnedWindowMessages=true, vlcPaneSetWindowPosUsed=false, foreignFixtureCoverPositioned=true,
                resizeToggleLimit="Canonical main is the only higher-priority grouping parent and has no resize control. OFF attached auxiliary resize verifies unchanged neighbors plus native SnapBypasses, not an ON-carry versus OFF-carry resize contrast.",
                scope="Exact native CtrlMove/Anchor/WindowManager and CtrlResize geometry after bounded private window messages. Clock click is only an attempt with geometry checks, not independent active-layout readback. No physical-pointer, repaint smoothness, or user-session certification." };
            using(var stream=new FileStream(args[0],FileMode.CreateNew,FileAccess.Write))
            using(var writer=new StreamWriter(stream)) writer.Write(new JavaScriptSerializer().Serialize(report));
            return error==null ? 0 : 1;
        }
    }
}
