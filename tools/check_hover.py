"""Offline compact-controller contracts; no VLC or desktop interaction.

Physical geometry, original pixels and hit tests do not certify native timing
or stacking. External framed-bar placement leaves wheel targeting origin stale.
"""
import argparse
from copy import deepcopy
from types import MethodType
import zipfile

from lxml import etree as E
from PIL import Image, ImageDraw

from assets import ThemeAssets, visible
from build import Builder, ROOT, SKIN, SOURCE
from check_panels import verify as verify_hits
from check_source_art import source_pixels, scaled
from skin_support import playback_action


CONTROLLERS = {'fullscreenController': ('fullscreen_controls', 360, 0, 0),
               'videoHoverController': ('video_hover_controls', 361, -31000, -30800)}
TRANSPORT = {'m_prev': (8, 27, 'playlist.previous()'),
             'm_stop': (76, 27, 'vlc.stop()'),
             'm_next': (110, 27, 'playlist.next()'),
             'vid_zoom': (312, 33, 'vlc.fullscreen()')}
EXPANDED = 'hover_volume_expanded.isActive'


def xy(node):
    return int(node.get('x', 0)), int(node.get('y', 0))


def volume_icon_pixels(icon, state):
    """Independent geometry oracle: centered glyph, unchanged circular backing."""
    colors = {'no': ((14,22,29),(62,76,85),(194,220,234)),
              'hov': ((20,34,43),(32,174,221),(242,250,255)),
              'do': ((8,14,20),(32,174,221),(242,250,255))}
    fill, outline, glyph = colors[state]
    assert icon.size == (23,23)
    backing = Image.new('RGBA', icon.size)
    ImageDraw.Draw(backing).ellipse((1,1,21,21), fill=fill+(255,), outline=outline+(255,))
    assert icon.getchannel('A').tobytes() == backing.getchannel('A').tobytes(), 'Speaker must retain circular hit footprint'
    inner = Image.new('L', icon.size)
    ImageDraw.Draw(inner).ellipse((3,3,19,19), fill=255)
    mask = Image.new('L', icon.size)
    for y in range(23):
        for x in range(23):
            pixel = icon.getpixel((x,y))
            if pixel == glyph+(255,):
                assert inner.getpixel((x,y)), ('Speaker glyph touches circular ring', state, x, y)
                mask.putpixel((x,y),255)
            else:
                assert pixel == backing.getpixel((x,y)), ('Speaker backing changed', state, x, y)
    assert mask.getbbox() == (3,5,20,18), ('Speaker glyph must center on (11,11)', state, mask.getbbox())
    return mask


def exact_image(assets, key, expected):
    actual = assets.image(key)
    assert actual.size == expected.size and actual.tobytes() == expected.tobytes(), (key, 'pixels changed')


def source_feedback(assets, node, prefix, state=''):
    for attr, suffix in [('up', 'no'), ('over', 'hov'), ('down', 'do')]:
        key = f'compact_{prefix}_{suffix}_png'
        assert node.get(attr+state) == key, (prefix, attr+state)
        exact_image(assets, key, source_pixels(SOURCE/f'{prefix}_{suffix}.png'))


def expected_carbon():
    image = Image.new('RGBA', (360, 64))
    image.paste((13,17,21,255), (0,0,360,64))
    alpha = Image.new('L', image.size)
    ImageDraw.Draw(alpha).rounded_rectangle((0, 0, 359, 63), radius=10, fill=255)
    image.putalpha(alpha)
    ImageDraw.Draw(image).rounded_rectangle((0, 0, 359, 63), radius=10, outline=(59, 72, 80, 255))
    return image


def flat_background_pixels(image):
    # Check a broad interior independently of the rounded-outline recipe.
    # Every source row/column, including the former 16px seams, must be flat.
    assert image.size == (360,64)
    interior = image.crop((12,2,348,62))
    assert interior.getextrema() == ((13,13),(17,17),(21,21),(255,255)), 'Compact background must have no grain, stripes or alpha modulation'


def transparent_layout(assets, layout, identifier, size):
    assert layout.tag == 'Layout' and layout.get('id') == identifier
    assert (int(layout.get('width')), int(layout.get('height'))) == size
    assert len(layout) == 1 and layout[0].tag == 'Image'
    marker = layout[0]
    assert xy(marker) == (0, 0)
    assert marker.get('width', '1') == marker.get('height', '1') == '1'
    assert marker.get('action', 'none') == marker.get('action2', 'none') == 'none'
    exact_image(assets, marker.get('image'), Image.new('RGBA', (1, 1)))


def state_hits(assets, layout, playing, expanded):
    """Resolve independent checkbox states before using the panel hit model."""
    clone = deepcopy(layout)
    flags = {'vlc.isPlaying': playing, EXPANDED: expanded,
             'fullscreenController.isVisible': True, 'video_hover_controls.isActive': True}
    for node in clone:
        node.set('visible', str(visible(node.get('visible'), flags=flags)).lower())
        if node.tag == 'Checkbox' and visible(node.get('state'), flags=flags):
            node.set('up1', node.get('up2'))
    assert verify_hits(assets, clone, 1, (int(layout.get('width')), 64), False, 1) == 7


def verify(assets, scale):
    volume_windows = assets.tree.findall('Window[@id="hover_volume_state"]')
    assert len(volume_windows) == 1
    volume_window = volume_windows[0]
    assert volume_window.get('visible') == 'true' and xy(volume_window) == (-31000, -30700)
    assert volume_window.get('dragdrop') == volume_window.get('playondrop') == 'false'
    assert len(volume_window) == 2
    transparent_layout(assets, volume_window[0], 'hover_volume_expanded', (72, 19))
    transparent_layout(assets, volume_window[1], 'hover_volume_collapsed', (71, 19))
    font = assets.tree.find('Font[@id="compactfont"]')
    assert font is not None and font.get('size') == '11', 'Compact font must not scale with main skin'
    flat_background_pixels(assets.image('compact_carbon'))
    exact_image(assets, 'compact_carbon', expected_carbon())
    rail_pixels = Image.new('RGBA', (1, 3))
    rail_pixels.putdata([(35, 114, 142, 255), (9, 22, 29, 255), (52, 76, 86, 255)])
    exact_image(assets, 'compact_rail', rail_pixels)
    layouts = []
    for window_id, (layout_id, width, x, y) in CONTROLLERS.items():
        windows = assets.tree.findall(f'Window[@id="{window_id}"]')
        assert len(windows) == 1
        window = windows[0]
        companion = window_id == 'videoHoverController'
        assert window.get('visible') == ('true' if companion else 'false')
        assert xy(window) == (x, y)
        assert window.get('dragdrop') == window.get('playondrop') == 'false'
        assert len(window) == (2 if companion else 1)
        if companion:
            transparent_layout(assets, window[-1], 'video_hover_closed', (362, 1))
        layout = window[0]
        layouts.append(layout)
        assert layout.get('id') == layout_id
        assert (int(layout.get('width')), int(layout.get('height'))) == (width, 64)
        for key, expected in [('minwidth', width), ('maxwidth', width), ('minheight', 64), ('maxheight', 64)]:
            assert int(layout.get(key, expected)) == expected
        assert layout.find('.//Video') is None and layout.find('Text[@text="$N"]') is None
        assert not layout.findall('.//Image[@action="resizeSE"]')
        background = layout.find('Image[@image="compact_carbon"]')
        assert background is not None and layout.index(background) == 0 and xy(background) == (0, 0)
        assert background.get('action') == ('none' if companion else 'move')
        if companion:
            assert not window.findall('.//Image[@action="move"]')
        buttons = layout.findall('Button')
        assert len(buttons) == 5
        expected_buttons = dict(TRANSPORT)
        expected_buttons['m_close'] = (334, 33, 'videoHoverController.setLayout(video_hover_closed)' if companion else 'fullscreenController.hide()')
        for prefix, (bx, by, action) in expected_buttons.items():
            matches = [n for n in buttons if n.get('up') == f'compact_{prefix}_no_png']
            assert len(matches) == 1
            node = matches[0]
            assert xy(node) == (bx, by)
            actual = node.get('action', '')
            assert (actual if prefix == 'm_close' else playback_action(actual)) == action
            source_feedback(assets, node, prefix)
        checks = layout.findall('Checkbox')
        assert len(checks) == 2
        play = layout.find('Checkbox[@state="vlc.isPlaying"]')
        assert play is not None and xy(play) == (42, 27)
        assert (playback_action(play.get('action1', '')), playback_action(play.get('action2', ''))) == ('vlc.play()', 'vlc.pause()')
        source_feedback(assets, play, 'm_play', '1')
        source_feedback(assets, play, 'm_pause', '2')
        volume = layout.find(f'Checkbox[@state="{EXPANDED}"]')
        assert volume is not None and xy(volume) == (232, 31)
        assert volume.get('action1') == 'hover_volume_state.setLayout(hover_volume_expanded)'
        assert volume.get('action2') == 'hover_volume_state.setLayout(hover_volume_collapsed)'
        for state in ('1', '2'):
            for attr, suffix in [('up', 'no'), ('over', 'hov'), ('down', 'do')]:
                key = f'compact_volume_{suffix}_png'
                assert volume.get(attr+state) == key
                icon = assets.image(key)
                assert icon.size == (23, 23) and set(icon.getchannel('A').tobytes()) == {0, 255}
                volume_icon_pixels(icon, suffix)
        assert len({assets.image(f'compact_volume_{s}_png').tobytes() for s in ('no', 'hov', 'do')}) == 3
        own_gate = layout_id+'.isActive' if companion else window_id+'.isVisible'
        texts = layout.findall('Text')
        assert len(texts) == 2
        time = layout.find('Text[@text="$t / $d"]')
        percent = layout.find('Text[@text="$V%"]')
        assert time is not None and xy(time) == (148, 33) and time.get('width') == '80'
        assert percent is not None and xy(percent) == (259, 34) and percent.get('width') == '46'
        assert time.get('visible') == own_gate
        for text in texts:
            assert text.get('font') == 'compactfont' and text.get('color') == '#FFFFFF'
            assert text.get('focus') == 'false' and text.get('scrolling') == 'none'
        sliders = layout.findall('Slider')
        assert len(sliders) == 2
        for variable, sx, sy, length in [('time', 12, 12, 336), ('volume', 264, 43, 40)]:
            slider = layout.find(f'Slider[@value="{variable}"]')
            assert slider is not None and xy(slider) == (sx, sy)
            assert slider.get('points') == f'(0,0),({length},0)' and slider.get('thickness') == '8'
            for attr, source in [('up', 'eq_thumb2.png'), ('down', 'eq_thumb2_do.png')]:
                key = 'compact_'+source.replace('.', '_')
                assert slider.get(attr) == key
                exact_image(assets, key, source_pixels(SOURCE/source))
        assert layout.find('Slider[@value="time"]').get('visible', 'true') == 'true'
        volume_slider = layout.find('Slider[@value="volume"]')
        rails = layout.findall('Image[@image="compact_rail"]')
        assert len(rails) == 2
        for rail, expected in zip(rails, [(12, 10, 336, 3), (264, 41, 40, 3)]):
            assert (*xy(rail), int(rail.get('width')), int(rail.get('height'))) == expected
            assert rail.get('resize') == 'scale'
        for expanded in (False, True):
            for own in (False, True):
                flags = {own_gate: own, EXPANDED: expanded}
                assert visible(percent.get('visible'), flags=flags) == (own and not expanded)
                assert visible(volume_slider.get('visible'), flags=flags) == (own and expanded)
                assert visible(rails[1].get('visible'), flags=flags) == (own and expanded)
            for playing in (False, True):
                state_hits(assets, layout, playing, expanded)
        for node in layout:
            key = node.get('image') or node.get('up') or node.get('up1')
            if key and node.tag != 'Slider':
                image = assets.image(key)
                assert xy(node)[0] >= 0 and xy(node)[1] >= 0
                assert xy(node)[0]+int(node.get('width', image.width)) <= 360
                assert xy(node)[1]+int(node.get('height', image.height)) <= 64
    normalized = []
    for layout in layouts:
        clone = deepcopy(layout)
        clone.set('width', '360')
        clone.set('minwidth', '360')
        clone.set('maxwidth', '360')
        for node in clone.iter():
            node.attrib.pop('id', None)
            if node.tag == 'Image' and node.get('image') == 'compact_carbon':
                node.set('action', 'none')
            for attr in ('visible', 'action'):
                if node.get(attr):
                    value = node.get(attr).replace('videoHoverController.setLayout(video_hover_closed)', 'controller.hide()')
                    value = value.replace('video_hover_controls.isActive', 'controller.isVisible')
                    node.set(attr, value.replace('fullscreenController', 'controller'))
        normalized.append(E.tostring(clone, method='c14n'))
    assert normalized[0] == normalized[1], 'Controller artwork or behavior diverged'


def mutations(assets, scale):
    original = assets.tree
    original_image = assets.image
    failures = ('name', 'visible', 'play', 'slider', 'overlap', 'tile', 'signal', 'closed-order',
                'helper-drag', 'scaled-size', 'volume-state', 'volume-gate', 'text-focus',
                'closed-paint', 'carbon-pixel', 'thumb-pixel', 'speaker-offset', 'speaker-ring', 'carbon-stripe')
    for failure in failures:
        assets.tree = deepcopy(original)
        window = assets.tree.find('Window[@id="fullscreenController"]')
        layout = window[0]
        if failure == 'name': window.set('id', 'fullscreen_controller')
        elif failure == 'visible': window.set('visible', 'true')
        elif failure == 'play': layout.find('Checkbox').set('action2', 'vlc.stop()')
        elif failure == 'slider': layout.find('Slider').set('points', '(336,0),(0,0)')
        elif failure == 'overlap': layout.find('Button').set('x', '42')
        elif failure == 'tile': layout.find('Image[@x="12"]').set('resize', 'mosaic')
        elif failure == 'signal': layout.find('Button').set('action', 'nfs_fx_unknown.show();playlist.previous()')
        elif failure == 'closed-order':
            companion = assets.tree.find('Window[@id="videoHoverController"]')
            companion.append(companion[0])
        elif failure == 'helper-drag': assets.tree.find('.//Layout[@id="video_hover_controls"]/Image').set('action', 'move')
        elif failure == 'scaled-size': layout.set('width', '720')
        elif failure == 'volume-state':
            volume = assets.tree.find('Window[@id="hover_volume_state"]')
            volume.append(volume[0])
        elif failure == 'volume-gate': layout.find('Slider[@value="volume"]').set('visible', 'true')
        elif failure == 'text-focus': layout.find('Text').set('focus', 'true')
        elif failure == 'closed-paint':
            assets.tree.find('.//Layout[@id="video_hover_closed"]/Image').set('image', 'compact_carbon')
        elif failure in ('speaker-offset', 'speaker-ring'):
            def corrupt_speaker(key):
                image = original_image(key)
                if key == 'compact_volume_no_png':
                    image = image.copy()
                    glyph = (194,220,234,255)
                    if failure == 'speaker-ring':
                        image.putpixel((20,11),glyph)
                    else:
                        points = [(x,y) for y in range(23) for x in range(23) if image.getpixel((x,y)) == glyph]
                        for x,y in points: image.putpixel((x,y),(14,22,29,255))
                        for x,y in points: image.putpixel((x+1,y),glyph)
                return image
            assets.image = corrupt_speaker
        elif failure == 'carbon-stripe':
            def striped_image(key):
                image = original_image(key)
                if key == 'compact_carbon':
                    image = image.copy()
                    ImageDraw.Draw(image).line((12,16,347,16), fill=(14,18,22,255))
                return image
            assets.image = striped_image
        elif failure in ('carbon-pixel', 'thumb-pixel'):
            corrupt_key = 'compact_carbon' if failure == 'carbon-pixel' else 'compact_eq_thumb2_png'
            def corrupt_image(key):
                image = original_image(key)
                if key == corrupt_key:
                    image = image.copy()
                    r, g, b, a = image.getpixel((0, 0))
                    image.putpixel((0, 0), (r ^ 1, g, b, a))
                return image
            assets.image = corrupt_image
        try:
            verify(assets, scale)
        except AssertionError:
            pass
        else:
            raise AssertionError(f'Unsafe {failure} mutation escaped')
        finally:
            assets.tree = original
            assets.image = original_image
    return len(failures)


def memory_assets(scale):
    """Exercise the compact builder without output files or packaging."""
    builder = Builder.__new__(Builder)
    builder.scale = scale
    builder.theme = E.Element('Theme', version='2.0')
    E.SubElement(builder.theme, 'ThemeInfo')
    builder.ids = {}
    images = {}
    def bitmap(self, name, im=None, frames=1, fps=0, loop=0, gridframes=1, prescaled=False):
        assert frames == gridframes == 1
        key = name.replace('.', '_')
        if key not in images:
            im = source_pixels(SOURCE/name) if im is None else im
            images[key] = im if prescaled else scaled(im, scale)
            self.ids[key] = images[key].size
        return key
    builder.bitmap = MethodType(bitmap, builder)
    builder.hover_controllers()
    assets = ThemeAssets.__new__(ThemeAssets)
    assets.tree = E.ElementTree(builder.theme)
    assets.resources = {n.get('id'): n for n in builder.theme.iter() if n.get('id')}
    assets.image = lambda key: images[key]
    assets.frame = lambda key, frame=0, count=None: images[key]
    return assets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    for scale in (1, 2):
        assets = memory_assets(scale) if args.self_test else ThemeAssets(SKIN/f'vlc-{scale}x')
        if not args.self_test:
            with zipfile.ZipFile(ROOT/'dist'/f'Need-for-Speed-Underground-{scale}x.vlt') as package:
                assert E.tostring(E.fromstring(package.read('theme.xml')), method='c14n') == E.tostring(assets.tree, method='c14n')
        verify(assets, scale)
        count = mutations(assets, scale)
        print(f'PASS {scale}x: physical compact bars, original 1x feedback, volume states, 8 playback/volume hit states, {count} rejected mutations; '+('memory only' if args.self_test else 'package XML matches'))
    print('Coverage limit: offline geometry/art checks do not certify native behavior; companion wheel targeting retains VLC\'s stale internal origin.')


if __name__ == '__main__':
    main()
