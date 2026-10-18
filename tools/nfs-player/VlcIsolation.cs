using System;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;

// Keep Qt's recent media and dialog settings away from the normal VLC profile.
static class VlcIsolation
{
    internal static ProcessStartInfo StartInfo(string installedExe,string data,string arguments,string osdScript=null)
    {
        installedExe=Path.GetFullPath(installedExe);
        string installed=Path.GetDirectoryName(installedExe);
        string hash=Hash(installedExe);
        string directory=Path.Combine(Path.GetFullPath(data),"VlcRuntime",hash);
        string portable=Path.Combine(directory,"portable");
        // VLC 3's portable-directory lookup uses a fixed MAX_PATH buffer.
        if(portable.Length>=260) throw new PathTooLongException("VLC's private settings path must be shorter than 260 characters.");
        Directory.CreateDirectory(portable);
        string executable=Path.Combine(directory,"vlc.exe");
        if(!File.Exists(executable)) File.Copy(installedExe,executable);
        if(Hash(executable)!=hash || Hash(installedExe)!=hash)
            throw new IOException("The private VLC launcher does not match the installed version. Refusing shared-settings fallback.");
        if(osdScript!=null)
        {
            var source=new FileInfo(osdScript);
            if(!source.Exists || source.Length==0 || source.Length>65536)
                throw new IOException("Invalid bundled volume observer.");
            string lua=Path.Combine(portable,"lua","intf");
            Directory.CreateDirectory(lua);
            string destination=Path.Combine(lua,"nfs_volume_osd_v1.lua");
            if(!File.Exists(destination) || Hash(destination)!=Hash(osdScript)) File.Copy(osdScript,destination,true);
        }
        var start=new ProcessStartInfo(executable,arguments) { UseShellExecute=false,WorkingDirectory=installed };
        start.EnvironmentVariables["PATH"]=installed+";"+(start.EnvironmentVariables["PATH"]??"");
        start.EnvironmentVariables["VLC_PLUGIN_PATH"]=Path.Combine(installed,"plugins");
        start.EnvironmentVariables["VLC_DATA_PATH"]=installed;
        return start;
    }

    internal static string Hash(string file)
    {
        using(var stream=File.OpenRead(file)) using(var sha=SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-","").ToLowerInvariant();
    }
}
