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


def intersects(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx+bw and bx < ax+aw and ay < by+bh and by < ay+ah


def verify_policy(tree):
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


def verify_header(layout, scale):
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
        images = layout.findall(f'Image[@image="{key}"]')
        buttons = layout.findall(f'Button[@up="{key}"]')
        assert len(images) == len(buttons) == 1, (prefix, 'Retain source parent backing and button')
        backing, button = images[0], buttons[0]
        offset = int(original.get('left').rsplit('-', 1)[1])
        expected = width-offset*scale, int(original.get('top', 0))*scale
        for node in (backing, button):
            assert (int(node.get('x')), int(node.get('y'))) == expected
            assert node.get('lefttop') == node.get('rightbottom') == 'righttop'
        assert max(layout.index(header) for header in headers) < layout.index(backing) < layout.index(button), (prefix, 'Header/backing/button draw order changed')
        backings.append(backing)
    return backings


def verify_geometry(assets, scale):
    video = verify_policy(assets.tree)
    layout = video.getparent()
    backings = verify_header(layout, scale)
    original = int(layout.get('width')), int(layout.get('height'))
    minimum = int(layout.get('minwidth')), int(layout.get('minheight'))
    maximum = int(layout.get('maxwidth')), int(layout.get('maxheight'))
    assert minimum[0] <= original[0] <= maximum[0] and minimum[1] <= original[1] <= maximum[1]
    handle = layout.find('Image[@action="resizeSE"]')
    assert handle is not None, 'Manual resizing must remain available'
    assert handle.get('lefttop') == handle.get('rightbottom') == 'rightbottom'
    assert assets.image(handle.get('image')).getchannel('A').getextrema()[0] > 0
    assert not any((n.get('up') or '').startswith('m_logo') for n in layout), 'Source logo belongs on the controller, away from video'
    sizes = [minimum, (original[0]+173*scale, original[1]+91*scale), maximum,
             (minimum[0], maximum[1]), (maximum[0], minimum[1])]
    for size in sizes:
        viewport = geometry(video, original, size, (0, 0))
        x, y, width, height = viewport
        assert width > 0 and height > 0
        assert (x, y, size[0]-x-width, size[1]-y-height) == (34*scale, 37*scale, 34*scale, 30*scale), 'Manual resize must preserve frame insets'
        for node in layout:
            if node.tag == 'Button':
                keys = [node.get(attr) for attr in ('up', 'over', 'down') if node.get(attr)]
            elif node is handle or node in backings:
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
        count = verify_geometry(assets, scale)
        package = ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt'
        with zipfile.ZipFile(package) as archive:
            packaged_xml = archive.read('theme.xml')
            assert E.tostring(E.fromstring(packaged_xml), method='c14n') == E.tostring(assets.tree, method='c14n'), 'Packaged geometry differs from audited theme'
            verify_policy(E.fromstring(packaged_xml))
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
        for mutation in ('wrong-header', 'missing-backing', 'backing-over-button'):
            changed = deepcopy(assets.tree.find('.//Layout[@id="video_1"]'))
            if mutation == 'wrong-header':
                changed.find('Image[@image="eq_top_right_1_png"]').set('image', 'f_top_right_1_png')
            else:
                backing = changed.find('Image[@image="vid_zoom_no_png"]')
                changed.remove(backing)
                if mutation == 'backing-over-button':
                    changed.append(backing)
            try:
                verify_header(changed, scale)
            except AssertionError:
                pass
            else:
                raise AssertionError('Source header mutation escaped: '+mutation)
        print(f'PASS {scale}x: generated/package media-autoresize disabled; source headers/backings; {count} manual sizes preserve viewport margins and control clearance; unsafe mutations rejected')


if __name__ == '__main__':
    main()
