"""Offline embedded-video sizing contract, including packaged XML.

VLC 3.0.23 CtrlVideo gates media-driven layout resizing on autoresize, while
onResize still follows manual layout resizing. These checks establish skin
geometry and policy only; they do not establish native aspect fit, decoding,
fullscreen restoration, visibility behavior, or pixel-level video placement.
"""
from copy import deepcopy
import zipfile

from lxml import etree as E

from assets import ThemeAssets, visible
from build import ROOT, SKIN, SOURCE
from check_panels import geometry
from check_source_art import verify_video_backing_pixels


def intersects(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx+bw and bx < ax+aw and ay < by+bh and by < ay+ah


def verify_policy(tree):
    fills = tree.findall('.//Image[@image="screen_black"]')
    assert len(fills) == 2 and all(node.get('resize') == 'scale' for node in fills), 'Solid fills must not tile once per pixel on native repaint'
    videos = tree.findall('.//Video')
    assert len(videos) == 1, 'Keep one embedded viewport across all palettes'
    video = videos[0]
    assert video.getparent().getparent().get('id') == 'video'
    assert video.get('visible', 'true') == 'true', 'Viewport must become eligible when its window is shown'
    # Omission is unsafe: the official DTD and parser default this to true.
    assert video.get('autoresize') == 'false', 'Media dimensions must not resize the skin window'
    assert video.get('lefttop', 'lefttop') == 'lefttop' and video.get('rightbottom') == 'rightbottom'
    assert video.get('xkeepratio', 'false') == video.get('ykeepratio', 'false') == 'false'
    return video


def verify_header(layout, scale, assets):
    verify_video_backing_pixels(assets, layout, scale)
    source = E.fromstring((SOURCE/'nfs.wms').read_bytes(), E.XMLParser(recover=True)).find('view[@id="videoView"]')
    width = int(layout.get('width'))
    headers = []
    for color in range(1, 8):
        original = source.find(f'subview[@id="vid7_{color}"]')
        key = original.get('backgroundImage').replace('.', '_')
        assert key == f'eq_top_right_{color}_png', 'Source video header has two button recesses'
        found = layout.findall(f'Image[@image="{key}"]')
        assert len(found) == 1, (color, 'Missing source video header')
        header = found[0]
        assert header.get('lefttop') == header.get('rightbottom') == 'righttop'
        assert (int(header.get('x')), int(header.get('y', 0))) == (width-164*scale, 0)
        for active in range(1, 8):
            assert visible(header.get('visible'), f'main_{active}') == (active == color)
        headers.append(header)
    backings = []
    for prefix in ('m_close', 'vid_zoom'):
        original = source.find(f'subview[@backgroundImage="{prefix}_no.png"]')
        assert original is not None and original.find(f'button[@image="{prefix}_no.png"]') is not None
        key = prefix+'_no_png'
        buttons = [node for node in layout if node.tag in ('Button','Checkbox') and (node.get('up') or node.get('up1')) == key]
        assert len(buttons) == 1, (prefix, 'Retain one original functional button')
        button = buttons[0]
        offset = int(original.get('left').rsplit('-', 1)[1])
        expected = width-offset*scale, int(original.get('top', 0))*scale
        assert (int(button.get('x')), int(button.get('y'))) == expected
        assert button.get('lefttop') == button.get('rightbottom') == 'righttop'
        for color in range(1, 8):
            images = layout.findall(f'Image[@image="video_{prefix}_backing_{color}"]')
            assert len(images) == 1, (prefix, color, 'Retain the native-scale source composite')
            backing = images[0]
            assert (int(backing.get('x')), int(backing.get('y'))) == expected
            assert backing.get('lefttop') == backing.get('rightbottom') == 'righttop'
            assert backing.get('visible') == headers[color-1].get('visible') == f'palette_{color}.isActive'
            for active in range(1, 8):
                assert visible(backing.get('visible'), f'main_{active}') == (active == color)
            assert max(layout.index(header) for header in headers) < layout.index(backing) < layout.index(button), (prefix, color, 'Header/backing/button draw order changed')
            backings.append(backing)
    return backings


def verify_zoom_controls(tree):
    controls = []
    for layout in tree.findall('.//Window[@id="main"]/Layout'):
        matches = [node for node in layout if (node.get('up') or node.get('up1')) == 'm_full_no_png']
        assert len(matches) == 1
        controls.append((matches[0], 'm_full', 'video.show();'))
    pane = tree.find('.//Window[@id="video"]/Layout')
    matches = [node for node in pane if (node.get('up') or node.get('up1')) == 'vid_zoom_no_png']
    assert len(matches) == 1
    controls.append((matches[0], 'vid_zoom', ''))
    for node, prefix, lead in controls:
        assert node.tag == 'Checkbox' and node.get('state') == 'video.isMaximized', 'Framed maximize must expose its restore state'
        assert node.get('action1') == lead+'video.maximize()'
        assert node.get('action2') == lead+'video.unmaximize()', 'Second click must restore rather than maximize again'
        for state in (1, 2):
            for attr, suffix in (('up', 'no'), ('over', 'hov'), ('down', 'do')):
                assert node.get(attr+str(state)) == prefix+'_'+suffix+'_png', (prefix, state, 'Original feedback was changed')
    return controls


def verify_geometry(assets, scale):
    video = verify_policy(assets.tree)
    layout = video.getparent()
    backings = verify_header(layout, scale, assets)
    original = int(layout.get('width')), int(layout.get('height'))
    minimum = int(layout.get('minwidth')), int(layout.get('minheight'))
    maximum = int(layout.get('maxwidth')), int(layout.get('maxheight'))
    assert minimum[0] <= original[0] <= maximum[0] and minimum[1] <= original[1] <= maximum[1]
    assert maximum[0] >= 8192 and maximum[1] >= 4320, 'Framed maximize must not stop at the previous 3000x2000 cap'
    handles = layout.findall('Image[@action="resizeSE"]')
    assert len(handles) == 7, 'Manual resizing must remain available in every palette'
    for handle in handles:
        assert handle.get('lefttop') == handle.get('rightbottom') == 'rightbottom'
        alpha = assets.image(handle.get('image')).getchannel('A')
        assert alpha.getpixel((alpha.width//2, alpha.height//2)) == 255
    for color in range(1, 8):
        assert sum(visible(handle.get('visible'), f'main_{color}') for handle in handles) == 1
    assert not any((n.get('up') or '').startswith('m_logo') for n in layout), 'Source logo belongs on the controller, away from video'
    sizes = [minimum, (original[0]+173*scale, original[1]+91*scale), maximum,
             (minimum[0], maximum[1]), (maximum[0], minimum[1])]
    # Monitor-sized geometry only, not a simulation of native maximize.
    candidates = [(1280,720),(1920,1080),(2560,1440),(3840,2160),(7680,4320),(8192,4320)]
    for size in candidates:
        if size[0] >= minimum[0] and size[1] >= minimum[1]:
            assert size[0] <= maximum[0] and size[1] <= maximum[1]
            if size not in sizes:
                sizes.append(size)
    for size in sizes:
        viewport = geometry(video, original, size, (0, 0))
        x, y, width, height = viewport
        assert width > 0 and height > 0
        assert (x, y, size[0]-x-width, size[1]-y-height) == (34*scale, 37*scale, 34*scale, 30*scale), 'Manual resize must preserve frame insets'
        for node in layout:
            if node.tag == 'Button':
                keys = [node.get(attr) for attr in ('up', 'over', 'down') if node.get(attr)]
            elif node.tag == 'Checkbox':
                keys = [node.get(attr+str(state)) for state in (1,2) for attr in ('up','over','down') if node.get(attr+str(state))]
            elif node in handles or node in backings:
                keys = [node.get('image')]
            else:
                continue
            for key in keys:
                bounds = geometry(node, original, size, assets.frame(key).size)
                assert not intersects(viewport, bounds), (size, node.get('id'), key, 'Video overlaps a retained control')
    return len(sizes)


def main():
    for scale in (1, 2):
        assets = ThemeAssets(SKIN/f'vlc-{scale}x')
        verify_zoom_controls(assets.tree)
        count = verify_geometry(assets, scale)
        package = ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt'
        with zipfile.ZipFile(package) as archive:
            packaged_xml = archive.read('theme.xml')
            assert E.tostring(E.fromstring(packaged_xml), method='c14n') == E.tostring(assets.tree, method='c14n'), 'Packaged geometry differs from audited theme'
            verify_policy(E.fromstring(packaged_xml))
            verify_zoom_controls(E.fromstring(packaged_xml))
        # Prove that both accidental opt-in and omission of the DTD-defaulted
        # attribute are caught; do not alter the generated theme on disk.
        for value in (None, 'true'):
            changed = deepcopy(assets.tree)
            node = changed.find('.//Video')
            if value is None:
                del node.attrib['autoresize']
            else:
                node.set('autoresize', value)
            try:
                verify_policy(changed)
            except AssertionError:
                pass
            else:
                raise AssertionError('Unsafe autoresize mutation escaped')
        changed = deepcopy(assets.tree)
        changed.find('.//Image[@image="screen_black"]').set('resize', 'mosaic')
        try:
            verify_policy(changed)
        except AssertionError:
            pass
        else:
            raise AssertionError('Per-pixel native repaint regression escaped')
        for mutation in ('wrong-header', 'missing-backing', 'backing-over-button', 'wrong-backing-palette', 'partial-alpha-backing'):
            changed = deepcopy(assets.tree.find('.//Layout[@id="video_1"]'))
            if mutation == 'wrong-header':
                changed.find('Image[@image="eq_top_right_1_png"]').set('image', 'f_top_right_1_png')
            else:
                backing = changed.find('Image[@image="video_vid_zoom_backing_1"]')
                if mutation == 'wrong-backing-palette':
                    backing.set('visible', 'palette_2.isActive')
                elif mutation == 'partial-alpha-backing':
                    backing.set('image', 'vid_zoom_no_png')
                else:
                    changed.remove(backing)
                    if mutation == 'backing-over-button':
                        changed.append(backing)
            try:
                verify_header(changed, scale, assets)
            except AssertionError:
                pass
            else:
                raise AssertionError('Source header mutation escaped: '+mutation)
        for prefix in ('m_full', 'vid_zoom'):
            for attr, value in (('action1','vlc.fullscreen()'), ('action2','video.maximize()'), ('up2',prefix+'_do_png'), ('over2',prefix+'_no_png'), ('down2',prefix+'_hov_png')):
                changed = deepcopy(assets.tree)
                node = next(node for node in changed.iter('Checkbox') if node.get('up1') == prefix+'_no_png')
                node.set(attr, value)
                try:
                    verify_zoom_controls(changed)
                except AssertionError:
                    pass
                else:
                    raise AssertionError('Framed maximize mutation escaped: '+prefix+'/'+attr)
        print(f'PASS {scale}x: generated/package media-autoresize disabled; framed maximize/restore and original checkbox states; source headers/backings; {count} sizes preserve viewport/control clearance; unsafe mutations rejected')


if __name__ == '__main__':
    main()
