"""Check fresh theme placement against declared work areas without launching VLC.

Saved VLC layouts and smaller work areas are outside this default-position
contract. Window overlap is allowed; local controls must remain inside them.
"""
from assets import ThemeAssets
from build import SKIN


WORK_AREAS = {1: (1280, 720), 2: (1920, 1040)}


def verify(assets, scale):
    screen_width, screen_height = WORK_AREAS[scale]
    count = 0
    windows = assets.tree.findall('Window')
    assert {w.get('id') for w in windows} == {'main', 'tracks', 'equalizer', 'info', 'video','palette_state'}
    for window in windows:
        wx, wy = int(window.get('x')), int(window.get('y'))
        for layout in window.findall('Layout'):
            width, height = int(layout.get('width')), int(layout.get('height'))
            assert wx >= 0 and wy >= 0 and wx+width <= screen_width and wy+height <= screen_height, (scale, window.get('id'), 'default outside work area')
            for node in layout:
                if node.tag not in ('Button', 'Checkbox') and not (node.tag == 'Image' and node.get('action') == 'resizeSE'):
                    continue
                if node.get('id', '').startswith('decorative_'):
                    continue
                keys = [node.get('image')] if node.tag == 'Image' else [node.get('up')] if node.tag == 'Button' else [node.get('up1'), node.get('up2')]
                x, y = int(node.get('x', 0)), int(node.get('y', 0))
                for key in keys:
                    im = assets.frame(key)
                    assert x >= 0 and y >= 0 and x+im.width <= width and y+im.height <= height, (scale, layout.get('id'), node.get('id'), 'control outside own window')
                count += 1
    return count


def main():
    for scale in (1, 2):
        assets = ThemeAssets(SKIN/f'vlc-{scale}x')
        count = verify(assets, scale)
        print(f'PASS {scale}x: 5 pane defaults and hidden palette state fit {WORK_AREAS[scale]}, {count} critical control instances contained')


if __name__ == '__main__':
    main()
