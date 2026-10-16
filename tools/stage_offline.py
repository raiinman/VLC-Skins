"""Update an explicit offline review bundle; never execute its launchers."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINTS = ('Start-1x.cmd', 'Start-2x.cmd', 'Preview-1x.cmd', 'Preview-2x.cmd',
                'Start-NFS.ps1', 'Playlist-Text-Size.ps1', 'Playlist-Text-Size.cmd')
DOCS = ('PARITY.md', 'VERIFICATION.md', 'SOURCES.md', 'COMPACT-CONTROLS.md',
        'INFO-FADES.md', 'INFO-SOURCE-AUDIT.md', 'SOUNDS-AND-HOVER.md',
        'VIDEO-REPAINT.md', 'FULLSCREEN.md', 'offline-review.json',
        'compact-review.json', 'info-fades-review.json', 'info-source-audit.json',
        'info-load-benchmark.json', 'load-benchmark.json', 'effects-hover-review.json',
        'visual-comparison.json', 'STORAGE-OPTIMIZATION.md', 'storage-optimization-review.json',
        'LOADING-AND-MEMORY.md', 'storage-load-benchmark.json',
        'FAST-LOADING.md', 'fast-loading-equivalence.json', 'fast-load-benchmark.json',
        'fresh-skin-install.json', 'fresh-1x-rollout.json', 'hover-visibility-review.json', 'UI-POLISH.md', 'ui-polish-review.json',
        'native-hover-review.json', 'ui-polish-install.json', 'ui-polish-rollout.json')
NOTICE = """NEED FOR SPEED UNDERGROUND / VLC — OFFLINE REVIEW BUNDLE

These are the current verified offline packages and matching support files.
Staging does not launch VLC, execute the helper, install a skin, change a profile,
or reload the running player. Native evidence is scoped by exact package hashes;
loading checks do not verify visual controls, sound or animation smoothness.

Read docs/UI-POLISH.md and native-hover-review.json for the current UI fixes
and scoped private native hover/tooltip tests. FAST-LOADING.md and
fast-load-benchmark.json retain the prior exact hashes' loading measurements. Earlier failed candidates retain their own scoped reports. Native
measurements apply only when their exact VLT hashes match this bundle.

For a future MANUAL launch, Start-1x.cmd or Start-2x.cmd starts an isolated review
instance with optional sound/hover support. Preview-1x.cmd / Preview-2x.cmd are
isolated skin previews. Run them only when you choose to test; nothing is started
by this staging tool. Playlist-Text-Size.cmd prepares a personal copy for a future
launch. Existing custom skins/settings remain untouched by bundle refreshes.

bundle-manifest.json identifies every payload staged in this refresh by SHA256.
It excludes itself and unrelated files already in the destination. File updates
are atomic individually; a successful manifest is written last.
"""


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def check_output(output, root=ROOT):
    output, root = output.resolve(), root.resolve()
    allowed = (root.parent / 'outputs').resolve()
    protected = {'appdata', 'program files', 'program files (x86)', 'programdata', 'windows'}
    if (output == allowed or not output.is_relative_to(allowed) or output.is_relative_to(root)
            or any(part.casefold() in protected for part in output.parts)):
        raise ValueError('Choose a bundle subdirectory under ' + str(allowed) +
                         '; repository, AppData, installed and other external paths are refused')
    return output


def target(output, relative):
    destination = output / relative
    if not destination.resolve().is_relative_to(output.resolve()):
        raise ValueError('Destination link escapes the bundle: ' + str(relative))
    return destination


def atomic_write(destination, source=None, data=None, expected=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    h, size = hashlib.sha256(), 0
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.nfs-stage-', delete=False) as stream:
            temporary = Path(stream.name)
            if source is None:
                stream.write(data)
                h.update(data)
                size = len(data)
            else:
                with source.open('rb') as original:
                    for block in iter(lambda: original.read(1024 * 1024), b''):
                        stream.write(block)
                        h.update(block)
                        size += len(block)
            stream.flush()
            os.fsync(stream.fileno())
        sha = h.hexdigest()
        if expected is not None and sha != expected:
            raise ValueError('Payload changed since verification: ' + str(source))
        if source is not None and digest(source) != sha:
            raise ValueError('Source changed during staging: ' + str(source))
        os.replace(temporary, destination)
        temporary = None
        return {'sha256': sha, 'bytes': size}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def verified_packages(root):
    review = json.loads((root / 'docs/offline-review.json').read_text(encoding='utf-8'))
    result = {}
    for scale in (1, 2):
        name = f'Need-for-Speed-Underground-{scale}x.vlt'
        path = root / 'dist' / name
        sha = digest(path)
        if sha != review['packages'][str(scale)]['sha256']:
            raise ValueError(name + ' does not match docs/offline-review.json; finish verification first')
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                normalized = member.replace('\\', '/')
                if PurePosixPath(normalized).is_absolute() or '..' in PurePosixPath(normalized).parts or ':' in normalized:
                    raise ValueError('Unsafe archive member: ' + member)
            bad = archive.testzip()
            if bad:
                raise ValueError('Archive CRC failure: ' + bad)
            current = root / f'skins/need-for-speed-underground/vlc-{scale}x/theme.xml'
            if archive.read('theme.xml') != current.read_bytes():
                raise ValueError(name + ' differs from the generated theme')
        result[Path(name)] = sha
    return result


def stage(root, output):
    """Internal fixture-capable implementation; CLI enforces the output policy."""
    packages = verified_packages(root)
    payloads = {relative: root / 'dist' / relative for relative in packages}
    for name in ENTRY_POINTS:
        payloads[Path(name)] = root / 'dist' / name
    support = root / 'dist/skin-support'
    if not support.is_dir() or not (support / 'SkinEffects.exe').is_file():
        raise ValueError('Matching skin-support tree is missing')
    for file in support.rglob('*'):
        if file.is_symlink():
            raise ValueError('Support tree must contain regular files: ' + str(file))
        if file.is_file():
            payloads[Path('skin-support') / file.relative_to(support)] = file
    for name in DOCS:
        path = root / 'docs' / name
        if path.is_file():
            payloads[Path('docs') / name] = path
    # Hash and validate all inputs before changing any existing bundle payload.
    expected = {relative: packages.get(relative) or digest(source) for relative, source in payloads.items()}
    output.mkdir(parents=True, exist_ok=True)
    for relative in [*payloads, Path('START-HERE.txt'), Path('bundle-manifest.json')]:
        target(output, relative)
    manifest = {'schemaVersion': 1, 'scope': 'Offline staging only; native evidence separately scoped by exact hashes',
                'native_visual_controls_and_audio_tests': 'pending', 'files': {}}
    for relative, source in sorted(payloads.items(), key=lambda pair: pair[0].as_posix()):
        manifest['files'][relative.as_posix()] = atomic_write(target(output, relative), source=source, expected=expected[relative])
    manifest['files']['START-HERE.txt'] = atomic_write(target(output, 'START-HERE.txt'), data=NOTICE.encode('utf-8'))
    atomic_write(target(output, 'bundle-manifest.json'), data=(json.dumps(manifest, indent=2) + '\n').encode('utf-8'))
    return manifest


def self_test():
    scratch = ROOT.parent / 'work'
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='nfs-stage-test-', dir=scratch) as temporary:
        base = Path(temporary)
        fixture, output = base / 'repo', base / 'outputs/review'
        (fixture / 'dist/skin-support/data').mkdir(parents=True)
        (fixture / 'docs').mkdir()
        packages = {}
        for scale in (1, 2):
            theme = fixture / f'skins/need-for-speed-underground/vlc-{scale}x/theme.xml'
            theme.parent.mkdir(parents=True)
            theme.write_bytes(f'<Theme version="2.0"><!-- {scale}x fixture --></Theme>'.encode())
            archive = fixture / f'dist/Need-for-Speed-Underground-{scale}x.vlt'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('theme.xml', theme.read_bytes())
            packages[str(scale)] = {'sha256': digest(archive)}
        (fixture / 'docs/offline-review.json').write_text(json.dumps({'packages': packages}))
        for name in ENTRY_POINTS:
            (fixture / 'dist' / name).write_bytes(('fixture ' + name).encode())
        (fixture / 'dist/skin-support/SkinEffects.exe').write_bytes(b'fixture only; never execute')
        (fixture / 'dist/skin-support/data/settings.txt').write_bytes(b'bundled fixture data')
        (output / 'custom').mkdir(parents=True)
        personal = output / 'custom/personal.vlt'
        personal.write_bytes(b'user custom preserved')
        settings = output / 'settings.json'
        settings.write_bytes(b'user settings preserved')
        assert check_output(output, fixture) == output.resolve()
        for rejected in (fixture / 'dist', base / 'AppData/test', base / 'outputs', base / 'installed/test',
                         base / 'outputs/AppData/test', base / 'outputs/Program Files/test'):
            try:
                check_output(rejected, fixture)
            except ValueError:
                pass
            else:
                raise AssertionError('Output restriction escaped')
        first = stage(fixture, output)
        for relative, record in first['files'].items():
            assert digest(output / relative) == record['sha256']
            assert (output / relative).stat().st_size == record['bytes']
        (fixture / 'dist/Start-1x.cmd').write_bytes(b'updated fixture')
        stage(fixture, output)
        assert (output / 'Start-1x.cmd').read_bytes() == b'updated fixture'
        assert personal.read_bytes() == b'user custom preserved' and settings.read_bytes() == b'user settings preserved'
        assert not list(output.rglob('.nfs-stage-*'))
        (fixture / 'dist/Need-for-Speed-Underground-2x.vlt').write_bytes(b'stale package')
        before = digest(output / 'bundle-manifest.json')
        try:
            stage(fixture, output)
        except ValueError:
            pass
        else:
            raise AssertionError('Stale verification escaped')
        assert digest(output / 'bundle-manifest.json') == before
    print('PASS staging fixtures: payload hashes, refresh, unrelated files, stale package rejection and output boundaries; no launcher executed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Required bundle subdirectory under this workspace outputs/')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        if args.output:
            parser.error('--self-test does not accept --output')
        self_test()
        return
    if args.output is None:
        parser.error('--output is required')
    output = check_output(args.output)
    manifest = stage(ROOT, output)
    print(f'Staged {len(manifest["files"])} hashed payloads in {output}; no launcher executed')


if __name__ == '__main__':
    main()
