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
        internal HoverFixtureWindow(int x, int y, int width, int height, IntPtr parent, bool skinClass = false)
        {
            if (skinClass) HoverFixtureApi.RegisterSkinClass();
            child = parent != IntPtr.Zero;
            if (skinClass) { AssignHandle(HoverFixtureApi.CreateSkinWindow(x,y,width,height)); return; }
            CreateHandle(new CreateParams { Caption = "NFS private exposure fixture", ClassName = skinClass ? "SkinWindowClass" : null,
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
        private delegate IntPtr WindowProcedure(IntPtr hwnd, uint message, IntPtr wp, IntPtr lp);
        [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
        private struct WindowClass
        {
            internal uint Style; internal WindowProcedure Procedure;
            internal int ClassExtra, WindowExtra;
            internal IntPtr Instance, Icon, Cursor, Background;
            internal string MenuName, ClassName;
        }
        [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] private static extern ushort RegisterClass(ref WindowClass value);
        [DllImport("user32.dll",CharSet=CharSet.Unicode)] private static extern IntPtr DefWindowProc(IntPtr hwnd,uint message,IntPtr wp,IntPtr lp);
        [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] private static extern IntPtr GetModuleHandle(string name);
        private static readonly WindowProcedure skinProcedure = DefWindowProc;
        private static bool skinRegistered;
        [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] private static extern IntPtr CreateWindowEx(uint exStyle,string className,string title,uint style,int x,int y,int width,int height,IntPtr parent,IntPtr menu,IntPtr instance,IntPtr param);
        internal static IntPtr CreateSkinWindow(int x,int y,int width,int height)
        {
            IntPtr result=CreateWindowEx(0x08000080,"SkinWindowClass","",0x80000000,x,y,width,height,IntPtr.Zero,IntPtr.Zero,GetModuleHandle(null),IntPtr.Zero);
            if(result==IntPtr.Zero) throw new InvalidOperationException("Private skin fixture window creation failed.");
            return result;
        }
        internal static void RegisterSkinClass()
        {
            if (skinRegistered) return;
            var value = new WindowClass { Style=0x4000, Procedure=skinProcedure, Instance=GetModuleHandle(null), ClassName="SkinWindowClass" };
            if (RegisterClass(ref value)==0) throw new InvalidOperationException("Private skin fixture class registration failed.");
            skinRegistered=true;
        }
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
                bool wroteAlpha = Native.SetBarOpacity(bar);
                uint colorKey, flags; byte alpha;
                bool read = HoverFixtureApi.GetLayeredWindowAttributes(bar, out colorKey, out alpha, out flags);
                bool layered = (Native.ReadStyle(bar, -20) & 0x80000) != 0;
                opacityReadbacks.Add(new { scale = scale, bar = prefix, reassert = pass != 0,
                    readSucceeded = read, alpha = alpha, flags = flags, layered = layered, wroteAlpha = wroteAlpha });
                Check(scale, prefix + (pass == 0 ? "-opaque-alpha255" : "-opaque-alpha255-reassert"),
                    read && flags == 2 && alpha == 255 && layered);
                if (pass != 0) Check(scale, prefix + "-unchanged-alpha-not-rewritten", !wroteAlpha);
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
        private static void SnappingSettings(string reportPath)
        {
            string folder=Path.Combine(Path.GetDirectoryName(reportPath),"snapping-settings-fixture");
            Directory.CreateDirectory(folder);
            string path=Path.Combine(folder,"snapping-enabled.txt");
            Check(0,"snapping-settings-missing-default-on",SkinSnapping.Load(path));
            Check(0,"snapping-settings-save-off",SkinSnapping.Save(path,false)&&File.ReadAllText(path)=="false");
            Check(0,"snapping-settings-reload-shared-off",!SkinSnapping.Load(path));
            Check(0,"snapping-settings-replace-on",SkinSnapping.Save(path,true)&&SkinSnapping.Load(path));
            File.WriteAllText(path,"invalid");
            Check(0,"snapping-settings-invalid-default-on",SkinSnapping.Load(path));
            string blocked=Path.Combine(folder,"directory-instead-of-file");Directory.CreateDirectory(blocked);
            Check(0,"snapping-settings-write-failure-contained",!SkinSnapping.Save(blocked,false)&&Directory.Exists(blocked));
            Check(0,"snapping-settings-no-temporary-files",Directory.GetFiles(folder,"*.tmp").Length==0);
        }
        private static void ClockTooltipGate(int scale)
        {
            int pid=Process.GetCurrentProcess().Id;
            using (var skin=new HoverFixtureWindow(point.X-80,point.Y-80,300*scale,298*scale,IntPtr.Zero,true))
            using (var cover=new HoverFixtureWindow(point.X-20,point.Y-20,80,80,IntPtr.Zero))
            using (var state=new HoverFixtureWindow(-31000,-30200,151,17,IntPtr.Zero,true))
            using (var fixedCommand=new HoverFixtureWindow(-31000,-29900,181,17,IntPtr.Zero,true))
            using (var wrongClass=new HoverFixtureWindow(-31000,-29900,181,17,IntPtr.Zero))
            {
                fixedCommand.Place(-31000,-29900,181,17);
                wrongClass.Place(-31000,-29900,181,17);
                Check(scale,"clock-fixed-command-exact-native-identity",ClockRefreshDecision.IsFixedCommand(pid,fixedCommand.Handle));
                Check(scale,"clock-fixed-command-other-pid-rejected",!ClockRefreshDecision.IsFixedCommand(pid+1,fixedCommand.Handle));
                Check(scale,"clock-fixed-command-wrong-class-rejected",!ClockRefreshDecision.IsFixedCommand(pid,wrongClass.Handle));
                fixedCommand.Hide();
                Check(scale,"clock-fixed-command-hidden-rejected",!ClockRefreshDecision.IsFixedCommand(pid,fixedCommand.Handle));
                fixedCommand.Place(-31000,-29901,181,17);
                Check(scale,"clock-fixed-command-wrong-position-rejected",!ClockRefreshDecision.IsFixedCommand(pid,fixedCommand.Handle));
                fixedCommand.Place(-31000,-29900,182,17);
                Check(scale,"clock-fixed-command-wrong-size-rejected",!ClockRefreshDecision.IsFixedCommand(pid,fixedCommand.Handle));
                skin.Place(point.X-80,point.Y-80,300*scale,298*scale);
                Check(scale,"tooltip-clock-deferred-over-exposed-skin",ClockRefreshDecision.PointerOverSkin(pid,point));
                Check(scale,"tooltip-clock-foreign-pid-not-deferred",!ClockRefreshDecision.PointerOverSkin(pid+1,point));
                cover.Place(point.X-20,point.Y-20,80,80);
                Check(scale,"tooltip-clock-resumes-over-covering-root",!ClockRefreshDecision.PointerOverSkin(pid,point));
                cover.Hide(); skin.Hide();
                Check(scale,"tooltip-clock-resumes-after-leave",!ClockRefreshDecision.PointerOverSkin(pid,point));
                state.Place(-31000,-30200,151,17);
                Check(scale,"tooltip-clock-offscreen-state-excluded",!ClockRefreshDecision.PointerOverSkin(pid,new Point(-30999,-30199)));
            }
        }
        private static void Stacking(int scale)
        {
            int pid = Process.GetCurrentProcess().Id, x = point.X - 150, y = point.Y - 120;
            using (var video = new HoverFixtureWindow(x, y, 708*scale, 440*scale, IntPtr.Zero))
            using (var bar = new HoverFixtureWindow(point.X-20, point.Y-20, 361, 64, IntPtr.Zero))
            using (var browser = new HoverFixtureWindow(point.X-40, point.Y-40, 180, 150, IntPtr.Zero))
            using (var popup = new HoverFixtureWindow(point.X-10, point.Y-10, 80, 80, IntPtr.Zero))
            using (var cascade = new HoverFixtureWindow(point.X-5,point.Y-5,70,70,IntPtr.Zero))
            using (var originalOwner = new HoverFixtureWindow(-30000,-30000,1,1,IntPtr.Zero))
            using (var stacking = new HoverStacking(pid))
            {
                video.Place(x,y,708*scale,440*scale); bar.Place(point.X-20,point.Y-20,361,64);
                Check(scale,"stack-original-owner-set",Native.SetOwner(bar.Handle,originalOwner.Handle));
                Native.SetWindowPos(video.Handle,new IntPtr(-2),0,0,0,0,0x0213);
                Check(scale,"stack-bind-and-place",stacking.Place(video.Handle,bar.Handle,point.X-20,point.Y-20));
                Check(scale,"stack-video-owns-bar",Native.GetWindow(bar.Handle,4)==video.Handle);
                Check(scale,"stack-normal-video-no-global-topmost",(Native.ReadStyle(bar.Handle,-20)&8)==0&&(Native.ReadStyle(video.Handle,-20)&8)==0);
                browser.Place(point.X-40,point.Y-40,180,150);
                Native.SetWindowPos(browser.Handle,new IntPtr(-2),0,0,0,0,0x0213);
                Native.SetWindowPos(browser.Handle,IntPtr.Zero,0,0,0,0,0x0213);
                Application.DoEvents();
                Check(scale,"stack-browser-covers-video-and-bar",Native.GetAncestor(Native.WindowFromPoint(point),2)==browser.Handle);
                Check(scale,"stack-covered-reposition-succeeds",stacking.Place(video.Handle,bar.Handle,point.X-20,point.Y-20));
                Check(scale,"stack-refresh-does-not-raise-video-pair",Native.GetAncestor(Native.WindowFromPoint(point),2)==browser.Handle);
                bool onVideo,onBar;IntPtr root;
                Check(scale,"stack-covered-exposure-denied",!Read(video.Handle,bar.Handle,true,pid,out onVideo,out onBar,out root));
                // Simulate the native owner being raised, not physical activation.
                Native.SetWindowPos(video.Handle,IntPtr.Zero,0,0,0,0,0x0213);
                Application.DoEvents();
                coverageReadbacks.Add(new { scale=scale, phase="video-owner-raise", root=Native.GetAncestor(Native.WindowFromPoint(point),2).ToInt64(),
                    video=video.Handle.ToInt64(), bar=bar.Handle.ToInt64(), browser=browser.Handle.ToInt64(),
                    videoPrevious=Native.GetWindow(video.Handle,3).ToInt64(), barNext=Native.GetWindow(bar.Handle,2).ToInt64(),
                    barVisible=Native.IsWindowVisible(bar.Handle), videoStyle=Native.ReadStyle(video.Handle,-20), barStyle=Native.ReadStyle(bar.Handle,-20) });
                Check(scale,"stack-video-raise-and-helper-sync-lift-bar",stacking.Place(video.Handle,bar.Handle,point.X-20,point.Y-20)&&Native.GetWindow(bar.Handle,4)==video.Handle&&Native.GetAncestor(Native.WindowFromPoint(point),2)==bar.Handle);
                Check(scale,"stack-exposed-inactive-bar-retained",Read(video.Handle,bar.Handle,true,pid,out onVideo,out onBar,out root)&&onBar);
                popup.Place(point.X-10,point.Y-10,80,80);
                Native.SetWindowPos(popup.Handle,new IntPtr(-2),0,0,0,0,0x0213);
                Native.SetWindowPos(popup.Handle,IntPtr.Zero,0,0,0,0,0x0213);
                Check(scale,"stack-popup-remains-above-after-refresh",stacking.Place(video.Handle,bar.Handle,point.X-20,point.Y-20)&&Native.GetAncestor(Native.WindowFromPoint(point),2)==popup.Handle);
                Check(scale,"stack-unowned-popup-does-not-maintain-bar",!Read(video.Handle,bar.Handle,true,pid,out onVideo,out onBar,out root));
                Check(scale,"stack-popup-owner-assigned",Native.SetOwner(popup.Handle,bar.Handle));
                Check(scale,"stack-owned-popup-maintains-bar",Read(video.Handle,bar.Handle,true,pid,out onVideo,out onBar,out root)&&onBar&&HoverDecision.Show(true,false,false,onBar,9000));
                cascade.Place(point.X-5,point.Y-5,70,70);
                Check(scale,"stack-cascade-owner-assigned",Native.SetOwner(cascade.Handle,popup.Handle));
                Native.SetWindowPos(cascade.Handle,IntPtr.Zero,0,0,0,0,0x0213);
                Check(scale,"stack-owned-cascade-maintains-bar",Read(video.Handle,bar.Handle,true,pid,out onVideo,out onBar,out root)&&onBar&&root==cascade.Handle);
                cascade.Hide();
                Point outsideBar = new Point(point.X - 30, point.Y + 10);
                Native.SetWindowPos(popup.Handle,IntPtr.Zero,outsideBar.X-5,outsideBar.Y-5,80,80,0x0014);
                Application.DoEvents();
                stacking.Place(video.Handle,bar.Handle,point.X-20,point.Y-20);
                bool popupExposure = HoverDecision.ReadExposure(pid,video.Handle,bar.Handle,true,outsideBar,out root,out onVideo,out onBar);
                Native.Rect barBounds; Native.GetWindowRect(bar.Handle,out barBounds);
                coverageReadbacks.Add(new { scale=scale, phase="outside-popup", root=root.ToInt64(), popup=popup.Handle.ToInt64(), popupExposure=popupExposure, onBar=onBar, contains=barBounds.Contains(outsideBar), owner=Native.GetWindow(popup.Handle,4).ToInt64(), below=HoverDecision.FirstVisibleRootBelow(bar.Handle,new Point(barBounds.Left+barBounds.Width/2,barBounds.Top+barBounds.Height/2)).ToInt64(), video=video.Handle.ToInt64(), x=outsideBar.X,y=outsideBar.Y });
                Check(scale,"stack-owned-popup-outside-bar-keeps-exact-desired",!barBounds.Contains(outsideBar)&&root==popup.Handle&&popupExposure&&HoverDecision.Show(popupExposure,false,false,onBar,9000,false));
                popup.Hide();
                // Regression topology: an independently raised bar above a browser
                // must not maintain itself using its own remembered rectangle.
                Native.SetWindowPos(browser.Handle,IntPtr.Zero,0,0,0,0,0x0213);
                Native.SetWindowPos(bar.Handle,IntPtr.Zero,0,0,0,0,0x0213);
                Check(scale,"stack-stale-floating-bar-topology",Native.GetAncestor(Native.WindowFromPoint(point),2)==bar.Handle&&HoverDecision.FirstVisibleRootBelow(bar.Handle,point)==browser.Handle);
                Check(scale,"stack-bar-over-covered-video-denied",!Read(video.Handle,bar.Handle,true,pid,out onVideo,out onBar,out root)&&!onBar);
                browser.Hide();
                Native.SetWindowPos(video.Handle,new IntPtr(-1),0,0,0,0,0x0213);
                Check(scale,"stack-respects-video-topmost-intent",stacking.Place(video.Handle,bar.Handle,point.X-20,point.Y-20)&&(Native.ReadStyle(bar.Handle,-20)&8)!=0);
                Native.SetWindowPos(video.Handle,new IntPtr(-2),0,0,0,0,0x0213);
                Check(scale,"stack-demotes-with-video",stacking.Place(video.Handle,bar.Handle,point.X-20,point.Y-20)&&(Native.ReadStyle(bar.Handle,-20)&8)==0);
                stacking.Dispose();
                Check(scale,"stack-original-owner-restored",Native.GetWindow(bar.Handle,4)==originalOwner.Handle);
                Check(scale,"stack-owner-cycle-rejected",Native.SetOwner(video.Handle,bar.Handle)&&!stacking.Bind(video.Handle,bar.Handle));
                Native.SetOwner(video.Handle,IntPtr.Zero);
            }
        }
        private static IntPtr ClockState(Target target)
        {
            var matches=target.Windows().Where(window => { Native.Rect bounds; return target.Owns(window)&&Native.GetWindowRect(window,out bounds)&&ClockRefreshDecision.Matches(bounds); }).ToList();
            return matches.Count==1 ? matches[0] : IntPtr.Zero;
        }
        private static bool WaitTooltip(Target target, bool visible, int timeout)
        {
            var watch=Stopwatch.StartNew();
            do { IntPtr tip=TooltipWindow(target); if(tip!=IntPtr.Zero&&Native.IsWindowVisible(tip)==visible)return true; Pause(); } while(watch.ElapsedMilliseconds<timeout);
            return false;
        }
        private static void PrivateTooltipHit(Target target,IntPtr main,int x,int y)
        {
            if(!target.Owns(main)||!Native.PostMessage(main,0x0206,IntPtr.Zero,new IntPtr((y<<16)|(x&0xffff)))) throw new InvalidOperationException("Owned tooltip hit probe failed.");
            Pause();
        }
        private static void ActualClockTooltip(int scale,Target target,IntPtr main)
        {
            var commands=target.Windows().Where(window=>ClockRefreshDecision.IsFixedCommand(target.Pid,window)).ToList();
            Check(scale,"actual-fixed-clock-command-discovery",commands.Count==1);
            IntPtr fixedCommand=commands[0],state=ClockState(target);
            Check(scale,"actual-clock-state-discovery",state!=IntPtr.Zero);
            foreach(int cell in new[]{0,10})
            {
                if(!target.Owns(fixedCommand)||!Native.PostMessage(fixedCommand,0x0203,new IntPtr(1),new IntPtr(cell)))throw new InvalidOperationException("Owned fixed clock command failed.");
                Pause();
                // Leave/re-enter the same original control after priming each
                // persistent Image. Right-double-click has no CtrlButton FSM
                // transition, and avoids WM_MOUSEMOVE TrackMouseEvent on a
                // non-input desktop. It performs only native hit/tooltip logic.
                PrivateTooltipHit(target,main,0,0);
                PrivateTooltipHit(target,main,74*scale,62*scale);
                Check(scale,"actual-tooltip-visible-before-fixed-cell-"+cell,WaitTooltip(target,true,1800));
                for(int repeat=0;repeat<3;repeat++)
                {
                    var pause=Stopwatch.StartNew(); while(pause.ElapsedMilliseconds<500)Pause();
                    if(!target.Owns(fixedCommand)||!Native.PostMessage(fixedCommand,0x0203,new IntPtr(1),new IntPtr(cell)))throw new InvalidOperationException("Owned fixed clock repeat failed.");
                    Pause(); Native.Rect bounds;
                    Check(scale,"actual-fixed-cell-"+cell+"-phase-b-"+repeat,target.Owns(state)&&Native.GetWindowRect(state,out bounds)&&bounds.Width==(cell==0?152:154));
                    Check(scale,"actual-tooltip-survives-fixed-cell-"+cell+"-"+repeat,WaitTooltip(target,true,200));
                }
            }
            // Reproduce the original native failure after establishing the new
            // path: changing the clicked state's Image cancels the global tip.
            if(!target.Owns(state)||!Native.PostMessage(state,0x0203,new IntPtr(1),IntPtr.Zero))throw new InvalidOperationException("Owned legacy clock baseline failed.");
            Check(scale,"actual-legacy-clock-cancels-tooltip-baseline",WaitTooltip(target,false,1000));
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
                    }
                    Check(scale,"actual-tooltip-test-main-window",main!=IntPtr.Zero);
                    ActualClockTooltip(scale,target,main);
                    tooltipTimerVisible=true;
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
                    tooltipTimerScope = "Private message-only native hit probe on original Button; fixed clock commands preserve native tooltip visibility. No physical hover or appearance certification.", ownedProcessClosed = cleanup });
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
                SnappingSettings(args[0]); Scale(1); Scale(2); Stacking(1); Stacking(2); ClockTooltipGate(1); ClockTooltipGate(2);
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
