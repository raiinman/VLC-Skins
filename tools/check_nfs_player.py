"""Compile and check standalone skin preparation and package rejection offline."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ['NfsPlayer', 'NfsSkin', 'SkinRuntime', 'Native', 'VlcIsolation', 'NativeHttp', 'HudCommands']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skin', type=Path, required=True)
    args = parser.parse_args()
    skin = args.skin.resolve(strict=True)
    compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    with tempfile.TemporaryDirectory(prefix='nfs-source-check-') as directory:
        scratch = Path(directory)
        for fixture, entry, arguments in [
                ('nfs-skin.test.cs', 'NfsSkinTest', [str(skin), str(scratch / 'skin')]),
                ('nfs-manifest.test.cs', 'NfsManifestTest', [str(scratch / 'manifest')])]:
            executable = scratch / (entry + '.exe')
            subprocess.run([str(compiler), '/nologo', '/target:exe', '/platform:x64',
                            '/warnaserror+', '/main:' + entry, '/out:' + str(executable),
                            '/r:System.Drawing.dll', '/r:System.Windows.Forms.dll',
                            '/r:System.Web.Extensions.dll', '/r:System.Xml.Linq.dll',
                            '/r:System.IO.Compression.dll', '/r:System.IO.Compression.FileSystem.dll',
                            str(ROOT / 'tools/nfs-player/tests' / fixture),
                            *[str(ROOT / 'tools/nfs-player' / (name + '.cs')) for name in SOURCES]],
                           check=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run([str(executable), *arguments], check=True, timeout=30,
                           creationflags=subprocess.CREATE_NO_WINDOW)
    print('PASS standalone source checks; no VLC, browser or user profile writes.')


if __name__ == '__main__':
    main()
