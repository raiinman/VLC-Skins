"""Render candidate XML/assets for compact-bar and filename review, offline.

These are asset reconstructions, never native screenshots. Pillow approximates
FreeType text and slider positions; native focus, timing and scrolling need VLC.
Synthetic bright/dark media contains no desktop captures or user media.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from assets import ThemeAssets, visible

ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / 'skins/need-for-speed-underground'
LONG_NAME = 'Need for Speed Underground — Original Soundtrack — 0123456789 — Long filename review.mp4'


def resized(image, node):
    size = int(node.get('width', image.width)), int(node.get('height', image.height))
    if size == image.size:
        return image
    if node.get('resize', 'mosaic') != 'mosaic':
        return image.resize(size, Image.Resampling.BILINEAR)
    result = Image.new('RGBA', size)
    for y in range(0, size[1], image.height):
        for x in range(0, size[0], image.width):
            result.paste(image, (x, y))
    return result


def text_image(assets, node, filename, offset):
    resource = assets.resources[node.get('font')]
    font = ImageFont.truetype(str(assets.directory / resource.get('file')), int(resource.get('size')))
    value = node.get('text', '').replace('$N', filename).replace('$t', '02:36').replace('$l', '-04:18').replace('$d', '06:54').replace('$V', '65')
    bounds = font.getbbox(value)
    width = int(node.get('width'))
    height = max(font.size + 2, bounds[3] - bounds[1])
    image = Image.new('RGBA', (width, height))
    length = font.getlength(value)
    alignment = node.get('alignment', 'left')
    x = max(0, (width - length) / 2) if alignment == 'center' else max(0, width - length) if alignment == 'right' else 0
    if length > width:
        x = -min(offset, max(0, length - width))
    ImageDraw.Draw(image).text((x, -bounds[1]), value, font=font, fill=node.get('color', '#FFFFFF'))
    return image


def render(assets, layout, state='idle', playing=False, filename=LONG_NAME, offset=0, palette=1, expanded=False):
    result = Image.new('RGBA', (int(layout.get('width')), int(layout.get('height'))))
    active = layout.get('id')
    flags = {active + '.isActive': True, f'palette_{palette}.isActive': True,
             'vlc.isPlaying': playing, 'video.isMaximized': False, 'hover_volume_expanded.isActive': expanded,
             'fullscreenController.isVisible': True, 'videoHoverController.isVisible': True}
    for node in layout:
        if not visible(node.get('visible'), active=active, flags=flags):
            continue
        x, y = int(node.get('x', 0)), int(node.get('y', 0))
        image = None
        if node.tag == 'Image':
            key = node.get('image')
            count = int(assets.resources[key].get('nbframes', 1))
            image = resized(assets.frame(key, count - 1), node)
        elif node.tag in ('Button', 'Checkbox'):
            attr = {'idle': 'up', 'hover': 'over', 'pressed': 'down'}[state]
            if node.tag == 'Checkbox':
                attr += '2' if visible(node.get('state'), active=active, flags=flags) else '1'
            key = node.get(attr) or node.get('up') or node.get('up1')
            count = int(assets.resources[key].get('nbframes', 1))
            image = assets.frame(key, count - 1)
        elif node.tag == 'Text':
            image = text_image(assets, node, filename, offset)
        elif node.tag == 'Slider':
            background = node.find('SliderBackground')
            if background is not None:
                count = int(background.get('nbvert', 1))
                image = assets.frame(background.get('image'), count // 2, count)
            else:
                points = [(int(a), int(b)) for a, b in re.findall(r'\((-?\d+),(-?\d+)\)', node.get('points', ''))]
                if points:
                    fraction = .65 if node.get('value') == 'volume' else .38
                    px = points[0][0] + (points[-1][0] - points[0][0]) * fraction
                    py = points[0][1] + (points[-1][1] - points[0][1]) * fraction
                    key = node.get('down') if state == 'pressed' else node.get('up')
                    image = assets.frame(key)
                    x += round(px - image.width / 2)
                    y += round(py - image.height / 2)
        if image is not None:
            result.alpha_composite(image, (x, y))
    return result


def media(size, bright):
    image = Image.new('RGB', size, '#EAF4FF' if bright else '#070B12')
    draw = ImageDraw.Draw(image)
    for x in range(-size[1], size[0], 55):
        draw.line((x, 0, x + size[1], size[1]), fill='#A1C7E8' if bright else '#243449', width=17)
    return image.convert('RGBA')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True, help='Explicit destination; creates asset renders and scope JSON')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    label_font = ImageFont.truetype(str(ROOT / 'vendor/FreeSans.ttf'), 13)
    report = {'method': __doc__.strip(), 'filename': LONG_NAME, 'cases': [], 'theme_sha256': {},
              'limits': ['All buttons share one feedback state to expose assets; this is not simultaneous native hover.',
                         'Pillow glyph placement, clipped long-name offsets and slider thumbs approximate the native renderer.',
                         'Bright/dark media is generated geometry, not a VLC video frame or desktop capture.',
                         'Native scrolling, click/drag behavior, focus and hover timing are outside this preview.']}
    for scale in (1, 2):
        assets = ThemeAssets(SKIN / f'vlc-{scale}x')
        report['theme_sha256'][str(scale)] = hashlib.sha256((assets.directory / 'theme.xml').read_bytes()).hexdigest()
        window = assets.tree.find('Window[@id="videoHoverController"]')
        layouts = [l for l in window if int(l.get('height')) == 64]
        assert layouts, 'Build a compact candidate first; no 64px companion layout exists'
        samples = []
        for layout in layouts:
            for state, playing, expanded in [('idle', False, False), ('hover', True, False), ('pressed', True, False),
                                             ('idle', False, True), ('hover', True, True), ('pressed', True, True)]:
                for bright in (False, True):
                    tile = media((410, 100), bright)
                    bar = render(assets, layout, state, playing, expanded=expanded)
                    assert bar.size == (361, 64), ('Physical companion size', scale, bar.size)
                    tile.alpha_composite(bar, (24, 20))
                    name = f'{state} / {"playing" if playing else "paused"} / volume {"expanded" if expanded else "collapsed"} / {"bright" if bright else "dark"}'
                    samples.append((name, tile))
                    report['cases'].append({'scale': scale, 'layout': layout.get('id'), 'state': state,
                                            'playing': playing, 'volume_expanded': expanded,
                                            'media': 'bright' if bright else 'dark', 'size': list(bar.size)})
        board = Image.new('RGB', (840, ((len(samples) + 1) // 2) * 132 + 48), '#161B22')
        draw = ImageDraw.Draw(board)
        draw.text((12, 12), f'{scale}x candidate / COMPACT ASSET RENDER / 360px artwork, 29px source controls', fill='white', font=label_font)
        for index, (name, tile) in enumerate(samples):
            x, y = 10 + index % 2 * 420, 48 + index // 2 * 132
            draw.text((x, y), name, fill='#D2DEEA', font=label_font)
            board.paste(tile.convert('RGB'), (x, y + 22))
        board.save(args.output_dir / f'compact-preview-{scale}x.png')
        # Full main art plus exact clipped text crops at the beginning and later
        # in a long title. No invented media is placed inside the original main.
        mains = [render(assets, assets.tree.find(f'.//Layout[@id="main_{p}"]'),
                        filename=LONG_NAME, offset=75 * scale, palette=p) for p in range(1, 8)]
        width, height = mains[0].size
        row_height = height + 40 * scale + 20
        main_board = Image.new('RGB', (width * 4, row_height * 2 + 35), '#161B22')
        md = ImageDraw.Draw(main_board)
        md.text((10, 8), f'{scale}x original main / white filename adaptation / long title clipped at +75px source offset', font=label_font, fill='white')
        for index, image in enumerate(mains):
            x, y = index % 4 * width, 35 + index // 4 * row_height
            main_board.paste(image, (x, y), image)
            for shift, dy in [(0, 0), (75 * scale, 19 * scale)]:
                sample = render(assets, assets.tree.find(f'.//Layout[@id="main_{index + 1}"]'), filename=LONG_NAME, offset=shift, palette=index + 1)
                crop = sample.crop((62 * scale, 117 * scale, 239 * scale, 133 * scale))
                main_board.paste(crop, (x, y + height + dy), crop)
        main_board.save(args.output_dir / f'metadata-preview-{scale}x.png')
        overview = main_board.copy()
        overview.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
        overview.save(args.output_dir / f'metadata-preview-{scale}x-overview.png')
    (args.output_dir / 'compact-preview.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Asset-only previews: {len(report["cases"])} compact cases plus all 14 main palettes, two filename offsets; {args.output_dir}')


if __name__ == '__main__':
    main()
