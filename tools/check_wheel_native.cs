// Synthetic, cross-process queued-message proof on an owner-created private desktop.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
internal static class WheelNativeFixture
{
    [StructLayout(LayoutKind.Sequential)] struct Point { public int x,y; }
    [StructLayout(LayoutKind.Sequential)] struct Msg { public IntPtr hwnd; public uint message; public UIntPtr wParam; public IntPtr lParam; public uint time; public Point pt; public uint extra; }
    [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct Wc { public uint style; public IntPtr proc; public int clsExtra,wndExtra; public IntPtr instance,icon,cursor,brush; public string menu,name; }
    delegate IntPtr WndProc(IntPtr h,uint m,IntPtr w,IntPtr l);
    static WndProc procedure=WindowProc;
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern ushort RegisterClassW(ref Wc c);
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern IntPtr CreateWindowExW(uint ex,string cls,string title,uint style,int x,int y,int w,int h,IntPtr parent,IntPtr menu,IntPtr instance,IntPtr param);
    [DllImport("user32.dll")] static extern IntPtr DefWindowProcW(IntPtr h,uint m,IntPtr w,IntPtr l);
    [DllImport("user32.dll")] static extern bool GetMessageW(out Msg m,IntPtr h,uint min,uint max);
    [DllImport("user32.dll")] static extern IntPtr DispatchMessageW(ref Msg m);
    [DllImport("user32.dll")] static extern bool DestroyWindow(IntPtr h);
    [DllImport("user32.dll")] static extern void PostQuitMessage(int code);
    [DllImport("user32.dll")] static extern bool PostMessageW(IntPtr h,uint m,IntPtr w,IntPtr l);
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern bool SetPropW(IntPtr h,string name,IntPtr value);
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern IntPtr GetPropW(IntPtr h,string name);
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern IntPtr RemovePropW(IntPtr h,string name);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h,out uint pid);
    [DllImport("user32.dll")] static extern IntPtr GetThreadDesktop(uint t);
    [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern bool GetUserObjectInformationW(IntPtr h,int index,StringBuilder text,int size,out int needed);
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] static extern IntPtr LoadLibraryW(string path);
    [DllImport("kernel32.dll",CharSet=CharSet.Ansi)] static extern IntPtr GetProcAddress(IntPtr h,string name);
    [DllImport("kernel32.dll")] static extern bool FreeLibrary(IntPtr h);
    [DllImport("user32.dll")] static extern IntPtr SetWindowsHookExW(int id,IntPtr callback,IntPtr dll,uint thread);
    [DllImport("user32.dll")] static extern bool UnhookWindowsHookEx(IntPtr hook);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h,int cmd);
    [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h,IntPtr after,int x,int y,int w,int height,uint flags);
    [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] static extern IntPtr SetCapture(IntPtr window);
    [DllImport("user32.dll")] static extern IntPtr GetCapture();
    [DllImport("user32.dll")] static extern bool ReleaseCapture();
    static void Need(bool ok,string why) { if(!ok)throw new InvalidOperationException(why); }
    static string Desktop(uint thread) { var text=new StringBuilder(256);int n;Need(GetUserObjectInformationW(GetThreadDesktop(thread),2,text,512,out n),"Desktop read failed");return text.ToString(); }
    static IntPtr Pack(int x,int y) { return new IntPtr(((long)(ushort)y<<16)|(ushort)x); }
    static IntPtr WindowProc(IntPtr h,uint m,IntPtr w,IntPtr l)
    {
        if(m>=0x8001&&m<=0x8003) {
            if(m==0x8001)SetCapture(h);else if(m==0x8002)ReleaseCapture();
            SetPropW(h,"CaptureReadback",GetCapture());SetPropW(h,"CaptureAck",new IntPtr(GetPropW(h,"CaptureAck").ToInt64()+1));return IntPtr.Zero;
        }
        if(m==0x203) { ReleaseCapture();SetPropW(h,"DoubleClicks",new IntPtr(GetPropW(h,"DoubleClicks").ToInt64()+1));return IntPtr.Zero; }
        if(m==0) { SetPropW(h,"NullMessages",new IntPtr(GetPropW(h,"NullMessages").ToInt64()+1));return IntPtr.Zero; }
        if(m==0x20A||m==0x200||m==0x20E) { SetPropW(h,"ObservedLP",l);SetPropW(h,"ObservedWP",w);SetPropW(h,"ObservedMessage",new IntPtr(m));SetPropW(h,"ObservedCount",new IntPtr(GetPropW(h,"ObservedCount").ToInt64()+1));return IntPtr.Zero; }
        if(m==0x10) { DestroyWindow(h);return IntPtr.Zero; }
        if(m==2) { PostQuitMessage(0);return IntPtr.Zero; }
        return DefWindowProcW(h,m,w,l);
    }
    static int Child(string ready)
    {
        var c=new Wc { proc=Marshal.GetFunctionPointerForDelegate(procedure), name="SkinWindowClass" };
        Need(RegisterClassW(ref c)!=0,"Register fixture class failed");
        IntPtr window=CreateWindowExW(0x08000080,c.name,"Private wheel fixture",0x90000000,100,100,361,64,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero);
        Need(window!=IntPtr.Zero,"Create fixture window failed");
        IntPtr clock=CreateWindowExW(0x08000080,c.name,"Private clock fixture",0x90000000,-31000,-30200,151,17,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero);
        Need(clock!=IntPtr.Zero&&SetPropW(window,"ClockWindow",clock),"Create private clock failed");
        IntPtr clear=CreateWindowExW(0x08000080,c.name,"Private playlist command fixture",0x90000000,-31000,-30100,161,17,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero);
        Need(clear!=IntPtr.Zero&&SetPropW(window,"ClearWindow",clear),"Create private playlist command failed");
        var otherClass=new Wc { proc=Marshal.GetFunctionPointerForDelegate(procedure),name="NfsNonSkinFixture" };
        Need(RegisterClassW(ref otherClass)!=0,"Register negative fixture class failed");
        IntPtr other=CreateWindowExW(0x08000080,otherClass.name,"Private negative command fixture",0x90000000,-31000,-30100,161,17,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero);
        Need(other!=IntPtr.Zero&&SetPropW(window,"OtherCommandWindow",other),"Create negative command failed");
        File.WriteAllText(ready,window.ToInt64().ToString());
        Msg m;while(GetMessageW(out m,IntPtr.Zero,0,0))DispatchMessageW(ref m);return 0;
    }
    static int Main(string[] args)
    {
        Need(Desktop(GetCurrentThreadId()).StartsWith("NfsLoad_",StringComparison.Ordinal),"Private desktop required");SetProcessDPIAware();
        if(args.Length==2&&args[0]=="--child")return Child(args[1]);
        if(args.Length!=2)return 2;
        string output=args[1],ready=output+".child",error=null;Process child=null;IntPtr hook=IntPtr.Zero,dll=IntPtr.Zero,window=IntPtr.Zero;
        var cases=new List<object>();bool cleaned=false;
        try
        {
            var permit=Stopwatch.StartNew();while(!File.Exists(output+".ready")&&permit.ElapsedMilliseconds<10000)Thread.Sleep(20);
            Need(File.Exists(output+".ready"),"Owner job not armed");
            child=Process.Start(new ProcessStartInfo(Process.GetCurrentProcess().MainModule.FileName,"--child \""+ready+"\"") { UseShellExecute=false,CreateNoWindow=true });
            var wait=Stopwatch.StartNew();while(!File.Exists(ready)&&wait.ElapsedMilliseconds<10000&&!child.HasExited)Thread.Sleep(20);
            Need(File.Exists(ready),"Child window unavailable");window=new IntPtr(long.Parse(File.ReadAllText(ready)));
            uint pid;uint thread=GetWindowThreadProcessId(window,out pid);Need(pid==(uint)child.Id&&thread!=0&&Desktop(thread)==Desktop(GetCurrentThreadId()),"Child ownership mismatch");
            IntPtr clock=GetPropW(window,"ClockWindow");uint clockPid;
            Need(clock!=IntPtr.Zero&&GetWindowThreadProcessId(clock,out clockPid)==thread&&clockPid==pid,"Clock ownership mismatch");
            IntPtr clear=GetPropW(window,"ClearWindow"),otherCommand=GetPropW(window,"OtherCommandWindow");
            Need(clear!=IntPtr.Zero&&GetWindowThreadProcessId(clear,out clockPid)==thread&&clockPid==pid,"Playlist command ownership mismatch");
            Need(otherCommand!=IntPtr.Zero&&GetWindowThreadProcessId(otherCommand,out clockPid)==thread&&clockPid==pid,"Negative command ownership mismatch");
            Action<uint> capture=message=> {
                long prior=GetPropW(window,"CaptureAck").ToInt64();Need(PostMessageW(window,message,IntPtr.Zero,IntPtr.Zero),"Capture fixture message failed");
                var timer=Stopwatch.StartNew();while(GetPropW(window,"CaptureAck").ToInt64()==prior&&timer.ElapsedMilliseconds<3000)Thread.Sleep(10);
                Need(GetPropW(window,"CaptureAck").ToInt64()==prior+1,"Capture acknowledgment missing");
            };
            Action<string,bool> check=(name,ok)=> { cases.Add(new{name=name,passed=ok});Need(ok,name); };
            capture(0x8001);check("before-hook-private-capture-established",GetPropW(window,"CaptureReadback")==window);
            long oldClicks=GetPropW(clock,"DoubleClicks").ToInt64();
            Need(PostMessageW(clock,0x203,new IntPtr(1),Pack(2,2)),"Baseline clock post failed");capture(0x8003);
            check("before-hook-clock-delivers-and-drops-capture",GetPropW(clock,"DoubleClicks").ToInt64()==oldClicks+1&&GetPropW(window,"CaptureReadback")==IntPtr.Zero);
            Action<string,uint,IntPtr,IntPtr,IntPtr> test=(name,message,wp,lp,expected)=> {
                Need(!child.HasExited&&GetWindowThreadProcessId(window,out pid)==thread&&pid==(uint)child.Id,"Lost owned window");
                long prior=GetPropW(window,"ObservedCount").ToInt64();Need(PostMessageW(window,message,wp,lp),"Synthetic queued message failed");
                var timer=Stopwatch.StartNew();while(GetPropW(window,"ObservedCount").ToInt64()==prior&&timer.ElapsedMilliseconds<3000)Thread.Sleep(10);
                bool ok=GetPropW(window,"ObservedCount").ToInt64()==prior+1&&GetPropW(window,"ObservedLP")==expected&&GetPropW(window,"ObservedWP")==wp&&GetPropW(window,"ObservedMessage").ToInt64()==message;
                cases.Add(new{name=name,passed=ok,expected=expected.ToInt64(),actual=GetPropW(window,"ObservedLP").ToInt64()});Need(ok,name);
            };
            IntPtr wheel=new IntPtr((120<<16)|4),volume=Pack(380,143),seek=Pack(180,112);
            test("before-hook-volume-screen-point",0x20A,wheel,volume,volume);
            dll=LoadLibraryW(Path.GetFullPath(args[0]));Need(dll!=IntPtr.Zero,"DLL load failed");IntPtr callback=GetProcAddress(dll,"CorrectWheel");Need(callback!=IntPtr.Zero,"Export missing");
            Need(SetPropW(window,"NfsSkinWheelBridge.OwnerPid",new IntPtr(child.Id))&&SetPropW(window,"NfsSkinWheelBridge.OriginX",new IntPtr(-31000))&&SetPropW(window,"NfsSkinWheelBridge.OriginY",new IntPtr(-30800))&&SetPropW(window,"NfsSkinWheelBridge.Enabled",new IntPtr(0x4E465357)),"Properties failed");
            hook=SetWindowsHookExW(3,callback,dll,thread);Need(hook!=IntPtr.Zero,"Thread hook failed");
            test("volume-local280x43",0x20A,wheel,volume,Pack(-30720,-30757));
            test("seek-local80x12",0x20A,wheel,seek,Pack(-30920,-30788));
            test("negative-wheel-delta-preserved",0x20A,new IntPtr(unchecked((int)0xFF880008)),volume,Pack(-30720,-30757));
            test("ordinary-motion-untouched",0x200,IntPtr.Zero,volume,volume);
            test("horizontal-wheel-untouched",0x20E,wheel,volume,volume);
            IntPtr outside=Pack(99,143);test("outside-point-untouched",0x20A,wheel,outside,outside);
            SetPropW(window,"NfsSkinWheelBridge.OwnerPid",new IntPtr(child.Id+1));test("wrong-pid-untouched",0x20A,wheel,volume,volume);SetPropW(window,"NfsSkinWheelBridge.OwnerPid",new IntPtr(child.Id));
            SetPropW(window,"NfsSkinWheelBridge.OriginX",new IntPtr(-1));test("wrong-origin-untouched",0x20A,wheel,volume,volume);SetPropW(window,"NfsSkinWheelBridge.OriginX",new IntPtr(-31000));
            ShowWindow(window,0);test("hidden-untouched",0x20A,wheel,volume,volume);ShowWindow(window,4);
            SetWindowPos(window,IntPtr.Zero,0,0,362,1,0x16);test("closed-size-untouched",0x20A,wheel,volume,volume);SetWindowPos(window,IntPtr.Zero,0,0,361,64,0x16);
            RemovePropW(window,"NfsSkinWheelBridge.Enabled");test("disabled-untouched",0x20A,wheel,volume,volume);
            capture(0x8001);check("private-GUI-thread-capture-established",GetPropW(window,"CaptureReadback")==window);
            long clicks=GetPropW(clock,"DoubleClicks").ToInt64(),nulls=GetPropW(clock,"NullMessages").ToInt64();
            Need(PostMessageW(clock,0x203,new IntPtr(1),Pack(2,2)),"Clock fixture post failed");
            capture(0x8003);
            check("clock-during-capture-becomes-WM_NULL",GetPropW(clock,"DoubleClicks").ToInt64()==clicks&&GetPropW(clock,"NullMessages").ToInt64()==nulls+1);
            check("clock-command-preserves-private-capture",GetPropW(window,"CaptureReadback")==window);
            capture(0x8002);check("private-capture-released",GetPropW(window,"CaptureReadback")==IntPtr.Zero);
            Need(PostMessageW(clock,0x203,new IntPtr(1),Pack(2,2)),"Clock fixture post failed");capture(0x8003);
            check("clock-after-release-delivers",GetPropW(clock,"DoubleClicks").ToInt64()==clicks+1);
            capture(0x8001);long ordinary=GetPropW(window,"DoubleClicks").ToInt64();
            Need(PostMessageW(window,0x203,new IntPtr(1),Pack(20,20)),"Ordinary fixture post failed");capture(0x8003);
            check("ordinary-double-click-delivers-during-capture",GetPropW(window,"DoubleClicks").ToInt64()==ordinary+1&&GetPropW(window,"CaptureReadback")==IntPtr.Zero);
            Action<string,IntPtr,int,int,bool> clearTest=(name,command,x,y,suppressed)=> {
                capture(0x8001);
                long priorClicks=GetPropW(command,"DoubleClicks").ToInt64(),priorNulls=GetPropW(command,"NullMessages").ToInt64();
                Need(PostMessageW(command,0x203,new IntPtr(1),Pack(x,y)),"Playlist command fixture post failed");capture(0x8003);
                check(name,GetPropW(command,"DoubleClicks").ToInt64()==priorClicks+(suppressed?0:1)&&
                    GetPropW(command,"NullMessages").ToInt64()==priorNulls+(suppressed?1:0)&&
                    GetPropW(window,"CaptureReadback")== (suppressed?window:IntPtr.Zero));
            };
            foreach(int width in new[]{161,162}) {
                Need(SetWindowPos(clear,IntPtr.Zero,-31000,-30100,width,17,0x14),"Playlist fixture geometry failed");
                foreach(int cell in new[]{0,10,20})clearTest("playlist-"+width+"-cell"+cell+"-suppressed-while-captured",clear,cell,0,true);
            }
            clearTest("playlist-noncell-x-delivers",clear,1,0,false);
            clearTest("playlist-noncell-y-delivers",clear,10,1,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-30100,160,17,0x14);
            clearTest("playlist-wrong-width-delivers",clear,0,0,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-30101,161,17,0x14);
            clearTest("playlist-wrong-position-delivers",clear,0,0,false);
            clearTest("playlist-wrong-class-delivers",otherCommand,0,0,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-30100,161,17,0x14);
            capture(0x8002);long delivered=GetPropW(clear,"DoubleClicks").ToInt64();
            Need(PostMessageW(clear,0x203,new IntPtr(1),Pack(0,0)),"Released playlist command post failed");capture(0x8003);
            check("playlist-command-after-capture-release-delivers",GetPropW(clear,"DoubleClicks").ToInt64()==delivered+1);
            Need(SetWindowPos(clear,IntPtr.Zero,-31000,-29900,181,17,0x14),"Fixed clock fixture geometry failed");
            foreach(int cell in new[]{0,10})clearTest("fixed-clock-cell"+cell+"-suppressed-while-captured",clear,cell,0,true);
            clearTest("fixed-clock-noncell-x-delivers",clear,1,0,false);
            clearTest("fixed-clock-noncell-y-delivers",clear,10,1,false);
            clearTest("fixed-clock-playlist-only-cell-delivers",clear,20,0,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-29900,180,17,0x14);
            clearTest("fixed-clock-wrong-width-delivers",clear,0,0,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-29901,181,17,0x14);
            clearTest("fixed-clock-wrong-position-delivers",clear,0,0,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-29900,181,17,0x14);
            capture(0x8002);delivered=GetPropW(clear,"DoubleClicks").ToInt64();
            Need(PostMessageW(clear,0x203,new IntPtr(1),Pack(10,0)),"Released fixed clock command post failed");capture(0x8003);
            check("fixed-clock-command-after-capture-release-delivers",GetPropW(clear,"DoubleClicks").ToInt64()==delivered+1);
            foreach(int width in new[]{191,192}) {
                Need(SetWindowPos(clear,IntPtr.Zero,-31000,-29800,width,17,0x14),"Snapping fixture geometry failed");
                foreach(int cell in new[]{0,10,20,30})clearTest("snapping-"+width+"-cell"+cell+"-suppressed-while-captured",clear,cell,0,true);
            }
            clearTest("snapping-noncell-x-delivers",clear,1,0,false);
            clearTest("snapping-noncell-y-delivers",clear,10,1,false);
            clearTest("snapping-noncell40-delivers",clear,40,0,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-29800,190,17,0x14);
            clearTest("snapping-wrong-width-delivers",clear,0,0,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-29801,191,17,0x14);
            clearTest("snapping-wrong-position-delivers",clear,0,0,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-29800,191,17,0x14);
            capture(0x8002);delivered=GetPropW(clear,"DoubleClicks").ToInt64();
            Need(PostMessageW(clear,0x203,new IntPtr(1),Pack(30,0)),"Released snapping command post failed");capture(0x8003);
            check("snapping-command-after-capture-release-delivers",GetPropW(clear,"DoubleClicks").ToInt64()==delivered+1);
            Need(SetWindowPos(clear,IntPtr.Zero,-31000,-29600,231,17,0x14),"Startup fixture geometry failed");
            foreach(int cell in new[]{0,1,2,10,11,12})clearTest("startup-cell"+cell+"-suppressed-while-captured",clear,cell,1,true);
            clearTest("startup-noncell-x-delivers",clear,3,1,false);
            clearTest("startup-noncell-y-delivers",clear,1,3,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-29600,230,17,0x14);
            clearTest("startup-wrong-width-delivers",clear,1,1,false);
            SetWindowPos(clear,IntPtr.Zero,-31000,-29601,231,17,0x14);
            clearTest("startup-wrong-position-delivers",clear,1,1,false);
            Need(UnhookWindowsHookEx(hook),"Unhook failed");hook=IntPtr.Zero;test("after-unhook-untouched",0x20A,wheel,volume,volume);
        }
        catch(Exception ex) { error=ex.GetType().Name+": "+ex.Message; }
        finally
        {
            if(window!=IntPtr.Zero)RemovePropW(window,"NfsSkinWheelBridge.Enabled");
            if(hook!=IntPtr.Zero)UnhookWindowsHookEx(hook);
            if(child!=null) { if(!child.HasExited)child.Kill();cleaned=child.WaitForExit(5000);child.Dispose(); }
            if(dll!=IntPtr.Zero)FreeLibrary(dll);
        }
        File.WriteAllText(output,new JavaScriptSerializer().Serialize(new { passed=error==null&&cleaned,error=error,cases=cases,ownedChildClosed=cleaned,
            scope="Cross-process queued-message wheel correction and clock/playlist-command capture protection on synthetic private SkinWindowClass. Not actual VLC controls or physical input delivery.",physicalInputUsed=false }));
        return error==null&&cleaned?0:1;
    }
}
