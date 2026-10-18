"""Offline launcher selection checks. No VLC, browser, dialog or user data writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--sources', type=Path, required=True)
parser.add_argument('--skin', type=Path, required=True)
parser.add_argument('--alternate-skin', type=Path, required=True)
args = parser.parse_args()
sources = args.sources.resolve(strict=True)
skin = args.skin.resolve(strict=True)
alternate = args.alternate_skin.resolve(strict=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
guards = {p: sha(p) for p in (skin, alternate)}
assert guards[skin] != guards[alternate], 'Supply the two distinct approved VLTs.'
with tempfile.TemporaryDirectory(prefix='nfs-launcher-') as directory:
    folder = Path(directory)
    executable = folder / 'Start NFS.exe'
    names = ['NfsPlayer', 'NfsSkin', 'SkinRuntime', 'Native', 'VlcIsolation', 'NativeHttp', 'HudCommands']
    compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    subprocess.run([str(compiler), '/nologo', '/target:winexe', '/platform:x64',
                    '/warnaserror+', '/main:NfsPlayer', '/out:' + str(executable),
                    *['/r:' + n + '.dll' for n in ('System.Drawing', 'System.Windows.Forms',
                      'System.Web.Extensions', 'System.Xml.Linq', 'System.IO.Compression',
                      'System.IO.Compression.FileSystem')],
                    *[str(sources / (n + '.cs')) for n in names]], check=True, timeout=30)
    adjacent = folder / 'Need-for-Speed-Underground-1x.vlt'
    shutil.copyfile(skin, adjacent)

    def prepare(name, explicit=None, remembered=None, expected=None):
        data = folder / name
        if remembered is not None:
            data.mkdir()
            (data / 'source-skin.txt').write_text(str(remembered))
        command = [str(executable), '--prepare-only', '--data-directory=' + str(data)]
        if explicit is not None:
            command.append('--skin=' + str(explicit))
        result = subprocess.run(command, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        if expected is None:
            assert result.returncode == 1 and not data.exists(), name
        else:
            assert result.returncode == 0, name
            assert (data / 'source-skin.txt').read_text() == str(expected), name

    prepare('fresh-adjacent', expected=adjacent)
    prepare('explicit-wins', explicit=alternate, expected=alternate)
    prepare('adjacent-before-remembered', remembered=alternate, expected=adjacent)
    invalid = folder / 'invalid.vlt'
    invalid.write_bytes(b'Unapproved skin')
    prepare('explicit-invalid-refused', explicit=invalid)
    adjacent.write_bytes(invalid.read_bytes())
    prepare('adjacent-invalid-refused')
    adjacent.unlink()  # Only this fixture's temporary copied file.
    prepare('remembered-fallback', remembered=alternate, expected=alternate)
assert all(sha(p) == value for p, value in guards.items())
print('PASS: adjacent discovery, explicit priority, remembered fallback and invalid skin rejection; source VLTs preserved.')
