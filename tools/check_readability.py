"""Guard the approved filename readability adaptation without running VLC.

Geometry and contrast are offline contracts, not native font/scroll evidence.
Original neighboring artwork and input coverage are checked by source/hit tests.
"""
import argparse
from copy import deepcopy
from pathlib import Path

from assets import ThemeAssets

ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / 'skins/need-for-speed-underground'


def luminance(rgb):
    values = [v / 255 for v in rgb]
    return sum(c * (v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
               for c, v in zip((.2126, .7152, .0722), values))


def verify(assets, scale):
    font = assets.resources['metadata']
    assert font.tag == 'Font' and font.get('size') == str(12 * scale)
    assert font.get('file') == 'assets/FreeSans.ttf'
    backing = assets.image('metadata_backing')
    assert backing.size == (177 * scale, 16 * scale)
    assert backing.getchannel('A').getextrema() == (255, 255), 'Backing must survive cached RGB copy'
    assert backing.getpixel((backing.width // 2, backing.height // 2)) == (8, 13, 17, 255)
    # Borders must stay subdued enough for white text even during scrolling.
    worst = max(luminance(backing.getpixel((x, y))[:3])
                for y in range(backing.height) for x in range(backing.width))
    assert 1.05 / (worst + .05) >= 7, 'White text contrast fell below 7:1'
    assert backing.getpixel((backing.width // 2, 0)) != (8, 13, 17, 255)
    assert backing.getpixel((backing.width // 2, backing.height - 1)) != (8, 13, 17, 255)
    count = 0
    main = assets.tree.find('Window[@id="main"]')
    for layout in main:
        lid = layout.get('id')
        if lid == 'main_start':
            continue
        text = layout.findall('Text[@text="$N"]')
        images = layout.findall('Image[@image="metadata_backing"]')
        if '_closed' in lid:
            assert not text and not images, 'Closed shutter must retain original interior'
            continue
        assert len(text) == len(images) == 1, (lid, 'Missing/duplicated metadata')
        text, image = text[0], images[0]
        expected = {'x': 62 * scale, 'y': 117 * scale, 'width': 177 * scale}
        assert all(text.get(k) == str(v) for k, v in expected.items()), lid
        for key, value in {'font': 'metadata', 'color': '#FFFFFF', 'scrolling': 'auto',
                           'focus': 'false', 'visible': lid + '.isActive'}.items():
            assert text.get(key) == value, (lid, key)
        assert (image.get('x'), image.get('y')) == (str(62 * scale), str(117 * scale))
        assert int(image.get('width', backing.width)) == backing.width
        assert int(image.get('height', backing.height)) == backing.height
        assert layout.index(image) < layout.index(text), 'Backing covers filename'
        assert image.get('action', 'none') == image.get('action2', 'none') == 'none'
        logo = layout.find('Button[@up="m_logo_no_png"]')
        assert logo is not None
        assert int(image.get('y')) + backing.height < int(logo.get('y')), 'Backing overlaps source logo'
        assert layout.index(text) < layout.index(logo), 'Retained logo must remain accessible'
        count += 1
    assert count == 42, ('Nonclosed metadata layout coverage', count)
    return count


def mutations(assets, scale):
    original_tree, original_resources = assets.tree, assets.resources
    for defect in ('font', 'color', 'focus', 'position', 'gate', 'backing-order'):
        try:
            assets.tree = deepcopy(original_tree)
            assets.resources = {n.get('id'): n for n in assets.tree.iter() if n.get('id')}
            layout = assets.tree.find('Window[@id="main"]/Layout[@id="main_1"]')
            text = layout.find('Text[@text="$N"]')
            if defect == 'font': assets.resources['metadata'].set('size', str(8 * scale))
            elif defect == 'color': text.set('color', '#777777')
            elif defect == 'focus': text.set('focus', 'true')
            elif defect == 'position': layout.find('Image[@image="metadata_backing"]').set('y', str(134 * scale))
            elif defect == 'gate': text.set('visible', 'true')
            else: layout.append(layout.find('Image[@image="metadata_backing"]'))
            try:
                verify(assets, scale)
            except AssertionError:
                continue
            raise AssertionError('Readability mutation escaped: ' + defect)
        finally:
            assets.tree, assets.resources = original_tree, original_resources
    return 6


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true', help='Also reject six changed-contract fixtures per scale')
    args = parser.parse_args()
    for scale in (1, 2):
        assets = ThemeAssets(SKIN / f'vlc-{scale}x')
        count = verify(assets, scale)
        rejected = mutations(assets, scale) if args.self_test else 0
        print(f'PASS {scale}x: {count} filename layouts, opaque backing, white 12x-scale font, contrast and logo separation; {rejected} mutations rejected')


if __name__ == '__main__':
    main()
