using System;
using System.Diagnostics;
using System.IO;

// A controller may start support only for the VLC process it created.
static class SkinRuntime
{
    internal static bool StartHelper(Process vlc,string installed,string skin,int width,int height,string directory,Action<string> log)
    {
        if(directory==null) return false;
        if(!Path.IsPathRooted(directory)) throw new ArgumentException("Skin support directory must be absolute.");
        string helper=Path.Combine(Path.GetFullPath(directory),"SkinEffects.exe");
        if(!File.Exists(helper)) throw new FileNotFoundException("The separate NFS skin helper is missing.",helper);
        if(vlc==null || vlc.HasExited) throw new InvalidOperationException("Owned VLC is unavailable.");
        string arguments="--pid "+vlc.Id+" --skin \""+skin+"\" --video-size "+width+"x"+height+
            " --trusted-vlc-runtime \""+vlc.StartInfo.FileName+"\" --installed-vlc \""+installed+
            "\" --pid-start-ticks "+vlc.StartTime.ToUniversalTime().Ticks;
        using(var process=Process.Start(new ProcessStartInfo(helper,arguments) {UseShellExecute=false,CreateNoWindow=true})) {}
        log("SKIN_EFFECTS started_for_owned_vlc");
        return true;
    }
}

// The shared intro controller never launches a browser or owns playlist state.
sealed class SkinStartup
{
    readonly Process process;
    readonly int width,height;
    readonly bool controlled;
    readonly Action<string> log;
    readonly DateTime deadline=DateTime.UtcNow.AddSeconds(40);
    readonly Stopwatch animation=new Stopwatch();
    IntPtr main;
    bool wasTopmost,replayed,activated,complete;
    DateTime nextReplay=DateTime.MinValue,nextReturn=DateTime.MinValue;
    int returnPosts;
    internal SkinStartup(Process process,int width,int height,bool controlled,Action<string> log)
    {this.process=process;this.width=width;this.height=height;this.controlled=controlled;this.log=log;}
    internal bool Tick()
    {
        if(complete) return true;
        if(process.HasExited) throw new InvalidOperationException("Owned VLC exited during startup.");
        IntPtr window=Native.FindSizedWindow(process.Id,width,height);
        if(window==IntPtr.Zero)
        {
            if(DateTime.UtcNow>deadline) throw new TimeoutException("VLC main window did not appear within 40 seconds.");
            return false;
        }
        if(main==IntPtr.Zero)
        {
            main=window;wasTopmost=(Native.GetWindowLongPtr(main,-20).ToInt64()&8)!=0;
            Native.SetWindowPos(main,new IntPtr(-1),0,0,0,0,0x13);
        }
        if(controlled)
        {
            if(DateTime.UtcNow>deadline) throw new TimeoutException("Startup animation helper did not become ready within 40 seconds.");
            if(!Native.StartupReady(process.Id)) return false;
            IntPtr command=Native.FindStartupCommand(process.Id);
            if(command==IntPtr.Zero || Native.TargetHasCapture(command)) return false;
            if(!animation.IsRunning)
            {
                if(!replayed || !Native.StartupTriggered(process.Id) || !Native.IsWindowVisible(main))
                {
                    if(DateTime.UtcNow>=nextReplay)
                    {
                        if(!activated) {Native.SetForegroundWindow(main);activated=true;}
                        Native.InvokeSkinOpen(command,process.Id,1,1);
                        nextReplay=DateTime.UtcNow.AddMilliseconds(250);
                        if(!replayed) log("STARTUP replay_requested");
                        replayed=true;
                    }
                    return false;
                }
                animation.Start();
            }
            if(!Native.IsWindowVisible(main) || animation.ElapsedMilliseconds<8100 || DateTime.UtcNow<nextReturn) return false;
            Native.InvokeSkinOpen(command,process.Id,11,1);
            if(++returnPosts<2) {nextReturn=DateTime.UtcNow.AddMilliseconds(150);return false;}
            log("STARTUP full_sequence_complete");
        }
        complete=true;
        return true;
    }
    internal void Release(bool activate)
    {
        IntPtr window=main;main=IntPtr.Zero;
        if(!Native.OwnedBy(window,process.Id)) return;
        Native.SetWindowPos(window,new IntPtr(wasTopmost ? -1 : -2),0,0,0,0,0x13);
        if(activate) {Native.SetWindowPos(window,IntPtr.Zero,0,0,0,0,0x13);Native.SetForegroundWindow(window);}
    }
}
