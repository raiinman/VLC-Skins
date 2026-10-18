using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

// The Python owner creates a never-selected desktop and job before arming this fixture.
static class NfsStandaloneNativeTest
{
    [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr window,IntPtr dc,uint flags);
    [DllImport("user32.dll")] static extern bool IsIconic(IntPtr window);
    delegate bool EnumCallback(IntPtr window,IntPtr parameter);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumCallback callback,IntPtr parameter);
    [DllImport("user32.dll")] static extern IntPtr SendMessage(IntPtr window,uint message,IntPtr wParam,IntPtr lParam);
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr window,System.Text.StringBuilder value,int length);
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr window,System.Text.StringBuilder value,int length);
    static void Need(bool value,string message) {if(!value) throw new Exception(message);}
    static string Http(NfsSession session,string query)
    {return ((Task<string>)typeof(NfsSession).GetMethod("Get",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(session,new object[] {query})).GetAwaiter().GetResult();}
    static int Count(NfsSession session)
    {return (int)typeof(NfsSession).GetMethod("Count",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,new object[] {Http(session,"playlist.json")});}
    static IntPtr Dialog()
    {
        IntPtr found=IntPtr.Zero;int count=0;
        EnumWindows(delegate(IntPtr w,IntPtr p) {
            var name=new System.Text.StringBuilder(100);var title=new System.Text.StringBuilder(100);GetClassName(w,name,100);GetWindowText(w,title,100);
            if(Native.OwnedBy(w,Process.GetCurrentProcess().Id)&&name.ToString()=="#32770"&&title.ToString()=="Clear playlist") {found=w;count++;}return true;
        },IntPtr.Zero);return count==1 ? found : IntPtr.Zero;
    }
    static IntPtr Signal(int pid,int y,int width,int height)
    {
        IntPtr result=IntPtr.Zero;int count=0;
        EnumWindows(delegate(IntPtr w,IntPtr p) {Native.RECT bounds;if(Native.OwnedBy(w,pid)&&Native.GetWindowRect(w,out bounds)&&bounds.Left==-31000&&bounds.Top==y&&bounds.Right-bounds.Left==width&&bounds.Bottom-bounds.Top==height) {result=w;count++;}return true;},IntPtr.Zero);
        return count==1 ? result : IntPtr.Zero;
    }
    static string Frame(IntPtr main)
    {
        using(var bitmap=new Bitmap(300,298))
        {
            using(var graphics=Graphics.FromImage(bitmap)) {var dc=graphics.GetHdc();try {Need(PrintWindow(main,dc,0),"Native frame capture failed.");} finally {graphics.ReleaseHdc(dc);}}
            using(var crop=bitmap.Clone(new Rectangle(78,76,135,140),PixelFormat.Format32bppArgb)) using(var bytes=new MemoryStream())
            {crop.Save(bytes,ImageFormat.Png);using(var sha=System.Security.Cryptography.SHA256.Create()) return Convert.ToBase64String(sha.ComputeHash(bytes.ToArray()));}
        }
    }
    static void SilencePrivate(string skin)
    {
        using(var archive=ZipFile.Open(skin,ZipArchiveMode.Update)) foreach(var entry in archive.Entries)
        {
            if(!entry.FullName.EndsWith(".wav",StringComparison.OrdinalIgnoreCase)) continue;
            byte[] bytes;using(var stream=entry.Open()) {bytes=new byte[stream.Length];int at=0,n;while((n=stream.Read(bytes,at,bytes.Length-at))>0) at+=n;}
            int offset=12,bits=0;
            while(offset+8<=bytes.Length)
            {
                int size=BitConverter.ToInt32(bytes,offset+4),start=offset+8;Need(size>=0&&start+(long)size+(size%2)<=bytes.Length,"Bad WAV chunk.");
                string tag=System.Text.Encoding.ASCII.GetString(bytes,offset,4);
                if(tag=="fmt ") bits=BitConverter.ToInt16(bytes,start+14);
                if(tag=="data") {Need(bits==8||bits==16||bits==24||bits==32,"Bad WAV format.");for(int i=start;i<start+size;i++) bytes[i]=(byte)(bits==8 ? 128 : 0);}
                offset=start+size+(size%2);
            }
            using(var stream=entry.Open()) {stream.Position=0;stream.Write(bytes,0,bytes.Length);stream.SetLength(bytes.Length);}
        }
    }
    [STAThread] static int Main(string[] args)
    {
        try
        {
            var deadline=Stopwatch.StartNew();while(!File.Exists(args[3]+".ready")) {if(deadline.Elapsed.TotalSeconds>20) throw new Exception("Fixture job not armed.");Thread.Sleep(20);}
            Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
            Directory.CreateDirectory(args[1]);File.WriteAllText(Path.Combine(args[1],"NfsUnderground1x.vlcrc"),"[skins2]\nskins2-config=[\"main\" \"main_3_closed\" 42 61 300 298 1][\"video\" \"video_1\" 400 60 708 440 1]\n");
            var skin=NfsSkin.Prepare(args[0],args[1]);SilencePrivate(skin.Path);
            using(var stop=new EventWaitHandle(false,EventResetMode.AutoReset)) using(var session=new NfsSession(skin,args[1],args[2],stop))
            using(var timer=new System.Windows.Forms.Timer {Interval=20})
            {
                var field=typeof(NfsSession).GetField("vlc",BindingFlags.Instance|BindingFlags.NonPublic);var vlc=(Process)field.GetValue(session);
                var started=typeof(NfsSession).GetField("started",BindingFlags.Instance|BindingFlags.NonPublic);
                var elapsed=Stopwatch.StartNew();Stopwatch intro=null;string first=null;bool moving=false,finished=false;int stage=0;
                var clearing=typeof(NfsSession).GetField("clearing",BindingFlags.Instance|BindingFlags.NonPublic);
                timer.Tick+=delegate {
                    try
                    {
                        Need(elapsed.Elapsed.TotalSeconds<45,"Standalone startup timed out.");
                        if(intro==null&&Native.StartupTriggered(vlc.Id)) intro=Stopwatch.StartNew();
                        var main=Native.FindSizedWindow(vlc.Id,300,298);
                        if(intro!=null&&main!=IntPtr.Zero&&intro.ElapsedMilliseconds>=250&&first==null) first=Frame(main);
                        if(intro!=null&&intro.ElapsedMilliseconds>=2100&&!moving) moving=first!=Frame(main);
                        if(stage==0&&(bool)started.GetValue(session)&&Native.PlaylistClearCapability(vlc.Id)==true)
                        {
                            Need(intro!=null&&intro.ElapsedMilliseconds>=8050&&moving,"Full moving intro was not completed.");
                            Need((Native.GetWindowLongPtr(main,-20).ToInt64()&8)==0,"Startup topmost was not restored.");
                            Need(Signal(vlc.Id,-29700,202,1)!=IntPtr.Zero||Signal(vlc.Id,-29700,203,1)!=IntPtr.Zero,"Snapping availability was not initialized.");
                            Need(Signal(vlc.Id,-30900,133,17)!=IntPtr.Zero,"Framed hover command missing.");
                            Need(Native.FindSizedWindow(vlc.Id,708,440)!=IntPtr.Zero,"Native framed video pane missing.");
                            Native.ShowWindow(main,6);Need(IsIconic(main),"Private main did not minimize.");
                            session.ShowPlayer();Need(!IsIconic(main)&&Native.IsWindowVisible(main),"Show player did not restore cached minimized main.");
                            string media=Path.Combine(args[1],"fixture-only.wav");File.WriteAllBytes(media,new byte[44]);string input=Uri.EscapeDataString(new Uri(media).AbsoluteUri);
                            Http(session,"status.json?command=in_enqueue&input="+input);Http(session,"status.json?command=in_enqueue&input="+input);
                            Need(Count(session)==2,"Private queue rows not added.");stage=1;session.ClearPlaylist();
                        }
                        else if(stage==1||stage==3)
                        {
                            var dialog=Dialog();if(dialog==IntPtr.Zero) return;
                            Need((SendMessage(dialog,0x400,IntPtr.Zero,IntPtr.Zero).ToInt64()&0xffff)==7,"Clear confirmation did not default to No.");
                            SendMessage(dialog,0x111,new IntPtr(stage==1 ? 7 : 6),IntPtr.Zero);stage++;
                        }
                        else if(stage==2&&!(bool)clearing.GetValue(session)) {Need(Count(session)==2,"No confirmation changed private rows.");stage=3;session.ClearPlaylist();}
                        else if(stage==4&&!(bool)clearing.GetValue(session))
                        {
                            Need(Count(session)==0,"Yes confirmation did not clear the private queue.");
                            finished=true;timer.Stop();stop.Set();
                            File.WriteAllText(args[3],"PASS: standalone controller; moving full intro; topmost restored; Show player restores cached minimized main; clear defaults No/preserves 2 private rows then Yes empties only owned queue; snapping initialized; framed video/hover channel present; private PCM silent fixture only.");
                        }
                    }
                    catch(Exception error) {timer.Stop();File.WriteAllText(args[3],error.ToString());stop.Set();}
                };
                timer.Start();Application.Run(session);Need(finished,"Standalone native checks failed.");
                string log=File.ReadAllText(Path.Combine(args[1],"nfs-player.log"));
                Need(log.Contains("CLOSE graceful_owned_process")&&!log.Contains("forced_owned_process"),"Owned VLC did not shut down gracefully.");
                string saved=File.ReadAllText(skin.ConfigPath);
                Need(saved.Contains("[\"main\" \"main_3_closed\" 42 61 300 298 1]"),"Private stable main choice/geometry was not flushed.");
            }
            return 0;
        }
        catch(Exception error) {File.WriteAllText(args[3],error.ToString());return 1;}
    }
}
