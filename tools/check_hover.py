"""Check native/companion controller artwork and controls without launching VLC.

The native fullscreenController name selects VLC's borderless mouse-motion
handler. XML has no windowed-video hover event; videoHoverController requires
the companion. Geometry/hit checks do not prove native timing or HWND behavior.
"""
import argparse
from copy import deepcopy
from types import MethodType
import zipfile

from lxml import etree as E
from assets import ThemeAssets
from build import Builder, ROOT, SKIN, SOURCE
from check_panels import verify as verify_hits
from check_source_art import ART_ATTRIBUTES, compare, scaled, source_pixels, verify_video_backing_pixels
from skin_support import playback_action


CONTROLLERS = {'fullscreenController': ('fullscreen_controls', 425, 0, 0),
               'videoHoverController': ('video_hover_controls', 426, -31000, -30800)}


def verify(assets, scale):
    layouts = []
    for window_id, (layout_id, width, x, y) in CONTROLLERS.items():
        windows = assets.tree.findall(f'Window[@id="{window_id}"]')
        assert len(windows) == 1, (window_id, 'Controller missing or duplicated')
        window = windows[0]
        companion = window_id == 'videoHoverController'
        assert window.get('visible') == ('true' if companion else 'false'), 'Companion must switch layouts without native show/focus'
        assert (int(window.get('x')), int(window.get('y'))) == (x, y)
        assert window.get('dragdrop') == window.get('playondrop') == 'false'
        assert len(window) == (2 if companion else 1)
        if companion:
            closed = window[-1]
            assert closed.tag == 'Layout' and closed.get('id') == 'video_hover_closed', 'Transparent layout must be the initial last layout'
            assert (int(closed.get('width')), int(closed.get('height'))) == (427*scale, scale)
            assert len(closed) == 1 and closed[0].tag == 'Image'
            marker = closed[0]
            assert marker.get('image') == 'hover_closed_marker'
            assert (marker.get('x'),marker.get('y'),marker.get('width'),marker.get('height')) == ('0','0','1','1')
            assert marker.get('action','none') == marker.get('action2','none') == 'none'
            image = assets.image('hover_closed_marker')
            assert image.size == (1,1) and image.tobytes() == bytes(4), 'Closed controller must have no visible or clickable pixel'
        layout = window[0]
        layouts.append(layout)
        assert layout.tag == 'Layout' and layout.get('id') == layout_id
        size = int(layout.get('width')), int(layout.get('height'))
        assert size == (width*scale, 146*scale)
        for name, value in [('minwidth', size[0]), ('maxwidth', size[0]),
                            ('minheight', size[1]), ('maxheight', size[1])]:
            assert int(layout.get(name, value)) == value, 'Controller must remain fixed size'
        assert layout.find('.//Video') is None, 'Controller must not create another video output'
        assert not layout.findall('.//Image[@action="resizeSE"]')
        buttons = layout.findall('Button')
        assert len(buttons) == 5
        expected = {'m_prev': 'playlist.previous()', 'm_next': 'playlist.next()',
                    'm_stop': 'vlc.stop()', 'vid_zoom': 'vlc.fullscreen()',
                    'm_close': 'videoHoverController.setLayout(video_hover_closed)' if companion else window_id+'.hide()'}
        for prefix, action in expected.items():
            matches = [b for b in buttons if b.get('up') == prefix+'_no_png']
            assert len(matches) == 1, (window_id, prefix)
            actual = matches[0].get('action', '')
            # Closing has no original click sound. Other transport controls
            # retain their full action after only approved leading signals.
            assert (actual if prefix == 'm_close' else playback_action(actual)) == action, (window_id, prefix)
            for attr, suffix in [('up','no'), ('over','hov'), ('down','do')]:
                assert matches[0].get(attr) == prefix+'_'+suffix+'_png'
        checks = layout.findall('Checkbox')
        assert len(checks) == 1
        play = checks[0]
        assert (play.get('state'), playback_action(play.get('action1', '')), playback_action(play.get('action2', ''))) == (
            'vlc.isPlaying', 'vlc.play()', 'vlc.pause()')
        for state, prefix in [('1','m_play'), ('2','m_pause')]:
            for attr, suffix in [('up','no'), ('over','hov'), ('down','do')]:
                assert play.get(attr+state) == prefix+'_'+suffix+'_png'
        sliders = layout.findall('Slider')
        assert len(sliders) == 2
        for variable, length in [('time',329), ('volume',85)]:
            matches = [s for s in sliders if s.get('value') == variable]
            assert len(matches) == 1
            slider = matches[0]
            assert slider.get('points') == f'(0,0),({length*scale},0)', 'Slider must increase left to right'
            assert slider.get('up') == 'eq_thumb2_png' and slider.get('down') == 'eq_thumb2_do_png'
            assert int(slider.get('thickness')) == 8*scale
            assert slider.get('visible', 'true') == 'true'
        for node in layout.findall('Text'):
            expected_gate = layout_id+'.isActive' if companion else window_id+'.isVisible'
            assert node.get('visible') == expected_gate, 'Hidden controller text must stop rasterizing'
            assert node.get('focus') == 'false', 'Labels must not steal transport/slider hits'
        for node in layout:
            key = node.get('image') or node.get('up') or node.get('up1')
            if not key or node.tag == 'Slider':
                continue
            image = assets.image(key)
            right = int(node.get('x',0))+int(node.get('width',image.width))
            bottom = int(node.get('y',0))+int(node.get('height',image.height))
            assert right <= 425*scale and bottom <= 146*scale, 'Artwork fills companion identification margin or escapes controller'
        verify_video_backing_pixels(assets, layout, scale)
        for color in range(1, 8):
            for prefix in ('m_close','vid_zoom'):
                backing = layout.find(f'Image[@image="video_{prefix}_backing_{color}"]')
                button = layout.find(f'Button[@up="{prefix}_no_png"]')
                header = layout.find(f'Image[@image="eq_top_right_{color}_png"]')
                assert backing.get('visible') == header.get('visible') == f'palette_{color}.isActive'
                assert layout.index(header) < layout.index(backing) < layout.index(button)
                assert (backing.get('x'), backing.get('y')) == (button.get('x'), button.get('y'))
            for checked in (False, True):
                assert verify_hits(assets, layout, color, size, checked, scale) == 6
        rails = layout.findall('Image[@image="hover_rail"]')
        assert len(rails) == 2 and all(n.get('resize') == 'scale' for n in rails)
        # Check all retained feedback and frame pixels against independent
        # source decoding, rather than against another generated controller.
        keys = {node.get(attr) for node in layout for attr in ART_ATTRIBUTES if node.get(attr)}
        for key in keys:
            source = SOURCE/(key[:-4]+'.png') if key.endswith('_png') else None
            if source is not None and source.exists():
                compare(assets, key, source_pixels(source), scale)
        for key, box in [('hover_carbon',(200,90,220,106)), ('hover_rail',(198,18,268,25))]:
            compare(assets, key, source_pixels(SOURCE/'eq_back.png').crop(box), scale)
    # The companion adds only one transparent column (two at2x). Visual/control
    # geometry remains identical; only IDs, text gates and close targets differ.
    normalized = []
    for layout in layouts:
        clone = deepcopy(layout)
        clone.set('width', str(425*scale))
        for node in clone.iter():
            node.attrib.pop('id', None)
            for attr in ('visible','action'):
                if node.get(attr):
                    value = node.get(attr).replace('videoHoverController.setLayout(video_hover_closed)','controller.hide()')
                    value = value.replace('video_hover_controls.isActive','controller.isVisible')
                    node.set(attr, value.replace('videoHoverController','controller').replace('fullscreenController','controller'))
        normalized.append(E.tostring(clone, method='c14n'))
    assert normalized[0] == normalized[1], 'Controller artwork or behavior diverged'


def mutations(assets, scale):
    original = assets.tree
    for failure in ('name', 'visible', 'play', 'slider', 'overlap', 'palette', 'tile', 'unknown-signal', 'trailing-signal', 'closed-paint', 'closed-order'):
        assets.tree = deepcopy(original)
        window = assets.tree.find('Window[@id="fullscreenController"]')
        layout = window[0]
        if failure == 'name': window.set('id','fullscreen_controller')
        elif failure == 'visible': window.set('visible','true')
        elif failure == 'play': layout.find('Checkbox').set('action2','vlc.stop()')
        elif failure == 'slider': layout.find('Slider').set('points',f'({329*scale},0),(0,0)')
        elif failure == 'overlap':
            stop = layout.find('Button[@up="m_stop_no_png"]')
            play = layout.find('Checkbox')
            stop.set('x',play.get('x')); stop.set('y',play.get('y'))
        elif failure == 'palette':
            layout.find('Image[@image="video_vid_zoom_backing_1"]').set('visible','palette_2.isActive')
        elif failure == 'tile': layout.find('Image[@image="hover_rail"]').set('resize','mosaic')
        elif failure == 'closed-paint':
            assets.tree.find('.//Layout[@id="video_hover_closed"]/Image').set('image','hover_carbon')
        elif failure == 'closed-order':
            companion = assets.tree.find('Window[@id="videoHoverController"]')
            companion.append(companion[0])
        else:
            previous = layout.find('Button[@up="m_prev_no_png"]')
            previous.set('action', 'nfs_fx_unknown.show();playlist.previous()' if failure == 'unknown-signal'
                         else 'playlist.previous();nfs_fx_button.show()')
        try:
            verify(assets, scale)
        except AssertionError:
            pass
        else:
            raise AssertionError(f'Unsafe {failure} mutation escaped')
        finally:
            assets.tree = original


def memory_assets(scale):
    """Exercise the builder without its constructor, output writes or packaging."""
    builder = Builder.__new__(Builder)
    builder.scale = scale
    builder.theme = E.Element('Theme', version='2.0')
    E.SubElement(builder.theme,'ThemeInfo')
    for font, size in [('ui',10),('small',8)]:
        E.SubElement(builder.theme,'Font',id=font,file='unused.ttf',size=str(size*scale))
    builder.ids = {}
    images = {}
    def bitmap(self, name, im=None, frames=1, fps=0, loop=0, gridframes=1, prescaled=False):
        assert frames == gridframes == 1, 'Hover controller must use static art'
        key = name.replace('.','_')
        if key not in images:
            im = source_pixels(SOURCE/name) if im is None else im
            images[key] = im if prescaled else scaled(im,scale)
            self.ids[key] = images[key].size
        return key
    builder.bitmap = MethodType(bitmap,builder)
    builder.hover_controllers()
    assets = ThemeAssets.__new__(ThemeAssets)
    assets.tree = E.ElementTree(builder.theme)
    assets.resources = {n.get('id'):n for n in builder.theme.iter() if n.get('id')}
    assets.image = lambda key: images[key]
    assets.frame = lambda key, frame=0, count=None: images[key]
    return assets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true', help='Check builder output entirely in memory before a package rebuild')
    args = parser.parse_args()
    for scale in (1,2):
        assets = memory_assets(scale) if args.self_test else ThemeAssets(SKIN/f'vlc-{scale}x')
        if not args.self_test:
            with zipfile.ZipFile(ROOT/'dist'/f'Need-for-Speed-Underground-{scale}x.vlt') as package:
                packaged = E.fromstring(package.read('theme.xml'))
                assert E.tostring(packaged,method='c14n') == E.tostring(assets.tree,method='c14n'), 'Packaged hover controls differ from audited XML'
        verify(assets,scale)
        mutations(assets,scale)
        print(f'PASS {scale}x: native/companion bars, transparent closed default, source art, 28 palette/play states, transport/slider hits and 11 rejected mutations; '+('memory only' if args.self_test else 'package XML matches'))


if __name__ == '__main__':
    main()
