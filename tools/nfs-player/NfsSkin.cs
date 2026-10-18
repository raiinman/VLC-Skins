using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Xml;
using System.Xml.Linq;

// Only the audited 1x core, with an optional notice-only release wrapper.
static class NfsSkin
{
    internal const string CanonicalHash="298b21d32f5eef893c6d5465e0692dca1035644c148d4bd48b2fa70e3d9f10e9";
    internal const string ReleaseHash="91ed2e80498b3b6fc3a746a22c54e02b79df8f0f491837eaee674fdd73c87497";
    internal sealed class Prepared
    {
        internal string Path,ConfigPath;
        internal bool ControlledStartup;
        internal int VideoWidth=708,VideoHeight=440;
    }
    static readonly Regex Entry=new Regex("\\[\"([^\"\\r\\n]+)\"\\s+\"([^\"\\r\\n]+)\"\\s+(-?\\d+)\\s+(-?\\d+)\\s+(\\d+)\\s+(\\d+)\\s+([01])\\]");
    static XElement Window(XElement theme,string id) {return theme.Elements("Window").SingleOrDefault(x=>(string)x.Attribute("id")==id);}
    static XElement Layout(XElement window,string id) {return window==null ? null : window.Elements("Layout").SingleOrDefault(x=>(string)x.Attribute("id")==id);}
    static string Read(string path) {return File.Exists(path) ? File.ReadAllText(path,new UTF8Encoding(false,true)) : "";}
    static string Setting(string text,string name)
    {var m=Regex.Match(text,"(?m)^"+Regex.Escape(name)+"=([^\\r\\n]*)");return m.Success ? m.Groups[1].Value : "";}
    static string Put(string text,string name,string value)
    {
        string pattern="(?m)^"+Regex.Escape(name)+"=[^\\r\\n]*";
        if(Regex.IsMatch(text,pattern)) return Regex.Replace(text,pattern,m=>name+"="+value);
        var section=Regex.Match(text,"(?m)^\\[skins2\\][^\\r\\n]*(?:\\r?\\n|$)");
        return section.Success ? text.Insert(section.Index+section.Length,name+"="+value+"\n") : text+"\n[skins2]\n"+name+"="+value+"\n";
    }
    internal static Prepared Prepare(string source,string data)
    {
        source=System.IO.Path.GetFullPath(source);data=System.IO.Path.GetFullPath(data);
        string normal=System.IO.Path.GetFullPath(System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),"vlc","vlcrc"));
        string destination=System.IO.Path.Combine(data,"NfsUnderground1x.vlt"),config=System.IO.Path.ChangeExtension(destination,".vlcrc");
        if(source.Equals(destination,StringComparison.OrdinalIgnoreCase) || config.Equals(normal,StringComparison.OrdinalIgnoreCase)) throw new IOException("The source skin and normal VLC settings must remain separate.");
        string hash=VlcIsolation.Hash(source);
        if(hash!=CanonicalHash && hash!=ReleaseHash) throw new IOException("Select the supported NFS Underground 1x release skin.");
        string text=Read(File.Exists(config) ? config : normal);
        Directory.CreateDirectory(data);
        string staging=destination+"."+Guid.NewGuid().ToString("N")+".tmp";
        Prepared result;
        try
        {
            using(var input=ZipFile.OpenRead(source))
            {
                var xmlSettings=new XmlReaderSettings {DtdProcessing=DtdProcessing.Ignore,XmlResolver=null,MaxCharactersInDocument=16000000};
                XElement theme;
                using(var stream=input.GetEntry("theme.xml").Open()) using(var reader=XmlReader.Create(stream,xmlSettings)) theme=XElement.Load(reader,LoadOptions.PreserveWhitespace);
                if(Layout(Window(theme,"main"),"main_start")==null || Window(theme,"nfs_fx_intro")==null || input.GetEntry("nfs-effects.json")==null || theme.DescendantsAndSelf().Any(x=>(string)x.Attribute("id")=="startup_command")) throw new IOException("Incompatible NFS skin contract.");
                string stable=StableLayout(text,theme);
                theme.Add(new XElement("Window",new XAttribute("id","startup_command"),new XAttribute("x",-31000),new XAttribute("y",-29600),new XAttribute("visible","true"),new XAttribute("dragdrop","false"),new XAttribute("playondrop","false"),
                    new XElement("Layout",new XAttribute("id","startup_controls"),new XAttribute("width",231),new XAttribute("height",17),
                        Cell("startup_replay_cell",0,"main.setLayout(main_1);main.setLayout(main_start);main.show();nfs_fx_intro.setLayout(nfs_fx_intro_trigger)",false),
                        Cell("startup_return_cell",10,"main.setLayout("+stable+")",true))));
                using(var output=ZipFile.Open(staging,ZipArchiveMode.Create)) foreach(var entry in input.Entries)
                {
                    var copy=output.CreateEntry(entry.FullName,entry.CompressedLength==entry.Length ? CompressionLevel.NoCompression : CompressionLevel.Optimal);copy.LastWriteTime=entry.LastWriteTime;copy.ExternalAttributes=entry.ExternalAttributes;
                    using(var stream=copy.Open())
                        if(entry.FullName=="theme.xml") {using(var writer=new StreamWriter(stream,new UTF8Encoding(false))) writer.Write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE Theme PUBLIC \"-//VideoLAN//DTD VLC Skins V2.0//EN\" \"skin.dtd\">\n"+theme.ToString(SaveOptions.DisableFormatting));}
                        else using(var original=entry.Open()) original.CopyTo(stream);
                }
                result=new Prepared {Path=destination,ConfigPath=config,ControlledStartup=true};
                text=PrepareConfig(text,theme,stable,destination,result);
            }
            if(VlcIsolation.Hash(source)!=hash) throw new IOException("Source skin changed during preparation.");
            if(File.Exists(destination)) File.Replace(staging,destination,null); else File.Move(staging,destination);
            File.WriteAllText(config,text,new UTF8Encoding(false));
            return result;
        }
        finally {if(File.Exists(staging)) File.Delete(staging);}
    }
    static XElement Cell(string id,int x,string action,bool gated)
    {
        var cell=new XElement("Image",new XAttribute("id",id),new XAttribute("image","nfs_effect_marker"),new XAttribute("x",x),new XAttribute("y",0),new XAttribute("width",3),new XAttribute("height",3),new XAttribute("resize","scale"),new XAttribute("action2",action));
        if(gated) cell.SetAttributeValue("visible","main_start.isActive");return cell;
    }
    static string StableLayout(string text,XElement theme)
    {
        var m=Entry.Matches(Setting(text,"skins2-config")).Cast<Match>().FirstOrDefault(x=>x.Groups[1].Value=="main");
        string value=m==null ? "main_1" : m.Groups[2].Value.Replace("_opening","").Replace("_closing","_closed");
        if(!Regex.IsMatch(value,"^main_[1-7](?:_closed)?(?:_remaining)?$") || Layout(Window(theme,"main"),value)==null) value="main_1";
        return value;
    }
    internal static string PrepareConfig(string text,XElement theme,string stable,string skin,Prepared result)
    {
        var saved=Setting(text,"skins2-config");var matches=Entry.Matches(saved).Cast<Match>().ToArray();
        bool valid=String.Concat(matches.Select(m=>m.Value))==saved;
        var prior=valid ? matches.ToDictionary(m=>m.Groups[1].Value,m=>m) : new Dictionary<string,Match>();
        var resets=new Dictionary<string,string> {{"videoHoverController","video_hover_closed"},{"hover_volume_state","hover_volume_collapsed"},{"info_frame_state","info_frame_idle"},{"playlist_clear_command","playlist_clear_ready"},{"playlist_clear_capability","playlist_clear_disabled"},{"snapping_command","snapping_ready"},{"snapping_state","snapping_unavailable"},{"startup_command","startup_controls"}};
        string mode="elapsed";Match p;
        if(prior.TryGetValue("clock_state",out p) && Regex.IsMatch(p.Groups[2].Value,"^clock_(elapsed|remaining)(?:_[ab])?$")) mode=p.Groups[2].Value.Contains("remaining") ? "remaining" : "elapsed";
        else if(prior.TryGetValue("main",out p) && p.Groups[2].Value.EndsWith("_remaining")) mode="remaining";
        var rows=new List<string>();
        foreach(var window in theme.Elements("Window"))
        {
            string id=(string)window.Attribute("id");XElement layout=null;string row=null;Match old;
            if(id=="main") layout=Layout(window,stable);
            else if(id=="palette_state")
            {
                Match palette;
                layout=prior.TryGetValue(id,out palette)&&Regex.IsMatch(palette.Groups[2].Value,"^palette_[1-7]$") ? Layout(window,palette.Groups[2].Value) : null;
                if(layout==null) layout=Layout(window,"palette_"+stable[5]);
            }
            else if(id=="clock_state") layout=Layout(window,"clock_"+mode+"_a");
            else if(id.StartsWith("nfs_fx_")) layout=Layout(window,id+"_ready");
            else if(resets.ContainsKey(id)) layout=Layout(window,resets[id]);
            else if(prior.TryGetValue(id,out old) && Layout(window,old.Groups[2].Value)!=null) row=old.Value;
            if(row==null)
            {
                if(layout==null) layout=window.Element("Layout");
                string x=(string)window.Attribute("x")??"0",y=(string)window.Attribute("y")??"0",w=(string)layout.Attribute("width"),h=(string)layout.Attribute("height");
                bool visible=(string)window.Attribute("visible")!="false";
                if(id=="main" && prior.TryGetValue(id,out old)) {x=old.Groups[3].Value;y=old.Groups[4].Value;w=old.Groups[5].Value;h=old.Groups[6].Value;visible=true;}
                if(id=="palette_state") {x="0";y="0";visible=false;}
                if(id=="fullscreenController" || id=="info_frame_state") visible=false;
                row="[\""+id+"\" \""+(string)layout.Attribute("id")+"\" "+x+" "+y+" "+w+" "+h+" "+(visible ? "1" : "0")+"]";
            }
            rows.Add(row);
            if(id=="video") {var v=Entry.Match(row);int w,h;if(Int32.TryParse(v.Groups[5].Value,out w)&&Int32.TryParse(v.Groups[6].Value,out h)&&w>=708&&h>=440) {result.VideoWidth=w;result.VideoHeight=h;}}
        }
        return Put(Put(text,"skins2-last",skin),"skins2-config",String.Concat(rows));
    }
}
