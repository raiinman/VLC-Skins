"""Stage the standalone 1x helper, without YouTube, Chrome, Python or user data."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
SKINS = [
    '298b21d32f5eef893c6d5465e0692dca1035644c148d4bd48b2fa70e3d9f10e9',
    '91ed2e80498b3b6fc3a746a22c54e02b79df8f0f491837eaee674fdd73c87497',
]
SUPPORT = {
    'SkinEffects.exe': '56cc00e980f8d387f2f7ce31892a7f98b1c2d9334f0b4ff68d0f26a1c170bb68',
    'NfsWheelBridge64.dll': '0b88ad21177e214f671360ebb1962f2599012459910d3410de7c6184dc592e5d',
}
START = """NFS Underground skin helper for VLC, Windows 64-bit

This is the NFS skin helper. It does not include or require YouTube,
Google Chrome, Python, an account, or a compiler.

1. Install 64-bit VLC 3 from https://www.videolan.org/vlc/.
2. Download Need-for-Speed-Underground-1x.vlt separately. Keep it as a VLT.
3. Unzip this whole folder, then open Start NFS.exe and select the VLT.

The helper adds original skin sounds, a separate skin-sound volume control,
synchronized startup, and compact controls over framed video. Use its tray
icon to adjust skin-sound volume. Your media volume is separate.

This launcher owns a private VLC session and settings. It does not replace
normal VLC settings or attach to another running player. The YouTube app is
a separate product and is not started by this launcher.

The optional YouTube app can use this helper through its explicit NFS adapter.
Use one intended launcher for that session, rather than starting both players.
Keep all files together. The programs are unsigned. Original-size 1x only.
"""
NOTICES = """NFS Underground skin helper

Original helper/controller code: Copyright 2026 Dead Signal Interactive.
MIT, see LICENSE-CODE.txt. This grant does not cover original skin materials.

The separately downloaded skin retains original artwork, animations, sounds
and branding by The Skins Factory / Electronic Arts. Original copyright
(c) 2003 Electronic Arts Inc. All Rights Reserved. No endorsement claimed.

VLC is installed separately and retains its own license. No VLC executable,
DLLs, plugins, original sound files, fonts or Python runtime are in this ZIP.
The launcher uses the installed VLC runtime and the separately selected skin.
https://github.com/raiinman/VLC-Skins
"""


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def package(controller, expected, support, output, version, skin=None):
    controller, support, output = map(lambda p: Path(p).resolve(), (controller, support, output))
    if not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z.-]{0,63}', version):
        raise ValueError('Invalid version')
    if not re.fullmatch(r'[0-9a-f]{64}', expected) or digest(controller) != expected:
        raise ValueError('Controller differs from the verified build')
    files = {'Start NFS.exe': controller}
    if skin is not None:
        skin = Path(skin).resolve()
        if digest(skin) != SKINS[1]:
            raise ValueError('Bundle requires the unchanged notice-bearing released 1x skin')
        files['Need-for-Speed-Underground-1x.vlt'] = skin
    for name, pinned in SUPPORT.items():
        source = support / name
        if digest(source) != pinned:
            raise ValueError('Support payload differs from the verified 1x build: ' + name)
        files[name] = source
    lua = support / 'data/lua/intf/nfs_volume_osd_v1.lua'
    if digest(lua) != '9ff2ac594b3c29f20dff8e5026282412e7398d9c2f59810cf7a73412fc8409f1':
        raise ValueError('Volume observer differs from the verified 1x build')
    files['nfs_volume_osd_v1.lua'] = lua
    files['LICENSE-CODE.txt'] = ROOT / 'LICENSE-CODE.txt'
    payloads = {name: source.read_bytes() for name, source in files.items()}
    start, notices = START, NOTICES
    if skin is not None:
        start = start.replace('NFS Underground skin helper for VLC', 'NFS Underground for VLC')
        start = start.replace('This is the NFS skin helper.', 'This download includes the 1x skin and its sounds/video-controls helper.')
        start = start.replace('2. Download Need-for-Speed-Underground-1x.vlt separately. Keep it as a VLT.\n3. Unzip this whole folder, then open Start NFS.exe and select the VLT.',
                              '2. Extract this whole ZIP to a folder you want to keep.\n3. Open Start NFS.exe. The included skin loads automatically.')
        notices = notices.replace('The separately downloaded skin', 'The included unchanged skin')
        notices = notices.replace('DLLs, plugins, original sound files, fonts or Python runtime are in this ZIP.\nThe launcher uses the installed VLC runtime and the separately selected skin.',
                                  'DLLs, plugins or Python runtime are bundled. Original artwork, sounds and\nfonts remain inside the included VLT with their own credits/license notices.\nThe launcher uses the installed VLC runtime and the included skin.')
    payloads.update({'START-HERE.txt': start.encode(), 'NOTICES.txt': notices.encode()})
    manifest = dict(schemaVersion=1, product='nfs-skin-helper', version=version,
                    architecture='win64', acceptedSkinSha256=SKINS,
                    files={name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()})
    payloads['bundle.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    if output.exists():
        raise ValueError('Choose a fresh ZIP path; existing outputs are never overwritten')
    if output.suffix.lower() != '.zip':
        raise ValueError('Output must be a ZIP')
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'x', compression=ZIP_DEFLATED) as archive:
        for name, data in payloads.items():
            archive.writestr(name, data, compress_type=ZIP_STORED if name.endswith('.vlt') else ZIP_DEFLATED)
    with ZipFile(output) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(payloads):
            raise ValueError('Final ZIP failed CRC/member verification')
        for name, data in payloads.items():
            if archive.read(name) != data:
                raise ValueError('Final ZIP changed a payload: ' + name)
    return dict(file=output.name, sha256=digest(output), bytes=output.stat().st_size,
                controllerSha256=expected, files=manifest['files'],
                acceptedSkinSha256=SKINS, includesSkin=skin is not None,
                includesYouTube=False, includesPython=False)


def self_test(skin=None):
    with tempfile.TemporaryDirectory(prefix='nfs-package-') as directory:
        root = Path(directory)
        controller = root / 'fixture-controller.exe'
        controller.write_bytes(b'fixture, never executed')
        expected = digest(controller)
        output = root / 'helper.zip'
        package(controller, expected, ROOT / 'dist/skin-support', output, 'test')
        with ZipFile(output) as archive:
            assert not any(name.endswith(('.py', '.vlt')) for name in archive.namelist())
            assert 'Start NFS.exe' in archive.namelist()
        if skin is not None:
            bundled = root / 'complete.zip'
            result = package(controller, expected, ROOT / 'dist/skin-support', bundled, 'test', skin)
            with ZipFile(bundled) as archive:
                member = 'Need-for-Speed-Underground-1x.vlt'
                assert digest(skin) == result['files'][member] == SKINS[1]
                assert archive.read(member) == Path(skin).read_bytes()
                assert archive.getinfo(member).compress_type == ZIP_STORED
                assert 'loads automatically' in archive.read('START-HERE.txt').decode()
                assert not any('youtube' in name.lower() or name.endswith('.py') for name in archive.namelist())
            bad_skin = root / 'changed.vlt'
            bad_skin.write_bytes(b'wrong skin')
            try:
                package(controller, expected, ROOT / 'dist/skin-support', root / 'bad-skin.zip', 'test', bad_skin)
            except ValueError:
                assert not (root / 'bad-skin.zip').exists()
            else:
                raise AssertionError('Unverified skin accepted')
        for bad_expected, bad_output, version in [(expected, output, 'test'),
                ('0' * 64, root / 'wrong.zip', 'test'),
                (expected, root / 'traversal.zip', '../bad')]:
            try:
                package(controller, bad_expected, ROOT / 'dist/skin-support', bad_output, version)
            except ValueError:
                pass
            else:
                raise AssertionError('Unsafe or unverified package accepted')
    print('PASS package contents, CRCs, hashes, overwrite/tamper/version rejection; no programs executed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controller', type=Path)
    parser.add_argument('--expected-controller-sha256')
    parser.add_argument('--support', type=Path, default=ROOT / 'dist/skin-support')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--skin', type=Path, help='Include the unchanged notice-bearing release 1x VLT')
    parser.add_argument('--version', default='1.1.0')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test(args.skin)
    elif args.controller and args.expected_controller_sha256 and args.output:
        print(json.dumps(package(args.controller, args.expected_controller_sha256,
                                 args.support, args.output, args.version, args.skin), indent=2))
    else:
        parser.error('--controller, --expected-controller-sha256 and --output are required')


if __name__ == '__main__':
    main()
