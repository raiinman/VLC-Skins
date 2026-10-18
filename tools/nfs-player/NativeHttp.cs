using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;

// Private HTTP templates retain installed VLC's command implementation unchanged.
// Native ES choices: VideoLAN vlc/3.0.x/modules/lua/libs/variables.c get_list.
static class NativeHttp
{
    const int MaximumTemplateBytes=1024*1024;
    internal static string Prepare(string installedVlcDir,string data)
    {
        return Prepare(installedVlcDir,data,Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"youtube-subtitles.json"));
    }
    internal static string Prepare(string installedVlcDir,string data,string subtitleTemplate)
    {
        if(subtitleTemplate==null) throw new ArgumentNullException("subtitleTemplate");
        return PrepareTemplates(installedVlcDir,data,subtitleTemplate);
    }
    internal static string PrepareBase(string installedVlcDir,string data)
    { return PrepareTemplates(installedVlcDir,data,null); }
    static string PrepareTemplates(string installedVlcDir,string data,string subtitleTemplate)
    {
        string installed=Path.GetFullPath(installedVlcDir), destination=Path.GetFullPath(data);
        if(destination.Equals(installed,StringComparison.OrdinalIgnoreCase) || destination.StartsWith(installed.TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))
            throw new IOException("Private HTTP data must be outside the installed VLC directory.");
        var files=new Dictionary<string,byte[]>();
        foreach(string name in new [] {"status.json","playlist.json"})
            files.Add(name,Read(Path.Combine(installed,"lua","http","requests",name)));
        if(subtitleTemplate!=null) files.Add("youtube-subtitles.json",Read(subtitleTemplate));
        string[] names=subtitleTemplate==null ? new [] {"status.json","playlist.json"} : new [] {"status.json","playlist.json","youtube-subtitles.json"};
        byte[] fingerprint;
        using(var memory=new MemoryStream())
        {
            foreach(string name in names)
            {
                byte[] label=Encoding.UTF8.GetBytes(name+"\0"+files[name].Length+"\0");
                memory.Write(label,0,label.Length); memory.Write(files[name],0,files[name].Length);
            }
            using(var sha=SHA256.Create()) fingerprint=sha.ComputeHash(memory.ToArray());
        }
        string parent=Path.Combine(destination,"HttpRuntime");
        string directory=Path.Combine(parent,BitConverter.ToString(fingerprint).Replace("-","").ToLowerInvariant());
        if(Path.Combine(directory,"requests","youtube-subtitles.json").Length>=260)
            throw new PathTooLongException("Private VLC HTTP paths must be shorter than 260 characters.");
        CheckDirectory(destination); CheckDirectory(parent);
        Directory.CreateDirectory(parent);
        if(!Directory.Exists(directory))
        {
            string staging=Path.Combine(parent,"prepare-"+Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(Path.Combine(staging,"requests"));
            foreach(var file in files) File.WriteAllBytes(Path.Combine(staging,"requests",file.Key),file.Value);
            try { Directory.Move(staging,directory); }
            catch(IOException) { if(!Directory.Exists(directory)) throw; }
        }
        CheckDirectory(directory);
        var rootEntries=Directory.GetFileSystemEntries(directory);
        string requests=Path.Combine(directory,"requests"); CheckDirectory(requests);
        if(rootEntries.Length!=1 || !Directory.Exists(requests)) throw new IOException("Unexpected private VLC HTTP content.");
        if(Directory.GetDirectories(requests).Length!=0 || Directory.GetFiles(requests).Length!=files.Count)
            throw new IOException("Unexpected private VLC HTTP requests.");
        foreach(var file in files)
        {
            byte[] actual=Read(Path.Combine(requests,file.Key));
            if(actual.Length!=file.Value.Length) throw new IOException("Private VLC HTTP content was modified.");
            for(int index=0;index<actual.Length;index++)
                if(actual[index]!=file.Value[index]) throw new IOException("Private VLC HTTP content was modified.");
        }
        return directory;
    }
    static void CheckDirectory(string path)
    {
        if((Directory.Exists(path) || File.Exists(path)) &&
            ((File.GetAttributes(path)&FileAttributes.ReparsePoint)!=0 || !Directory.Exists(path)))
            throw new IOException("Unexpected private VLC HTTP directory.");
    }
    static byte[] Read(string path)
    {
        var file=new FileInfo(path);
        if(!file.Exists || (file.Attributes&FileAttributes.ReparsePoint)!=0 || file.Length<1 || file.Length>MaximumTemplateBytes)
            throw new IOException("Missing or invalid VLC HTTP template.");
        byte[] data=File.ReadAllBytes(path);
        if(data.Length<1 || data.Length>MaximumTemplateBytes) throw new IOException("Invalid VLC HTTP template size.");
        return data;
    }
}
