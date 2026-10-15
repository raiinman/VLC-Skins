"""Offline panel hit ownership and resize geometry; does not launch VLC.

Image/button alpha hits follow VLC 3's CtrlImage/CtrlButton; slider rails
use a conservative corridor around their curve. Focusable text uses its box.
This is a source/geometry check, not evidence of native mouse behavior.
"""
import re
from array import array
from collections import Counter

from PIL import Image, ImageDraw

from assets import ThemeAssets, visible
from build import SKIN


def geometry(node, original, size, image_size):
    x, y = int(node.get('x', 0)), int(node.get('y', 0))
    w, h = int(node.get('width', image_size[0])), int(node.get('height', image_size[1]))
    dx, dy = size[0]-original[0], size[1]-original[1]
    first = node.get('lefttop', 'lefttop')
    last = node.get('rightbottom', 'lefttop')
    left, top = x + (dx if first.startswith('right') else 0), y + (dy if first.endswith('bottom') else 0)
    right = x+w + (dx if last.startswith('right') else 0)
    bottom = y+h + (dy if last.endswith('bottom') else 0)
    return left, top, right-left, bottom-top


def slider_geometry(node, original, size):
    points = [(int(x), int(y)) for x, y in re.findall(r'\((-?\d+),(-?\d+)\)', node.get('points'))]
    # VLC Bezier::getWidth/getHeight use the maximum coordinate plus one.
    curve = max(x for x, y in points)+1, max(y for x, y in points)+1
    return points, curve, geometry(node, original, size, curve)


def layers(assets, layout, palette, size, checked):
    original = int(layout.get('width')), int(layout.get('height'))
    result = []
    controls = []
    for node in layout:
        controls.append(node)
        # Native parsing assigns the nested scrollbar the next layout layer;
        # its coordinates remain relative to the layout, not the Playtree.
        if node.tag == 'Playtree':
            controls.extend(node.findall('Slider'))
    for node in controls:
        if not visible(node.get('visible'), f'main_{palette}'):
            continue
        if node.tag == 'Slider':
            _, _, (x, y, w, h) = slider_geometry(node, original, size)
            thumb = assets.image(node.get('up'))
            radius = max(int(node.get('thickness', 10)), (max(thumb.size)+1)//2)
            # Conservative rectangle: no retained button may intersect any rail.
            result.append((node, (x-radius, y-radius, w+2*radius, h+2*radius), None))
            continue
        if node.tag in ('Playtree', 'Video'):
            result.append((node, geometry(node, original, size, (0, 0)), None))
            continue
        if node.tag == 'Text':
            if visible(node.get('focus', 'true')):
                height = int(assets.resources[node.get('font')].get('size'))
                result.append((node, geometry(node, original, size, (0, height)), None))
            continue
        if node.tag not in ('Image', 'Button', 'Checkbox'):
            continue
        key = node.get('image') if node.tag == 'Image' else node.get('up') if node.tag == 'Button' else node.get('up2' if checked else 'up1')
        im = assets.frame(key)
        box = geometry(node, original, size, im.size)
        result.append((node, box, im.getchannel('A')))
    return result


def ownership(items, size):
    canvas = Image.new('I', size)
    for index, (node, (x, y, w, h), alpha) in enumerate(items, 1):
        if alpha is None:
            ImageDraw.Draw(canvas).rectangle((x, y, x+w-1, y+h-1), fill=index)
            continue
        mask = alpha.point(lambda a: 255 if a else 0)
        if mask.getextrema() == (255, 255):
            ImageDraw.Draw(canvas).rectangle((x, y, x+w-1, y+h-1), fill=index)
            continue
        if mask.getbbox() is None:
            continue
        # The converter uses tiled Image controls for resizable frame rails.
        for oy in range(0, h, mask.height):
            for ox in range(0, w, mask.width):
                part = mask.crop((0, 0, min(mask.width, w-ox), min(mask.height, h-oy)))
                canvas.paste(index, (x+ox, y+oy), part)
    return canvas


def verify(assets, layout, palette, size, checked, scale, stats=None):
    items = layers(assets, layout, palette, size, checked)
    canvas = ownership(items, size)
    count = 0
    for index, (node, (x, y, w, h), alpha) in enumerate(items, 1):
        if node.tag == 'Slider':
            original = int(layout.get('width')), int(layout.get('height'))
            points, curve, (sx, sy, sw, sh) = slider_geometry(node, original, size)
            assert len(points) == 2, 'Panel slider check currently models straight rails'
            tw, th = assets.image(node.get('up')).size
            for t in (0, .25, .5, .75, 1):
                px = round(points[0][0]*(1-t)+points[1][0]*t)
                py = round(points[0][1]*(1-t)+points[1][1]*t)
                cx, cy = sx+int(px*sw/curve[0]), sy+int(py*sh/curve[1])
                assert tw//2 <= cx < size[0]-(tw+1)//2 and th//2 <= cy < size[1]-(th+1)//2, (layout.get('id'), node.get('id'), t, 'slider thumb outside window')
                assert canvas.getpixel((cx, cy)) == index, (layout.get('id'), node.get('id'), t, 'slider access obstructed')
                if stats is not None:
                    stats['slider_samples'] += 1
            continue
        if node.tag not in ('Button', 'Checkbox'):
            continue
        actual = canvas.crop((x, y, x+w, y+h))
        points = [(a, owner) for a, owner in zip(alpha.tobytes(), array('i', actual.tobytes())) if a > 100]
        assert points and all(owner == index for a, owner in points), (layout.get('id'), palette, size, node.get('id'), 'button obscured')
        count += 1
    # A functional corner must follow the lower-right edge at every size.
    handles = layout.findall('Image[@action="resizeSE"]')
    if handles:
        active_handles = [node for node in handles if visible(node.get('visible'), f'main_{palette}')]
        assert len(active_handles) == 1, (layout.get('id'), palette, 'Resize handle palette selection')
        handle = active_handles[0]
        original = int(layout.get('width')), int(layout.get('height'))
        im = assets.image(handle.get('image'))
        x, y, w, h = geometry(handle, original, size, im.size)
        assert (size[0]-x, size[1]-y) == (36*scale, 24*scale), (layout.get('id'), 'resize handle detached')
        index = next(i for i, item in enumerate(items, 1) if item[0] is handle)
        assert canvas.getpixel((x+w//2, y+h//2)) == index, (layout.get('id'), 'resize handle obscured')
        viewport = layout.find('Playtree')
        if viewport is None:
            viewport = layout.find('Video')
        vx, vy, vw, vh = geometry(viewport, original, size, (0, 0))
        expected_right = (52 if viewport.tag == 'Playtree' else 34)*scale
        assert (vx, vy, size[0]-vx-vw, size[1]-vy-vh) == (34*scale, 37*scale, expected_right, 30*scale), (layout.get('id'), 'viewport margin changed')
    return count


def main():
    for scale in (1, 2):
        assets = ThemeAssets(SKIN/f'vlc-{scale}x')
        counts = Counter()
        for layout in assets.tree.findall('.//Layout'):
            if layout.getparent().get('id') in ('main','palette_state'):
                continue
            original = int(layout.get('width')), int(layout.get('height'))
            sizes = [original]
            if layout.get('maxwidth') is not None:
                sizes += [(original[0]+173*scale, original[1]+91*scale), (int(layout.get('maxwidth')), int(layout.get('maxheight')))]
            for size in sizes:
                for palette in range(1, 8):
                    for checked in (False, True):
                        counts['buttons'] += verify(assets, layout, palette, size, checked, scale, counts)
                        counts['states'] += 1
        print(f'PASS {scale}x: {counts["states"]} panel palette/size/check states, {counts["buttons"]} button ownership checks, {counts["slider_samples"]} slider access samples; resize handles and viewport margins')


if __name__ == '__main__':
    main()
