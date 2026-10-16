"""Check fresh theme placement against declared work areas without launching VLC.

Saved VLC layouts and smaller work areas are outside this default-position
contract. Window overlap is allowed; local controls must remain inside them.
"""
from assets import ThemeAssets
from build import SKIN


WORK_AREAS = {1: (1280, 720), 2: (1920, 1040)}
EFFECT_KEYS = ('button', 'shutter', 'intro', 'info', 'logo')


def verify(assets, scale):
    screen_width, screen_height = WORK_AREAS[scale]
    count = 0
    windows = assets.tree.findall('Window')
    expected = {'main', 'tracks', 'equalizer', 'info', 'video', 'palette_state',
                'fullscreenController', 'videoHoverController', 'nfs_hover_command'}
    expected.update('nfs_fx_'+key for key in EFFECT_KEYS)
    assert {w.get('id') for w in windows} == expected
    for window in windows:
        wx, wy = int(window.get('x')), int(window.get('y'))
        key = window.get('id')
        if key == 'fullscreenController':
            assert (wx, wy, window.get('visible')) == (0, 0, 'false')
            assert len(window) == 1
            assert (int(window[0].get('width')), int(window[0].get('height'))) == (425*scale, 146*scale)
        offscreen = key == 'videoHoverController' or key == 'nfs_hover_command' or key.startswith('nfs_fx_')
        if offscreen:
            if key == 'videoHoverController':
                position = (-31000, -30800)
                layout_sizes = {'video_hover_controls': (426*scale, 146*scale), 'video_hover_closed': (427*scale, scale)}
                default_layout = 'video_hover_closed'
            elif key == 'nfs_hover_command':
                position = (-31000, -30900)
                layout_sizes = {'nfs_hover_command_layout': (67, 17)}
                default_layout = 'nfs_hover_command_layout'
            else:
                effect = key.removeprefix('nfs_fx_')
                position = (-31000, -31000)
                layout_sizes = {key+'_ready': (41+EFFECT_KEYS.index(effect), 17), key+'_trigger': (51+EFFECT_KEYS.index(effect), 17)}
                default_layout = key+('_trigger' if effect == 'intro' else '_ready')
            assert (wx, wy) == position, (key, 'Offscreen command sentinel moved')
            assert window.get('visible') == 'true', 'Commands must switch layouts rather than show a window during input'
            assert window.get('dragdrop') == window.get('playondrop') == 'false'
            assert len(window) == len(layout_sizes)
            assert {layout.get('id') for layout in window} == set(layout_sizes)
            assert window[-1].get('id') == default_layout
            if key == 'videoHoverController':
                closed = window.find('Layout[@id="video_hover_closed"]')
                assert len(closed) == 1 and closed[0].tag == 'Image'
                assert assets.frame(closed[0].get('image')).getchannel('A').getbbox() is None, 'Closed hover window must be transparent and noninteractive'
        for layout in window.findall('Layout'):
            width, height = int(layout.get('width')), int(layout.get('height'))
            if offscreen:
                assert (width, height) == layout_sizes[layout.get('id')]
                assert wx+width < 0 and wy+height < 0, 'Helper could intercept workspace input at its default position'
            else:
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
        print(f'PASS {scale}x: panes/native fullscreen defaults fit {WORK_AREAS[scale]}; helper sentinels stay offscreen; {count} critical control instances contained')


if __name__ == '__main__':
    main()
