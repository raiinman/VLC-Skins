"""Check preview launchers without executing CMD, start, VLC, or desktop input.

Only each extracted PowerShell INI writer executes, against private fixtures
under work/. Normal profiles and installed skins are never accessed.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def writer_command(text, scale):
    assert f'set "NFS_REVIEW_CONFIG=%~dp0parity-{scale}x-vlcrc.ini"' in text
    assert f'set "NFS_REVIEW_SKIN=%~dp0Need-for-Speed-Underground-{scale}x.vlt"' in text
    assert re.search(r'if not exist "%NFS_REVIEW_SKIN%" \([^)]*exit /b 1\s*\)', text)
    matches = re.findall(r'^powershell.exe -NoLogo -NoProfile -NonInteractive -Command "([^\r\n]+)"$', text, re.M)
    assert len(matches) == 1, 'Expected one isolated configuration writer'
    writer = matches[0]
    starts = re.findall(r'^start .+$', text, re.M)
    assert len(starts) == 1
    launch = starts[0]
    assert '--config="%NFS_REVIEW_CONFIG%"' in launch and '--intf=skins2' in launch
    assert '--skins2-last' not in text and '--skins2-config' not in text, 'Preview selection and reset must use its owned INI consistently'
    before_start = text[text.index('powershell.exe'):text.index(launch)]
    assert re.search(r'if errorlevel 1 \([^)]*exit /b 1\s*\)', before_start), 'Writer failure must abort before start'
    assert text.index('if not exist "%NFS_REVIEW_SKIN%"') < text.index('powershell.exe')
    # Execute precisely the reviewed writer; paths enter only through env vars.
    assert '$env:NFS_REVIEW_CONFIG' in writer and '$env:NFS_REVIEW_SKIN' in writer
    return writer


def run_writer(powershell, command, config, skin, cwd):
    env = dict(os.environ, NFS_REVIEW_CONFIG=str(config), NFS_REVIEW_SKIN=str(skin))
    return subprocess.run([powershell, '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', command],
                          env=env, cwd=cwd, capture_output=True, timeout=20,
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def main():
    powershell = shutil.which('powershell.exe')
    assert powershell, 'Windows PowerShell is required to verify the launcher INI writer'
    scratch = ROOT.parent/'work'
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='launcher-check-', dir=scratch) as tmp:
        fixture = Path(tmp)/"Unicode-é-路径 & O'Brien"
        fixture.mkdir()
        for scale in (1, 2):
            text = (ROOT/f'dist/Preview-{scale}x.cmd').read_text(encoding='utf-8')
            command = writer_command(text, scale)
            config = fixture/f'parity-{scale}x-vlcrc.ini'
            skin = fixture/f'Need-for-Speed-Underground-{scale}x.vlt'
            skin.write_bytes(b'writer fixture only; never opened by VLC')
            config.write_text('[skins2]\nskins2-last=stale.vlt\nskins2-config=saved-layout\n', encoding='utf-8')
            result = run_writer(powershell, command, config, skin, fixture)
            assert result.returncode == 0, ('INI writer failed', result.stderr.decode(errors='replace'))
            expected = f'[skins2]\r\nskins2-last={skin}\r\nskins2-config=\r\n'.encode('utf-8')
            assert config.read_bytes() == expected, 'Writer must reset saved layout and preserve Unicode skin path as UTF-8 without BOM'
            blocked = fixture/f'blocked-{scale}x.ini'
            blocked.mkdir()
            result = run_writer(powershell, command, blocked, skin, fixture)
            assert result.returncode != 0, 'Unwritable target must produce a failing exit code'
            assert blocked.is_dir() and config.read_bytes() == expected, 'Failure must leave other fixtures unchanged'
            print(f'PASS {scale}x: isolated launcher paths, UTF-8 writer/reset with Unicode, ampersand and apostrophe; write failure exits nonzero. VLC not launched.')


if __name__ == '__main__':
    main()
