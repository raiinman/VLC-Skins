"""Compare delivered static artwork against independently decoded source pixels."""
from pathlib import Path

from lxml import etree as E
from PIL import Image

from assets import ThemeAssets


ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / 'skins/need-for-speed-underground'
SOURCE = SKIN / 'original'
ART_ATTRIBUTES = {'image', 'up', 'over', 'down', 'up1', 'over1', 'down1',
                  'up2', 'over2', 'down2'}


def pixels(image):
    data = image.load()
    return (data[x, y] for y in range(image.height) for x in range(image.width))


def source_pixels(path):
    """Apply the WMS exact magenta key before any output scaling."""
    image = Image.open(path).convert('RGBA')
    image.putdata([(r, g, b, 0 if (r, g, b) == (255, 0, 255) else a)
                   for r, g, b, a in pixels(image)])
    return image


def scaled(image, scale):
    return image if scale == 1 else image.resize(
        (image.width * scale, image.height * scale), Image.Resampling.LANCZOS)


def mapped_crop(source, mapping, color):
    """Recover a WMP buttongroup region from its original mapping image."""
    mask = Image.new('L', mapping.size)
    mask.putdata([255 if pixel == color else 0 for pixel in pixels(mapping)])
    bounds = mask.getbbox()
    assert bounds is not None, ('Missing source mapping color', color)
    crop = source.crop(bounds)
    crop.putalpha(mask.crop(bounds))
    return crop, bounds


def compare(assets, resource, expected, scale):
    actual = assets.image(resource)
    expected = scaled(expected, scale)
    assert actual.size == expected.size, (scale, resource, 'dimensions')
    assert actual.tobytes() == expected.tobytes(), (scale, resource, 'source pixels')


def main():
    original = E.fromstring((SOURCE / 'nfs.wms').read_bytes(), E.XMLParser(recover=True))
    source_controls = {node.get('image').replace('.', '_'): node
                       for node in original.iter()
                       if node.get('image') and node.get('hoverImage')}
    for scale in (1, 2):
        assets = ThemeAssets(SKIN / f'vlc-{scale}x')
        used = {value for node in assets.tree.iter()
                for attr, value in node.attrib.items() if attr in ART_ATTRIBUTES}
        original_count = 0
        for path in sorted(SOURCE.iterdir()):
            if path.suffix.lower() not in ('.png', '.jpg'):
                continue
            resource = path.name.replace('.', '_')
            if resource not in used:
                continue
            compare(assets, resource, source_pixels(path), scale)
            original_count += 1

        state_bindings = 0
        for node in assets.tree.iter():
            state_groups = [('up', 'over', 'down')] if node.tag == 'Button' else (
                [('up1', 'over1', 'down1'), ('up2', 'over2', 'down2')]
                if node.tag == 'Checkbox' else [])
            for up, over, down in state_groups:
                source = source_controls.get(node.get(up))
                if source is None:
                    continue
                assert node.get(over) == source.get('hoverImage').replace('.', '_'), (
                    scale, node.get('id'), 'source hover binding')
                assert node.get(down) == source.get('downImage').replace('.', '_'), (
                    scale, node.get('id'), 'source pressed binding')
                state_bindings += 1

        # A renamed or dropped source resource must not silently reduce coverage.
        assert original_count >= 176, ('Original source coverage shrank', original_count)
        assert state_bindings >= 920, ('Source state coverage shrank', state_bindings)

        menu = assets.tree.find('.//Layout[@id="info_menu"]')
        mapping = Image.open(SOURCE / 'c_menu_map.png').convert('RGB')
        for index, green in enumerate((0, 51, 102, 153)):
            for state in ('no', 'hov', 'do'):
                expected, bounds = mapped_crop(
                    source_pixels(SOURCE / f'c_menu_{state}.jpg'), mapping,
                    (0, green, 255))
                resource = f'menu_{index}_{state}'
                compare(assets, resource, expected, scale)
                if state == 'no':
                    button = menu.find(f'Button[@up="{resource}"]')
                    assert button is not None, resource
                    assert (int(button.get('x')), int(button.get('y'))) == (
                        (171 + bounds[0]) * scale, (103 + bounds[1]) * scale), resource

        mapping = Image.open(SOURCE / 'eq_set_map.png').convert('RGB')
        for state in ('no', 'hov', 'do'):
            expected, _ = mapped_crop(
                source_pixels(SOURCE / f'eq_set_{state}.png'), mapping,
                (0, 51, 255))
            compare(assets, f'eq_power_{state}_png', expected, scale)
        print(f'PASS {scale}x: {original_count} source images, {state_bindings} '
              'source control state bindings, 12 menu states, 3 EQ power states '
              'and source menu positions')


if __name__ == '__main__':
    main()
