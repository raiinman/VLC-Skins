using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Xml;
using System.Xml.Linq;

static class NfsSkinTest
{
    static void Check(bool value,string message) {if(!value) throw new Exception(message);}
    static XElement Theme(string path)
    {
        using(var zip=ZipFile.OpenRead(path)) using(var stream=zip.GetEntry("theme.xml").Open())
        using(var reader=XmlReader.Create(stream,new XmlReaderSettings {DtdProcessing=DtdProcessing.Ignore,XmlResolver=null})) return XElement.Load(reader);
    }
    static int Main(string[] args)
    {
        string source=Path.GetFullPath(args[0]),scratch=Path.GetFullPath(args[1]);
        string before=VlcIsolation.Hash(source);Directory.CreateDirectory(scratch);
        string expected=NfsSkin.ReleaseHash;
        Check(before==NfsSkin.CanonicalHash||before==expected,"Explicit supported source required.");
        string config=Path.Combine(scratch,"NfsUnderground1x.vlcrc");
        string text="[audio]\nvolume=0.73\n[skins2]\nskins2-config=[\"main\" \"main_4_closing_remaining\" 123 456 300 298 1][\"video\" \"video_1\" 333 444 900 550 1][\"clock_state\" \"clock_elapsed_b\" -31000 -30200 152 17 1][\"playlist_clear_command\" \"playlist_clear_requested\" -31000 -30100 162 17 1]\n";
        text=text.Replace("[\"video\"", "[\"palette_state\" \"palette_6\" 0 0 1 1 0][\"video\"");
        File.WriteAllText(config,text);
        var result=NfsSkin.Prepare(source,scratch);
        Check(result.ControlledStartup,"Controlled intro is required.");
        var theme=Theme(result.Path);
        Check(!theme.DescendantsAndSelf().Any(x=>((string)x.Attribute("id")??"").StartsWith("youtube")),"No YouTube resources.");
        Check(!theme.DescendantsAndSelf().Any(x=>((string)x.Attribute("id")??"").StartsWith("yt_")),"No YouTube HUD addon.");
        var command=theme.Elements("Window").Single(x=>(string)x.Attribute("id")=="startup_command");
        Check((string)command.Attribute("x")=="-31000"&&(string)command.Attribute("y")=="-29600","Offscreen startup.");
        Check(command.Descendants("Image").Single(x=>(string)x.Attribute("id")=="startup_return_cell").Attribute("action2").Value=="main.setLayout(main_4_closed_remaining)","Stable shutter/clock/palette return.");
        string updated=File.ReadAllText(config);
        Check(updated.Contains("volume=0.73"),"Preserve unrelated preferences.");
        Check(updated.Contains("[\"main\" \"main_4_closed_remaining\" 123 456 300 298 1]"),"Preserve main geometry.");
        Check(updated.Contains("[\"palette_state\" \"palette_6\" 0 0 1 1 0]"),"Preserve independent valid palette selection.");
        Check(updated.Contains("[\"video\" \"video_1\" 333 444 900 550 1]")&&result.VideoWidth==900&&result.VideoHeight==550,"Preserve native video geometry for helper discovery.");
        Check(updated.Contains("[\"clock_state\" \"clock_elapsed_a\" -31000 -30200 151 17 1]"),"Explicit clock wins over old main suffix.");
        Check(updated.Contains("[\"playlist_clear_command\" \"playlist_clear_ready\" -31000 -30100 161 17 1]"),"Do not replay clear.");
        Check(updated.Contains("[\"playlist_clear_capability\" \"playlist_clear_disabled\" -31000 -30000 171 1 1]"),"Clear capability starts disabled.");
        Check(updated.Contains("[\"snapping_command\" \"snapping_ready\" -31000 -29800 191 17 1]"),"Reset snapping command.");
        Check(updated.Contains("[\"videoHoverController\" \"video_hover_closed\""),"Hover starts closed.");
        Check(updated.Contains("[\"nfs_fx_intro\" \"nfs_fx_intro_ready\""),"Intro must wait for helper readiness.");
        using(var original=ZipFile.OpenRead(source)) using(var derived=ZipFile.OpenRead(result.Path))
        {
            Check(original.Entries.Count==derived.Entries.Count,"No injected archive payloads.");
            foreach(var entry in original.Entries.Where(x=>x.FullName!="theme.xml"))
            {using(var a=entry.Open()) using(var b=derived.GetEntry(entry.FullName).Open()) {var aa=new MemoryStream();var bb=new MemoryStream();a.CopyTo(aa);b.CopyTo(bb);Check(aa.ToArray().SequenceEqual(bb.ToArray()),"Original asset changed: "+entry.FullName);}}
        }
        var originalTheme=Theme(source);command.Remove();Check(XNode.DeepEquals(originalTheme,theme),"Only startup command changes the original theme.");
        var again=NfsSkin.Prepare(source,scratch);Check(File.ReadAllText(again.ConfigPath)==updated,"Upgrade preparation is stable.");
        Check(VlcIsolation.Hash(source)==before,"Source skin remains unchanged.");
        string bad=Path.Combine(scratch,"unsupported.vlt");File.WriteAllText(bad,"not a supported skin");bool rejected=false;
        try {NfsSkin.Prepare(bad,Path.Combine(scratch,"bad"));} catch(IOException) {rejected=true;}
        Check(rejected&&!Directory.Exists(Path.Combine(scratch,"bad")),"Reject unsupported before data creation.");
        Console.WriteLine("NFS skin preparation passed: stable startup, transients, preferences and original assets.");return 0;
    }
}
