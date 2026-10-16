"""Test shared native hover exposure on private non-input fixture desktops only.

Default mode launches only synthetic private windows. --actual-vlc explicitly
launches owned copied VLCs with private settings, never the product helper.
Never switches desktop, injects physical input or accesses live settings for
writing. Requires --output scratch directory; reports exclude full end-to-end use.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
from lxml import etree as E

from windows_load_host import DesktopProcess, ProcessGuard, input_desktop

ROOT = Path(__file__).resolve().parents[1]


class OwnedJob:
    """Kill only this fixture and its private child VLCs on owner failure."""
    def __init__(self, process):
        class Basic(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
                        ('flags', wintypes.DWORD), ('minimum', ctypes.c_size_t), ('maximum', ctypes.c_size_t),
                        ('active', wintypes.DWORD), ('affinity', ctypes.c_size_t), ('priority', wintypes.DWORD), ('scheduling', wintypes.DWORD)]
        class Counters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ('reads', 'writes', 'other', 'read_bytes', 'write_bytes', 'other_bytes')]
        class Extended(ctypes.Structure):
            _fields_ = [('basic', Basic), ('io', Counters), ('process_memory', ctypes.c_size_t),
                        ('job_memory', ctypes.c_size_t), ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = self.kernel.CreateJobObjectW
        create.argtypes, create.restype = [ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE
        self.handle = create(None, None)
        if not self.handle: raise ctypes.WinError(ctypes.get_last_error())
        try:
            info = Extended(); info.basic.flags = 0x2000
            configure = self.kernel.SetInformationJobObject
            configure.argtypes, configure.restype = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL
            assign = self.kernel.AssignProcessToJobObject
            assign.argtypes, assign.restype = [wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL
            if not configure(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)) or not assign(self.handle, process.handle):
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            self.close()
            raise
    def close(self):
        if self.handle:
            close = self.kernel.CloseHandle
            close.argtypes, close.restype = [wintypes.HANDLE], wintypes.BOOL
            if not close(self.handle): raise ctypes.WinError(ctypes.get_last_error())
            self.handle = None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def silent_video(path):
    """Own steady image input produces a native video output without audio."""
    from PIL import Image
    Image.new('RGB', (32, 32), (64, 48, 32)).save(path)


def actual_requests(output, installed):
    runtime = output/'VlcRuntime'/sha(installed)
    shutil.copytree(installed.parent, runtime)
    (runtime/'portable').mkdir(exist_ok=True)
    assert sha(runtime/'vlc.exe') == sha(installed)
    data_root = output/'skin-support-data'
    shutil.copytree(ROOT/'dist/skin-support/data', data_root)
    font = Path('skins/fonts/FreeSans.ttf')
    assert sha(data_root/font) == sha(ROOT/'dist/skin-support/data'/font)
    requests, hashes = [], {}
    for scale in (1, 2):
        folder = output/f'{scale}x'
        folder.mkdir()
        source = ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt'
        skin = folder/source.name
        hashes[str(scale)] = sha(source)
        shutil.copyfile(source, skin)
        assert sha(skin) == hashes[str(scale)]
        with zipfile.ZipFile(skin) as archive:
            tree = E.fromstring(archive.read('theme.xml'))
        saved = []
        for window in tree.findall('Window'):
            name = window.get('id')
            layout = window.findall('Layout')[-1]
            if name == 'main': layout = window.find('Layout[@id="main_1"]')
            visible = 1 if name == 'video' else int(window.get('visible', 'true') == 'true')
            saved.append(f'["{name}" "{layout.get("id")}" {window.get("x", "0")} {window.get("y", "0")} {layout.get("width")} {layout.get("height")} {visible}]')
        config, log, clip = folder/'vlcrc.ini', folder/'vlc.log', folder/'silent-fixture.png'
        config.write_text('[skins2]\nskins2-last='+str(skin)+'\nskins2-config='+''.join(saved)+'\n', encoding='utf-8')
        silent_video(clip)
        temporary = folder/'Temp'
        temporary.mkdir()
        env = {'APPDATA': str(folder/'AppData'), 'LOCALAPPDATA': str(folder/'LocalAppData'), 'TEMP': str(temporary), 'TMP': str(temporary),
               'VLC_DATA_PATH': str(data_root)}
        arguments = ['--no-one-instance', '--no-one-instance-when-started-from-file', '--no-media-library',
                     '--config='+str(config), '--intf=skins2', '--skins2-last='+str(skin), '--no-qt-privacy-ask',
                     '--no-metadata-network-access', '--aout=dummy', '--vout=wingdi', '--demux=image', '--image-duration=600', '--image-fps=10/1', '--verbose=2',
                     '--file-logging', '--logfile='+str(log), str(clip)]
        requests.append(dict(scale=scale, executable=str(runtime/'vlc.exe'), installed=str(installed),
                             arguments=subprocess.list2cmdline(arguments), skin=str(skin), log=str(log), environment=env))
    path = output/'requests.json'
    path.write_text(json.dumps(requests), encoding='utf-8')
    return path, hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--actual-vlc', action='store_true', help='Explicitly launch both copied VLTs on the private fixture desktop')
    parser.add_argument('--protect-pid', type=int, action='append', default=[])
    parser.add_argument('--guard-file', type=Path, action='append', default=[])
    args = parser.parse_args()
    scratch = (ROOT.parent/'work').resolve()
    output = args.output.resolve()
    if not output.is_relative_to(scratch) or output == scratch:
        parser.error('--output must be a new subdirectory under workspace work/')
    output.mkdir(parents=True, exist_ok=False)
    compiler = Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    if not compiler.is_file():
        compiler = Path(os.environ['WINDIR'])/'Microsoft.NET/Framework/v4.0.30319/csc.exe'
    product, fixture = ROOT/'tools/SkinEffects.cs', ROOT/'tools/check_hover_native.cs'
    compiled_product, compiled_fixture = output/'CompiledProduct.cs', output/'CompiledFixture.cs'
    compiled_product.write_bytes(product.read_bytes())
    compiled_fixture.write_bytes(fixture.read_bytes())
    executable = output/'HoverNativeFixture.exe'
    references = ['System.Windows.Forms', 'System.Drawing', 'System.Web.Extensions',
                  'System.IO.Compression', 'System.IO.Compression.FileSystem']
    command = [str(compiler), '/nologo', '/target:winexe', '/optimize+',
               '/main:NfsSkinSupport.HoverNativeFixture', '/out:'+str(executable)]
    command += ['/reference:'+name+'.dll' for name in references]
    subprocess.run(command+[str(compiled_product), str(compiled_fixture)], check=True, capture_output=True, text=True)
    point = wintypes.POINT()
    get_cursor = ctypes.WinDLL('user32', use_last_error=True).GetCursorPos
    get_cursor.argtypes, get_cursor.restype = [ctypes.POINTER(wintypes.POINT)], wintypes.BOOL
    if not get_cursor(ctypes.byref(point)):
        raise ctypes.WinError(ctypes.get_last_error())
    before = input_desktop()
    normal = Path(os.environ['APPDATA'])/'vlc'
    paths = list(dict.fromkeys([normal/'vlcrc', normal/'vlc-qt-interface.ini', *args.guard_file]))
    hashes_before = {str(path.resolve()): sha(path) for path in paths}
    guards = []
    process = None
    job = None
    report_path = output/'fixture.json'
    report = {'passed': False}
    cleanup_error = None
    try:
        for pid in args.protect_pid: guards.append(ProcessGuard(pid))
        environment = dict(os.environ)
        environment['TEMP'] = environment['TMP'] = str(output)
        command = [str(executable), str(report_path), str(point.x), str(point.y)]
        package_hashes = {}
        if args.actual_vlc:
            requests, package_hashes = actual_requests(output, Path('C:/Program Files/VideoLAN/VLC/vlc.exe'))
            command.append(str(requests))
        process = DesktopProcess(command, environment)
        job = OwnedJob(process)
        if args.actual_vlc: Path(str(requests)+'.ready').write_text('Owned fixture job armed\n')
        result = process.wait(290 if args.actual_vlc else 30)
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding='utf-8-sig'))
        else:
            report['error'] = 'Native fixture produced no report; private-desktop APIs may be unavailable.'
        report['fixture_exit_code'] = result
        report['packages'] = package_hashes
        report['skin_copies_unchanged'] = all(sha(output/f'{scale}x'/f'Need-for-Speed-Underground-{scale}x.vlt') == value for scale, value in package_hashes.items())
    finally:
        cleanup_errors = []
        for owned in (job, process):
            if owned is not None:
                try: owned.close()
                except Exception as error: cleanup_errors.append(str(error))
        cleanup_error = '; '.join(cleanup_errors) or None
        report['cleanup_error'] = cleanup_error
        report['owned_process_closed'] = process is not None and process.handle is None
        try:
            report['input_desktop_unchanged'] = input_desktop() == before
        except OSError:
            report['input_desktop_unchanged'] = False
        report['protected_processes'] = [dict(pid=guard.pid, creation_filetime=guard.started, alive=guard.alive()) for guard in guards]
        for guard in guards: guard.close()
        hashes_after = {str(path.resolve()): sha(path) for path in paths}
        report['guarded_files_unchanged'] = hashes_before == hashes_after
        report['guarded_file_count'] = len(paths)
        (output/'preservation.json').write_text(json.dumps(dict(before=hashes_before, after=hashes_after), indent=2)+'\n', encoding='utf-8')
        report['source_sha256'] = sha(compiled_product)
        report['fixture_sha256'] = sha(compiled_fixture)
        report['fixture_executable_sha256'] = sha(executable)
        report['packaged_helper_sha256_reference_only'] = sha(ROOT/'dist/skin-support/SkinEffects.exe')
        report['deployed_helper_executable_launched'] = False
        report['binary_scope'] = ('The private fixture executable compiles immutable copies of product source and fixture source. '
                                  'It calls shared product methods directly. The packaged helper hash is reference only; '
                                  'neither the packaged nor the user-session helper executable is launched by this test.')
        report['passed'] = bool(report.get('passed') and report.get('fixture_exit_code') == 0 and not cleanup_error and report['input_desktop_unchanged']
                              and report['guarded_files_unchanged'] and all(item['alive'] for item in report['protected_processes'])
                              and report.get('skin_copies_unchanged', False))
        (output/'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'cases': len(report.get('cases', [])), 'report': str(output/'result.json')}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
