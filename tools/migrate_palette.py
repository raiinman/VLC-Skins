"""Add persistent palette state to an explicitly selected, closed VLC profile.

No profile is discovered automatically. Unrecognized/empty saved layouts are
left unchanged. Other entries and configuration text retain their exact bytes.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import tempfile
import time


ENTRY = re.compile(r'\["([^"\r\n]+)"\s+"([^"\r\n]+)"\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+([01])\]')


def migrate(text):
    lines = list(re.finditer(r'(?m)^skins2-config=([^\r\n]*)', text))
    if len(lines) != 1:
        return text
    line = lines[0]
    saved = line.group(1)
    entries = list(ENTRY.finditer(saved))
    if not entries:
        return text
    end = 0
    for entry in entries:
        if saved[end:entry.start()].strip(' \t'):
            return text
        end = entry.end()
    if saved[end:].strip(' \t'):
        return text
    main = [entry for entry in entries if entry.group(1) == 'main']
    state = [entry for entry in entries if entry.group(1) == 'palette_state']
    if len(main) != 1 or len(state) > 1:
        return text
    layout = main[0].group(2)
    color = re.fullmatch(r'main_([1-7])(?:_(?:opening|closed|closing))?(?:_remaining)?', layout)
    if layout == 'main_start':
        number = '1'
    elif color:
        number = color.group(1)
    else:
        return text
    replacement = f'["palette_state" "palette_{number}" 0 0 1 1 0]'
    if state:
        saved = saved[:state[0].start()] + replacement + saved[state[0].end():]
    else:
        saved += replacement
    return text[:line.start(1)] + saved + text[line.end(1):]


def migrate_file(config):
    config = Path(config).resolve(strict=True)
    before = config.read_bytes()
    after = migrate(before.decode('utf-8')).encode('utf-8')
    if after == before:
        return None
    backup = config.with_name(config.name+f'.palette-backup-{time.time_ns()}')
    with backup.open('xb') as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())
    descriptor, temporary = tempfile.mkstemp(prefix=config.name+'.palette-', suffix='.tmp', dir=config.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(after)
            stream.flush()
            os.fsync(stream.fileno())
        shutil.copymode(config, temporary)
        if config.read_bytes() != before:
            raise RuntimeError('Configuration changed during migration; original was left untouched.')
        os.replace(temporary, config)
    finally:
        if temporary.exists():
            temporary.unlink()
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path, help='Explicit VLC configuration path; close its VLC instance first.')
    args = parser.parse_args()
    backup = migrate_file(args.config)
    print('Palette migration applied; backup: '+str(backup) if backup else 'Configuration unchanged.')


if __name__ == '__main__':
    main()
