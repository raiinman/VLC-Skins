"""Add redistribution notices to a release copy, preserving every runtime byte."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
CREDITS = """Need for Speed Underground for VLC, original-size 1x.
Original skin: The Skins Factory.
Original copyright (c) 2003 Electronic Arts Inc. All Rights Reserved.
VLC conversion: Dead Signal Interactive, with AI assistance.
Original artwork, sounds, scripts and branding retain their owners' rights.
No endorsement or ownership of those original materials is claimed.

FreeSans.ttf is retained unchanged from VLC's skin resources.
Its original font metadata credits Free Software Foundation, 2002/2003,
and the GNU GPL. See FreeSans-GPL-2.0.txt, retained from VLC's distribution.
Our original conversion/tool/helper code uses LICENSE-CODE.txt (MIT).
The MIT grant does not relicense upstream artwork, sounds, scripts or fonts.
https://github.com/raiinman/VLC-Skins
"""


def package(source, output, expected):
    source, output = source.resolve(), output.resolve()
    if source == output:
        raise ValueError('Release output must be a separate copy')
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Unexpected canonical source hash')
    additions = {
        'notices/CREDITS.txt': CREDITS.encode('utf-8'),
        'notices/FreeSans-GPL-2.0.txt': (ROOT/'vendor/GPL-2.0.txt').read_bytes(),
        'notices/LICENSE-CODE.txt': (ROOT/'LICENSE-CODE.txt').read_bytes(),
    }
    with ZipFile(source) as archive:
        if archive.testzip() is not None:
            raise ValueError('Source CRC failure')
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate source member')
        payload = []
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or ':' in info.filename or '\\' in info.filename:
                raise ValueError('Unsafe source member')
            if info.filename in additions:
                raise ValueError('Release notice collision')
            payload.append((info, archive.read(info.filename)))
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w') as archive:
        for info, content in payload:
            archive.writestr(info, content)
        for name, content in additions.items():
            info = ZipInfo(name, (2026, 10, 16, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, content)
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('Release CRC failure')
        assert set(archive.namelist()) == set(names) | set(additions)
        for info, content in payload:
            assert archive.read(info.filename) == content
            assert archive.getinfo(info.filename).compress_type == info.compress_type
        for name, content in additions.items():
            assert archive.read(name) == content
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
    return {'sourceSha256': expected, 'releaseSha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'bytes': output.stat().st_size, 'runtimeMembersUnchanged': len(payload), 'noticesAdded': sorted(additions)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-source-sha256', required=True)
    args = parser.parse_args()
    import json
    print(json.dumps(package(args.source, args.output, args.expected_source_sha256), indent=2))


if __name__ == '__main__':
    main()
