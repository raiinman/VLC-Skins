"""Offline resize-corner pixels and Windows cached-image copy regression.

CtrlImage caches drawBitmap into OSGraphics, then drawGraphics uses masked
BitBlt(SRCCOPY), not per-pixel alpha compositing against the final layout.
The paint model assumes a black cache, matching the reported rectangle.
It is a bounded source-derived model, not a Windows screenshot/render test.
"""
import zipfile

from lxml import etree as E
from PIL import Image

from assets import ThemeAssets, visible
from build import ROOT, SKIN, SOURCE
from check_panels import geometry


def source_corner(color, scale):
    full = Image.open(SOURCE/f'f_bot_right_{color}.png').convert('RGBA')
    data = full.tobytes()
    full.putdata([(r, g, b, 0 if (r, g, b) == (255, 0, 255) else a)
                  for r, g, b, a in zip(data[::4], data[1::4], data[2::4], data[3::4])])
    if scale != 1:
        full = full.resize((full.width*scale, full.height*scale), Image.Resampling.LANCZOS)
    # Crop after resizing the full frame, preserving its edge filter pixels.
    return full.crop((128*scale, 33*scale, 151*scale, 57*scale))


def cached_copy(destination, bitmap):
    cached = Image.alpha_composite(Image.new('RGBA', bitmap.size, 'black'), bitmap).convert('RGB')
    mask = bitmap.getchannel('A').point(lambda a: 255 if a else 0)
    result = destination.copy()
    result.paste(cached, (0, 0), mask)
    return result


def verify_patch(actual, expected):
    assert actual.size == expected.size and actual.tobytes() == expected.tobytes(), 'Resize patch must retain exact native-scale palette corner RGBA'
    # Drawing the real corner again through native cache-copy semantics must
    # preserve the already drawn frame, including its transparent edge holes.
    background = Image.new('RGB', expected.size, (113, 89, 67))
    baseline = cached_copy(background, expected)
    assert cached_copy(baseline, actual).tobytes() == baseline.tobytes(), 'Cached resize image overwrites the frame'
    alpha = actual.getchannel('A')
    assert alpha.getpixel((actual.width//2, actual.height//2)) == 255, 'Resize center must remain hittable'


def verify(assets, scale):
    checked = 0
    for name in ('tracks', 'video'):
        layout = assets.tree.find(f'.//Window[@id="{name}"]/Layout')
        original = int(layout.get('width')), int(layout.get('height'))
        maximum = int(layout.get('maxwidth')), int(layout.get('maxheight'))
        sizes = [original, (original[0]+173*scale, original[1]+91*scale), maximum,
                 (original[0], maximum[1]), (maximum[0], original[1])]
        handles = layout.findall('Image[@action="resizeSE"]')
        assert len(handles) == 7, (name, 'One source corner patch per palette required')
        for color in range(1, 8):
            active = [h for h in handles if visible(h.get('visible'), f'main_{color}')]
            assert len(active) == 1, (name, color, 'Resize palette selection')
            node = active[0]
            assert node.get('lefttop') == node.get('rightbottom') == 'rightbottom'
            actual = assets.image(node.get('image'))
            verify_patch(actual, source_corner(color, scale))
            for size in sizes:
                x, y, w, h = geometry(node, original, size, actual.size)
                assert (size[0]-x, size[1]-y, w, h) == (36*scale, 24*scale, 23*scale, 24*scale)
                checked += 1
    # Alias kept for adapters that already refer to this resource by name.
    verify_patch(assets.image('resize_hit'), source_corner(1, scale))
    return checked


def main():
    for scale in (1, 2):
        assets = ThemeAssets(SKIN/f'vlc-{scale}x')
        count = verify(assets, scale)
        with zipfile.ZipFile(ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt') as archive:
            assert E.tostring(E.fromstring(archive.read('theme.xml')), method='c14n') == E.tostring(assets.tree, method='c14n')
            for node in assets.tree.findall('.//Image[@action="resizeSE"]'):
                resource = assets.resources[node.get('image')]
                filename = resource.getparent().get('file') if resource.tag == 'SubBitmap' else resource.get('file')
                assert archive.read(filename) == (assets.directory/filename).read_bytes(), 'Packaged corner differs'
        expected = source_corner(1, scale)
        old_mask = Image.new('RGBA', expected.size, (0, 0, 0, 1))
        baseline = cached_copy(Image.new('RGB', expected.size, (113, 89, 67)), expected)
        assert cached_copy(baseline, old_mask).tobytes() != baseline.tobytes(), 'Model failed to expose the old black rectangle'
        try:
            verify_patch(old_mask, expected)
        except AssertionError:
            pass
        else:
            raise AssertionError('Old alpha-1 mask escaped')
        print(f'PASS {scale}x: {count} palette/size corner checks, exact source RGBA and cached-copy preservation; old black-mask regression rejected')


if __name__ == '__main__':
    main()
