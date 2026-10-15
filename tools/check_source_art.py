"""Compare delivered static artwork against independently decoded source pixels."""
from pathlib import Path
import re

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


def native_menu_crop(source, mapping, color, scale):
    """Scale the full source artwork before selecting its hard mapped region."""
    mask = Image.new('L', mapping.size)
    mask.putdata([255 if pixel == color else 0 for pixel in pixels(mapping)])
    bounds = mask.getbbox()
    assert bounds is not None, ('Missing source mapping color', color)
    native = scaled(source, scale).copy()
    if scale != 1:
        mask = mask.resize(native.size, Image.Resampling.NEAREST)
    native.putalpha(mask)
    return native.crop(tuple(value*scale for value in bounds)), bounds


def compare(assets, resource, expected, scale, prescaled=False):
    actual = assets.image(resource)
    expected = expected if prescaled else scaled(expected, scale)
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
        assert original_count >= 177, ('Original source coverage shrank', original_count)
        assert state_bindings >= 920, ('Source state coverage shrank', state_bindings)

        # WMS subview backings and child feedback both draw; a partially alpha
        # idle bitmap is not redundant behind its child button.
        backing_count = 0
        for target_id, source_id in [('tracks', 'plView'), ('equalizer', 'eqView'),
                                     ('video', 'videoView'), ('info', 'infoView')]:
            source_view = original.find(f'view[@id="{source_id}"]')
            for parent in source_view.findall('subview'):
                name = parent.get('backgroundImage')
                if name not in ('m_close_no.png', 'vid_zoom_no.png'):
                    continue
                for layout in assets.tree.findall(f'./Window[@id="{target_id}"]/Layout'):
                    expression = parent.get('left')
                    match = re.fullmatch(r'jscript:view.width-(\d+)', expression)
                    x = int(layout.get('width'))-int(match.group(1))*scale if match else int(expression)*scale
                    y = int(parent.get('top', 0))*scale
                    key = name.replace('.', '_')
                    image = next((node for node in layout.findall('Image')
                                  if node.get('image') == key and
                                  (int(node.get('x', 0)), int(node.get('y', 0))) == (x, y)), None)
                    button = next((node for node in layout if node.tag in ('Button','Checkbox')
                                   and (node.get('up') or node.get('up1')) == key and
                                   (int(node.get('x', 0)), int(node.get('y', 0))) == (x, y)), None)
                    assert image is not None and button is not None, (layout.get('id'), 'Source button backing missing')
                    assert layout.index(image) < layout.index(button), (layout.get('id'), 'Backing covers button feedback')
                    backing_count += 1

        source_link = original.find('.//subview[@id="link1"]')
        source_menu = original.find('.//subview[@id="menuBack"]')
        expected = tuple((int(source_menu.get(axis)) + int(source_link.get(axis).rsplit('+', 1)[1]))*scale
                         for axis in ('left', 'top'))
        link = assets.tree.find('.//Layout[@id="info_c_sub_4_1"]/Image[@image="c_link_no_jpg"]')
        assert link is not None, 'Settled Web Destinations source overlay missing'
        assert (int(link.get('x')), int(link.get('y'))) == expected, 'Web Destinations overlay moved'

        menu = assets.tree.find('.//Layout[@id="info_menu"]')
        mapping = Image.open(SOURCE / 'c_menu_map.png').convert('RGB')
        for index, green in enumerate((0, 51, 102, 153)):
            for state in ('no', 'hov', 'do'):
                expected, bounds = native_menu_crop(
                    source_pixels(SOURCE / f'c_menu_{state}.jpg'), mapping,
                    (0, green, 255), scale)
                resource = f'menu_{index}_{state}'
                compare(assets, resource, expected, scale, prescaled=True)
                if state == 'no':
                    button = menu.find(f'Button[@up="{resource}"]')
                    assert button is not None, resource
                    assert (int(button.get('x')), int(button.get('y'))) == (
                        (171 + bounds[0]) * scale, (103 + bounds[1]) * scale), resource
                    assert button.get('over') == f'menu_{index}_hov'
                    assert button.get('down') == f'menu_{index}_do'

        mapping = Image.open(SOURCE / 'eq_set_map.png').convert('RGB')
        for state in ('no', 'hov', 'do'):
            expected, _ = mapped_crop(
                source_pixels(SOURCE / f'eq_set_{state}.png'), mapping,
                (0, 51, 255))
            compare(assets, f'eq_power_{state}_png', expected, scale)
        print(f'PASS {scale}x: {original_count} source images, {state_bindings} '
              'source control state bindings, 12 menu states, 3 EQ power states '
              f'and source menu positions; {backing_count} source button backings and web overlay')


if __name__ == '__main__':
    main()
