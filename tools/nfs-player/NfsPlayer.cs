using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;

// Independent skin session controller. No browser, resolver or YouTube dependency.
static class NfsPlayer
{
    [STAThread]
    static int Main(string[] arguments)
    {
        bool noninteractive=Array.IndexOf(arguments,"--prepare-only")>=0||Array.IndexOf(arguments,"--self-test")>=0||Array.IndexOf(arguments,"--stop-owned-session")>=0;
        try
        {
            ValidateBundle(AppDomain.CurrentDomain.BaseDirectory);
            string data=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"NfsUnderground1x"),skin=null,support=AppDomain.CurrentDomain.BaseDirectory;bool stop=false,prepareOnly=false;
            foreach(string argument in arguments)
            {
                if(argument.StartsWith("--skin=")) skin=Absolute(argument.Substring(7));
                else if(argument.StartsWith("--data-directory=")) data=Absolute(argument.Substring(17));
                else if(argument.StartsWith("--support-directory=")) support=Absolute(argument.Substring(20));
                else if(argument=="--stop-owned-session") stop=true;
                else if(argument=="--prepare-only") prepareOnly=true;
                else if(argument=="--self-test") {SelfTest();return 0;}
                else throw new ArgumentException("Unknown NFS Player argument.");
            }
            string suffix=Scope(data),name="Local\\NfsUnderground1x"+suffix;
            if(stop) {if(prepareOnly||skin!=null) throw new ArgumentException("Stop cannot be combined with preparation.");try {using(var request=EventWaitHandle.OpenExisting(name+"Stop")) request.Set();return 0;} catch(WaitHandleCannotBeOpenedException) {return 2;}}
            bool created;
            using(var mutex=new Mutex(true,name,out created))
            {
                if(!created) return 0;
                using(var request=new EventWaitHandle(false,EventResetMode.AutoReset,name+"Stop"))
                {
                    Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
                    string bundled=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"Need-for-Speed-Underground-1x.vlt");
                    if(skin==null && File.Exists(bundled)) skin=bundled;
                    if(skin==null)
                    {
                        string remembered=Path.Combine(data,"source-skin.txt");
                        if(File.Exists(remembered)) skin=Absolute(File.ReadAllText(remembered).Trim());
                        else using(var dialog=new OpenFileDialog {Title="Choose Need for Speed Underground 1x skin",Filter="VLC skin (*.vlt)|*.vlt",CheckFileExists=true})
                        {if(dialog.ShowDialog()!=DialogResult.OK) return 1;skin=dialog.FileName;}
                    }
                    // Validation precedes persisting the chosen input.
                    var prepared=NfsSkin.Prepare(skin,data);
                    File.WriteAllText(Path.Combine(data,"source-skin.txt"),skin,new UTF8Encoding(false));
                    if(prepareOnly) return 0;
                    using(var context=new NfsSession(prepared,data,support,request)) Application.Run(context);
                }
                mutex.ReleaseMutex();
            }
            return 0;
        }
        catch(Exception error) {if(noninteractive) Console.Error.WriteLine(error.Message);else MessageBox.Show(error.Message,"NFS Underground VLC",MessageBoxButtons.OK,MessageBoxIcon.Error);return 1;}
    }
    static string Absolute(string path) {if(!Path.IsPathRooted(path)) throw new ArgumentException("Paths must be absolute.");return Path.GetFullPath(path);}
    static string Scope(string path)
    {using(var sha=SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(Path.GetFullPath(path).TrimEnd(Path.DirectorySeparatorChar).ToUpperInvariant()))).Replace("-","").Substring(0,24);}
    internal static void SelfTest()
    {
        if(Scope(Path.Combine(Path.GetTempPath(),"nfs-a"))!=Scope(Path.Combine(Path.GetTempPath(),"nfs-a","."))) throw new Exception("Data scope normalization failed.");
        if(Scope(Path.Combine(Path.GetTempPath(),"nfs-a"))==Scope(Path.Combine(Path.GetTempPath(),"nfs-b"))) throw new Exception("Data scope separation failed.");
        var signal=new PlaylistClearCommands();
        if(signal.Observe(162,true,true)) throw new Exception("Unarmed clear accepted.");
        signal.Observe(161,true,true);if(!signal.Observe(162,true,true)||signal.Observe(162,true,true)) throw new Exception("Clear consumption failed.");
    }
    internal static void ValidateBundle(string directory)
    {
        string root=Path.GetFullPath(directory).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar,manifest=Path.Combine(root,"bundle.json");
        if(!File.Exists(manifest)) return; // Explicit developer source builds have no release manifest.
        var info=new FileInfo(manifest);if(info.Length>1024*1024||(info.Attributes&FileAttributes.ReparsePoint)!=0) throw new IOException("Invalid NFS package manifest.");
        var value=new JavaScriptSerializer().DeserializeObject(File.ReadAllText(manifest)) as Dictionary<string,object>;object schema,product,files,accepted;
        if(value==null||!value.TryGetValue("schemaVersion",out schema)||!(schema is int)||(int)schema!=1||!value.TryGetValue("product",out product)||Convert.ToString(product)!="nfs-skin-helper"||!value.TryGetValue("files",out files)||!value.TryGetValue("acceptedSkinSha256",out accepted)) throw new IOException("Incompatible NFS package manifest.");
        var hashes=accepted as object[];var map=files as Dictionary<string,object>;
        if(hashes==null||hashes.Length<1||hashes.Length>2||map==null||map.Count<1||map.Count>128) throw new IOException("Invalid NFS package bounds.");
        var distinct=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach(var item in hashes) {string hash=item as string;if(hash==null||(hash!=NfsSkin.CanonicalHash&&hash!=NfsSkin.ReleaseHash)||!distinct.Add(hash)) throw new IOException("Unsupported NFS skin hash.");}
        distinct.Clear();
        foreach(var pair in map)
        {
            string relative=pair.Key.Replace('/',Path.DirectorySeparatorChar);string hash=pair.Value as string;
            if(Path.IsPathRooted(relative)||relative.IndexOf(':')>=0||!distinct.Add(relative)||hash==null||!System.Text.RegularExpressions.Regex.IsMatch(hash,"^[0-9a-f]{64}$")) throw new IOException("Invalid NFS package file entry.");
            string current=root;
            foreach(string part in relative.Split(Path.DirectorySeparatorChar))
            {
                if(part.Length==0||part=="."||part=="..") throw new IOException("Invalid NFS package path.");
                current=Path.Combine(current,part);
                if((File.Exists(current)||Directory.Exists(current))&&(File.GetAttributes(current)&FileAttributes.ReparsePoint)!=0) throw new IOException("NFS package links are unsupported.");
            }
            if(!File.Exists(current)||VlcIsolation.Hash(current)!=hash) throw new IOException("NFS package integrity check failed.");
        }
    }
}

sealed class NfsSession : ApplicationContext
{
    readonly Process vlc;
    readonly string data,password;
    readonly int port;
    readonly EventWaitHandle stop;
    readonly System.Windows.Forms.Timer timer=new System.Windows.Forms.Timer {Interval=100};
    readonly NotifyIcon tray;
    readonly PlaylistClearCommands clearSignal=new PlaylistClearCommands();
    readonly SemaphoreSlim control=new SemaphoreSlim(1,1);
    readonly SkinStartup startup;
    IntPtr signal,main;
    bool clearing,closing,started;
    internal NfsSession(NfsSkin.Prepared skin,string directory,string support,EventWaitHandle request)
    {
        data=directory;stop=request;
        string installed=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),"VideoLAN","VLC","vlc.exe");
        if(!File.Exists(installed)) throw new IOException("Install 64-bit VLC before opening NFS Player.");
        // Refuse partial helper bundles instead of silently dropping skin features.
        foreach(string required in new [] {"SkinEffects.exe","NfsWheelBridge64.dll","nfs_volume_osd_v1.lua"})
            if(!File.Exists(Path.Combine(support,required))) throw new IOException("Missing skin support file: "+required);
        port=FreePort();password=Guid.NewGuid().ToString("N");
        string http=NativeHttp.PrepareBase(Path.GetDirectoryName(installed),data),lua=Path.Combine(support,"nfs_volume_osd_v1.lua");
        string args="--no-one-instance --no-one-instance-when-started-from-file --no-qt-privacy-ask --config=\""+skin.ConfigPath+"\" --intf skins2 --embedded-video --skinned-video --extraintf=http:luaintf --osd --lua-intf=nfs_volume_osd_v1 --http-src=\""+http+"\" --http-host=127.0.0.1 --http-port="+port+" --http-password="+password+" --stats";
        vlc=Process.Start(VlcIsolation.StartInfo(installed,data,args,lua));
        try
        {
            if(!SkinRuntime.StartHelper(vlc,installed,skin.Path,skin.VideoWidth,skin.VideoHeight,support,Log)) throw new IOException("Skin support could not start.");
            startup=new SkinStartup(vlc,300,298,skin.ControlledStartup,Log);
            var menu=new ContextMenuStrip();menu.Items.Add("Show player",null,delegate {ShowPlayer();});
            menu.Items.Add("Clear playlist...",null,delegate {ClearPlaylist();});menu.Items.Add("Exit",null,delegate {CloseOwned();});
            tray=new NotifyIcon {Icon=System.Drawing.SystemIcons.Application,Text="NFS Underground VLC",ContextMenuStrip=menu,Visible=true};
            timer.Tick+=Tick;timer.Start();Log("START owned_skin_session");
        }
        catch {if(!vlc.HasExited) {vlc.Kill();vlc.WaitForExit(5000);}throw;}
    }
    void Log(string message) {File.AppendAllText(Path.Combine(data,"nfs-player.log"),DateTime.UtcNow.ToString("o")+" "+message+Environment.NewLine);}
    internal void ShowPlayer()
    {
        if(closing||vlc.HasExited||main==IntPtr.Zero||!Native.IsWindow(main)||!Native.OwnedBy(main,vlc.Id)) return;
        Native.ShowWindow(main,9);Native.SetForegroundWindow(main);
    }
    void Tick(object sender,EventArgs args)
    {
        try
        {
            if(vlc.HasExited || stop.WaitOne(0)) {CloseOwned();return;}
            if(!started) {if(!startup.Tick()) return;main=Native.FindSizedWindow(vlc.Id,300,298);startup.Release(false);started=true;Log("STARTUP_COMPLETE");}
            int width;IntPtr found=Native.FindPlaylistClearSignal(vlc.Id,out width);
            if(found!=signal) {clearSignal.Observe(0,false,false);signal=found;}
            if(found==IntPtr.Zero) {clearSignal.Observe(0,false,false);return;}
            if(Native.TargetHasCapture(found)) return;
            bool available=!clearing&&!closing;
            bool requested=clearSignal.Observe(width,true,available);
            if(width!=161) Native.InvokeSkinOpen(found,vlc.Id,0,0);
            if(Native.PlaylistClearCapability(vlc.Id)!=available) Native.InvokeSkinOpen(found,vlc.Id,available ? 10 : 20,0);
            if(requested) ClearPlaylist();
        }
        catch(Exception error) {Log("ERROR "+error.GetType().Name);CloseOwned();}
    }
    internal async void ClearPlaylist()
    {
        if(clearing||closing||!started) return;
        clearing=true;
        try
        {
            await control.WaitAsync();
            try
            {
                int count=Count(await Get("playlist.json"));
                if(closing||vlc.HasExited||count==0) return;
                IntPtr main=Native.FindSizedWindow(vlc.Id,300,298),owner=Native.PlaylistDialogWindow(vlc.Id,main);
                if(owner==IntPtr.Zero||!Native.OwnedBy(owner,vlc.Id)) return;
                if(MessageBox.Show(new WindowOwner(owner),"Clear all "+count+" playlist items?","Clear playlist",MessageBoxButtons.YesNo,MessageBoxIcon.Question,MessageBoxDefaultButton.Button2)!=DialogResult.Yes) return;
                if(closing||vlc.HasExited) return;
                await Get("status.json?command=pl_empty");
                if(Count(await Get("playlist.json"))!=0) throw new IOException("VLC did not confirm an empty playlist.");
                Log("CLEAR confirmed_empty");
            }
            finally {control.Release();}
        }
        catch(Exception error) {if(!closing) MessageBox.Show(error.Message,"NFS Underground VLC");}
        finally {clearing=false;}
    }
    static int Count(string json)
    {return CountNode(new JavaScriptSerializer {MaxJsonLength=4*1024*1024}.DeserializeObject(json),0);}
    static int CountNode(object node,int depth)
    {
        if(depth>32) throw new IOException("Playlist nesting exceeds the supported limit.");
        var item=node as Dictionary<string,object>;if(item==null) return 0;
        object type,children;int count=0;
        if(item.TryGetValue("type",out type)&&Convert.ToString(type)=="leaf") return 1;
        if(item.TryGetValue("children",out children)) foreach(var child in children as IEnumerable??new object[0]) {count+=CountNode(child,depth+1);if(count>20000) throw new IOException("Playlist exceeds the supported limit.");}
        return count;
    }
    Task<string> Get(string request)
    {
        return Task.Run(delegate {
            if(vlc.HasExited) throw new IOException("The owned VLC session has closed.");
            var http=(HttpWebRequest)WebRequest.Create("http://127.0.0.1:"+port+"/requests/"+request);http.Timeout=5000;http.ReadWriteTimeout=5000;http.Proxy=null;
            http.Headers[HttpRequestHeader.Authorization]="Basic "+Convert.ToBase64String(Encoding.UTF8.GetBytes(":"+password));
            using(var response=http.GetResponse()) using(var reader=new StreamReader(response.GetResponseStream())) {char[] buffer=new char[4*1024*1024+1];int read=0,n;while((n=reader.Read(buffer,read,buffer.Length-read))>0) {read+=n;if(read==buffer.Length) throw new IOException("VLC response exceeds the supported limit.");}return new string(buffer,0,read);}
        });
    }
    async void CloseOwned()
    {
        if(closing) return;closing=true;timer.Stop();startup.Release(false);
        if(signal!=IntPtr.Zero&&Native.OwnedBy(signal,vlc.Id)&&!Native.TargetHasCapture(signal)) Native.InvokeSkinOpen(signal,vlc.Id,20,0);
        try
        {
            if(!vlc.HasExited)
            {
                // VLC may terminate the HTTP connection while processing its native quit hotkey.
                try {await Get("status.json?command=key&val=quit");} catch(WebException) {} catch(IOException) {}
                await Task.Run(delegate {vlc.WaitForExit(8000);});
                if(!vlc.HasExited) {Log("CLOSE forced_owned_process");vlc.Kill();vlc.WaitForExit(5000);}
                else Log("CLOSE graceful_owned_process");
            }
        }
        catch(Exception error) {Log("CLOSE "+error.GetType().Name);if(!vlc.HasExited) vlc.Kill();}
        tray.Visible=false;tray.Dispose();timer.Dispose();Log("END owned_skin_session");vlc.Dispose();ExitThread();
    }
    static int FreePort() {var listener=new TcpListener(IPAddress.Loopback,0);listener.Start();int value=((IPEndPoint)listener.LocalEndpoint).Port;listener.Stop();return value;}
    sealed class WindowOwner : IWin32Window {readonly IntPtr handle;internal WindowOwner(IntPtr value) {handle=value;}public IntPtr Handle {get {return handle;}}}
}
