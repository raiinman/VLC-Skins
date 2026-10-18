using System;
using System.Collections.Generic;
using System.IO;
using System.Web.Script.Serialization;

static class NfsManifestTest
{
    static void Need(bool value,string message) {if(!value) throw new Exception(message);}
    static void Write(string root,object value) {File.WriteAllText(Path.Combine(root,"bundle.json"),new JavaScriptSerializer().Serialize(value));}
    static bool Reject(string root) {try {NfsPlayer.ValidateBundle(root);return false;} catch(IOException) {return true;}}
    static int Main(string[] args)
    {
        string root=Path.GetFullPath(args[0]);Directory.CreateDirectory(root);string file=Path.Combine(root,"test-payload.txt");File.WriteAllText(file,"original fixture");
        var files=new Dictionary<string,object> {{"test-payload.txt",VlcIsolation.Hash(file)}};
        var value=new Dictionary<string,object> {{"schemaVersion",1},{"product","nfs-skin-helper"},{"version","1.1.0"},{"acceptedSkinSha256",new [] {NfsSkin.CanonicalHash,NfsSkin.ReleaseHash}},{"files",files}};
        Write(root,value);NfsPlayer.ValidateBundle(root);
        File.WriteAllText(file,"tampered");Need(Reject(root),"Tampered payload accepted.");File.WriteAllText(file,"original fixture");
        files["../outside.txt"]=new string('0',64);Write(root,value);Need(Reject(root),"Traversal accepted.");files.Remove("../outside.txt");
        value["acceptedSkinSha256"]=new [] {new string('0',64)};Write(root,value);Need(Reject(root),"Unknown skin pin accepted.");
        value["acceptedSkinSha256"]=new [] {NfsSkin.CanonicalHash,NfsSkin.CanonicalHash};Write(root,value);Need(Reject(root),"Duplicate skin pins accepted.");
        value["acceptedSkinSha256"]=new [] {NfsSkin.ReleaseHash};value["product"]="youtube";Write(root,value);Need(Reject(root),"Different product accepted.");
        value["product"]="nfs-skin-helper";files["TEST-PAYLOAD.TXT"]=VlcIsolation.Hash(file);Write(root,value);Need(Reject(root),"Case-insensitive duplicate paths accepted.");
        Console.WriteLine("NFS manifest checks passed: exact product/pins, payload integrity and bounded safe paths.");return 0;
    }
}
