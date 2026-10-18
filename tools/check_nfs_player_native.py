"""Opt-in standalone NFS controller proof on a never-selected desktop."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('--actual-vlc', action='store_true')
p.add_argument('--source', type=Path, required=True)
p.add_argument('--support', type=Path, required=True)
p.add_argument('--skin-tools', type=Path, default=Path(__file__).resolve().parent)
p.add_argument('--guard-pid', type=int, action='append', default=[])
a = p.parse_args()
if not a.actual_vlc:
    p.error('Explicit --actual-vlc is required')
for name in ('SkinEffects.exe', 'NfsWheelBridge64.dll', 'nfs_volume_osd_v1.lua'):
    if not (a.support / name).is_file():
        p.error('--support must name the extracted standalone helper ZIP folder: missing ' + name)
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(a.skin_tools))
from windows_load_host import DesktopProcess, ProcessGuard, input_desktop
from check_hover_native import OwnedJob

folder = root.parent / 'work' / ('nfs-standalone-native-' + str(time.time_ns()))
folder.mkdir()
exe = folder / 'Fixture.exe'
sources = ['NfsPlayer', 'NfsSkin', 'SkinRuntime', 'Native', 'VlcIsolation', 'NativeHttp', 'HudCommands']
source_hashes = {name + '.cs': hashlib.sha256((root / 'tools/nfs-player' / (name + '.cs')).read_bytes()).hexdigest()
                 for name in sources}
subprocess.run([str(Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'),
                '/nologo', '/target:exe', '/main:NfsStandaloneNativeTest', '/out:' + str(exe),
                '/r:System.Drawing.dll', '/r:System.Windows.Forms.dll', '/r:System.Web.Extensions.dll',
                '/r:System.Xml.Linq.dll', '/r:System.IO.Compression.dll', '/r:System.IO.Compression.FileSystem.dll',
                str(root / 'tools/nfs-player/tests/nfs-standalone-native.test.cs'),
                *[str(root / 'tools/nfs-player' / (name + '.cs')) for name in sources]], check=True)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
known = [Path(os.environ['APPDATA']) / 'vlc/vlcrc', Path(os.environ['APPDATA']) / 'vlc/vlc-qt-interface.ini', a.source]
before = {str(path): sha(path) for path in known if path.exists()}
guards = [ProcessGuard(pid) for pid in a.guard_pid]
desktop = input_desktop()
env = dict(os.environ)
env['APPDATA'] = str(folder / 'private-roaming')
env['LOCALAPPDATA'] = str(folder / 'private-local')
report = folder / 'result.txt'
process = job = None
try:
    process = DesktopProcess([str(exe), str(a.source.resolve()), str(folder / 'data'), str(a.support.resolve()), str(report)], env)
    job = OwnedJob(process)
    Path(str(report) + '.ready').write_text('ready', encoding='utf-8')
    code = process.wait(60)
    assert code == 0, report.read_text(encoding='utf-8')
    print(report.read_text(encoding='utf-8'))
finally:
    if process:
        process.close()
    if job:
        job.close()
    assert input_desktop() == desktop
    assert all(sha(Path(path)) == digest for path, digest in before.items())
    assert all(guard.alive() for guard in guards)
    assert all(sha(root / 'tools/nfs-player' / name) == digest for name, digest in source_hashes.items())
    for guard in guards:
        guard.close()
(folder / 'evidence.json').write_text(json.dumps({'normalAndSourceHashesPreserved': True, 'inputDesktopUnchanged': True,
    'physicalInputUsed': False, 'sourceSHA256': sha(a.source), 'supportSHA256': sha(a.support / 'SkinEffects.exe'),
    'nativeClearDefaultNo': True, 'nativeClearNoPreserved2': True, 'nativeClearYesEmptied0': True,
    'gracefulShutdown': True, 'savedGeometryFlushed': True, 'sourceHashesSHA256': source_hashes,
    'limitations': ['PCM dispatch is silent in private fixture; speaker audibility unverified',
                    'Hover channel and native pane observed; physical mouse hover behavior unverified',
                    'Clear No/Yes exercised only on two fixture-owned local rows; NO USER playlist changed']}, indent=2), encoding='utf-8')
print('Evidence:', folder)
