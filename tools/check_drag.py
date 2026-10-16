"""Check retained magnetic edge movement offline, without pointer input or VLC launches.

Models the native single-window work-area edge-offset formula. These checks
establish the intended 15px magnetic snap threshold, not smooth native repaint timing or
which work area VLC chooses on a particular monitor configuration.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import zipfile

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]


def edge_offsets(left, top, width, height, dx, dy, work, magnet):
    """Independent transcription of WindowManager::checkAnchors edge tests."""
    wl, wt, wr, wb = work
    new_left, new_top = left + dx, top + dy
    if wl - magnet < new_left < wl + magnet:
        dx = wl - left
    if wt - magnet < new_top < wt + magnet:
        dy = wt - top
    if wr - magnet < new_left + width < wr + magnet:
        dx = wr - left - width
    if wb - magnet < new_top + height < wb + magnet:
        dy = wb - top - height
    return dx, dy


def sweep():
    count = 0
    # Negative-origin/upper-monitor rectangles exercise coordinate arithmetic;
    # this does not assert that VLC selects a per-monitor work area itself.
    for work in ((0, 0, 1920, 1040), (-2560, 0, 0, 1440),
                 (0, -1440, 2560, 0), (-1920, -1080, 0, 0)):
        wl, wt, wr, wb = work
        for scale in (1, 2):
            width, height = 708 * scale, 440 * scale
            left, top = wl + 200, wt + 80
            for distance in range(-30, 31):
                candidates = ((wl + distance, wt + 80),
                              (wr - width + distance, wt + 80),
                              (wl + 200, wt + distance),
                              (wl + 200, wb - height + distance))
                for edge, (x, y) in enumerate(candidates):
                    requested = (x - left, y - top)
                    expected = requested
                    if abs(distance) < 15:
                        targets = ((wl, y), (wr - width, y),
                                   (x, wt), (x, wb - height))
                        snap_x, snap_y = targets[edge]
                        expected = (snap_x - left, snap_y - top)
                    assert edge_offsets(left, top, width, height, *requested, work, 15) == expected
                    count += 1
            # Independently specified examples preserve the desired magnetic
            # threshold, including the strict 15px boundary.
            for distance in (-14, -1, 1, 14):
                requested = (wl + distance - left, 0)
                assert edge_offsets(left, top, width, height, *requested, work, 15) == (wl - left, 0)
            for distance in (-15, 15):
                requested = (wl + distance - left, 0)
                assert edge_offsets(left, top, width, height, *requested, work, 15) == requested
    return count


def verify_theme(tree):
    assert tree.tag == 'Theme' and tree.get('magnet', '15') == '15', 'Retain native 15px magnetic edge snapping'


def mutation_checks():
    # Omission resolves to the official parser/DTD default. Explicit15 is
    # equivalent. Docking anchors are audited separately, never forbidden here.
    theme = E.Element('Theme', version='2.0')
    verify_theme(theme)
    theme.set('magnet', '15')
    verify_theme(theme)
    for value in ('0', '-15', '14'):
        changed = deepcopy(theme)
        changed.set('magnet', value)
        try:
            verify_theme(changed)
        except AssertionError:
            pass
        else:
            raise AssertionError('Unsafe magnetic threshold mutation escaped: ' + value)
    return 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true', help='Pure formula and contract mutations only')
    args = parser.parse_args()
    samples, mutations = sweep(), mutation_checks()
    if not args.self_test:
        for scale in (1, 2):
            canonical = E.parse(str(ROOT / f'skins/need-for-speed-underground/vlc-{scale}x/theme.xml')).getroot()
            with zipfile.ZipFile(ROOT / f'dist/Need-for-Speed-Underground-{scale}x.vlt') as archive:
                packaged = E.fromstring(archive.read('theme.xml'))
            verify_theme(canonical)
            verify_theme(packaged)
            assert E.tostring(canonical, method='c14n') == E.tostring(packaged, method='c14n'), 'Package XML differs from canonical theme'
            print(f'PASS {scale}x: native magnet=15 retained, packaged XML matches; {len(packaged.findall(".//Anchor"))} explicit docking anchors')
    print(f'PASS {samples} edge-sweep samples, {mutations} rejected contract mutations; offline only')
    print('Scope: intended work-area snapping only. Pane docking, native repaint stutter and monitor selection require separate evidence.')


if __name__ == '__main__':
    main()
