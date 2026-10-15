"""Offline combined-art comparisons; neither WMP nor VLC is executed.

Source references reconstruct retained WMS layers, including original sibling
z-order. Fonts, metadata/clock tokens and the added conversion credit are omitted
from both references. Source frame height is trimmed by the documented 72-pixel
transparent margin. These are pixel-composition checks, not native render proof.
"""
import json
import hashlib
from functools import lru_cache
from pathlib import Path

from lxml import etree as E
from PIL import Image, ImageChops, ImageDraw, ImageFont

from assets import ThemeAssets, visible
from check_source_art import source_pixels as decode_source, scaled, pixels

ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT/'skins/need-for-speed-underground'
SOURCE = SKIN/'original'
DOCS = ROOT/'docs'
WMS = E.fromstring((SOURCE/'nfs.wms').read_bytes(), E.XMLParser(recover=True))
MAIN = WMS.find('view[@id="mainView"]')
INFO = WMS.find('view[@id="infoView"]')


@lru_cache(maxsize=256)
def source_pixels(path):
    return decode_source(path)


def put(canvas, image, x, y, scale):
    canvas.alpha_composite(scaled(image, scale), (x*scale, y*scale))


@lru_cache(maxsize=512)
def original(name, scale):
    return scaled(source_pixels(SOURCE/name), scale)


def draw_button(canvas, node, scale, state, ox=0, oy=0, closed=False):
    name = node.get({'idle':'image', 'hover':'hoverImage', 'pressed':'downImage'}[state]) or node.get('image')
    if state == 'idle' and closed and node.get('id') == 'shutterButton':
        name = node.get('downImage')
    if name:
        x = ox+int(node.get('left', 0)); y = oy+int(node.get('top', 0))
        put(canvas, source_pixels(SOURCE/name), x, y, scale)


def source_main(palette, closed, state, scale, raise_outer=False):
    canvas = Image.new('RGBA', (300*scale, 298*scale))
    canvas.alpha_composite(original(f'main_back_{palette}.png', scale))
    if closed:
        put(canvas, source_pixels(SOURCE/'shutter_light.png'), 21, 32, scale)
        if raise_outer:
            put(canvas, source_pixels(SOURCE/'shutter_f01.png'), 54, 52, scale)
    for group in MAIN.findall('subview'):
        if group.get('id') not in ('mainBackFrame', 'mainBackFrame2', 'mainBackFrame3'):
            continue
        if closed and group.get('id') == 'mainBackFrame2':
            continue
        for node in sorted(group, key=lambda n:int(n.get('zIndex', 0))):
            if node.tag in ('text', 'subview', 'pausebutton'):
                continue
            if node.tag == 'customSlider':
                image = source_pixels(SOURCE/node.get('image'))
                count = 29 if node.get('id') == 'volume' else 33
                height = image.height//count; index = count//2
                put(canvas, image.crop((0, index*height, image.width, (index+1)*height)),
                    int(node.get('left')), int(node.get('top')), scale)
            elif node.get('image'):
                draw_button(canvas, node, scale, state, closed=closed)
    if closed and not raise_outer:
        put(canvas, source_pixels(SOURCE/'shutter_f01.png'), 54, 52, scale)
    return canvas


def tile(image, size):
    canvas = Image.new('RGBA', size)
    for y in range(0, size[1], image.height):
        for x in range(0, size[0], image.width):
            canvas.paste(image, (x, y))
    return canvas


def source_info(page, palette, state, scale):
    canvas = Image.new('RGBA', (413*scale, 282*scale))
    # Evaluate the source frame's expressions at its logical 413x354 size.
    # Stretch/tile rails end at the source corner positions, then trim only
    # the 72-pixel transparent bottom margin from the output canvas.
    nodes = [n for n in INFO if (n.get('id') or '').startswith('info')
             and (n.get('id') or '').endswith('_'+str(palette))]
    for node in sorted(nodes, key=lambda n:int(n.get('zIndex', 0))):
        name = node.get('backgroundImage')
        if not name:
            continue
        def position(attr, default):
            value = node.get(attr, str(default)).replace('jscript:view.width', '413').replace('jscript:view.height', '354')
            parts = value.split('-')
            return int(parts[0])-int(parts[1]) if len(parts) == 2 else int(value)
        x, y = position('left', 0), position('top', 0)
        image = original(name, scale)
        if node.get('backgroundTiled') == 'true':
            if node.get('horizontalAlignment') == 'stretch':
                image = tile(image, ((413-164-177)*scale, image.height))
            else:
                image = tile(image, (image.width, (282-57-61)*scale))
        canvas.alpha_composite(image, (x*scale, y*scale))
    put(canvas, source_pixels(SOURCE/'c_back.png'), 14, 34, scale)
    put(canvas, source_pixels(SOURCE/('c_back.jpg' if page == 'menu' else page+'.jpg')), 37, 35, scale)
    if page == 'c_sub_4_1':
        # nfs.js endAlphaBlend shows this retained layer after page 4 settles.
        # Its obsolete outbound actions are removed; preserve the idle artwork.
        link = INFO.find('subview[@id="link1"]')
        put(canvas, source_pixels(SOURCE/link.get('backgroundImage')), 127, 118, scale)
    close_parent = INFO.find('subview[@zIndex="20"]')
    close = close_parent.find('button')
    put(canvas, source_pixels(SOURCE/close_parent.get('backgroundImage')), 345, 6, scale)
    draw_button(canvas, close, scale, state, 345, 6)
    if page == 'menu':
        node = INFO.find('.//buttongroup[@id="menuBackButtons"]')
        # WMP BUTTONGROUP.showBackground defaults false. Unmapped pixels
        # retain c_back.jpg; they must not receive the full group bitmap.
        assert node.get('showBackground', 'false').lower() == 'false'
        mapping = Image.open(SOURCE/node.get('mappingImage')).convert('RGB')
        mask = Image.new('L', mapping.size)
        mask.putdata([255 if (r == 0 and g in (0, 51, 102, 153) and b == 255) else 0
                      for r, g, b in pixels(mapping)])
        name = node.get({'idle':'image', 'hover':'hoverImage', 'pressed':'downImage'}[state])
        overlay = original(name, scale).copy()
        if scale != 1:
            mask = mask.resize(overlay.size, Image.Resampling.NEAREST)
        overlay.putalpha(mask)
        canvas.alpha_composite(overlay, (171*scale, 103*scale))
    else:
        draw_button(canvas, INFO.find('.//subview[@id="infoMenuBack"]/button'), scale, state, 47, 226)
        if page.startswith(('c_sub_2_', 'c_sub_3_')):
            index = int(page.rsplit('_', 1)[1]); last = 4 if page.startswith('c_sub_2_') else 9
            for control, x, disabled in [('navPrev', 323, index == 1), ('navNext', 348, index == last)]:
                node = INFO.find(f'.//button[@id="{control}"]')
                if disabled:
                    put(canvas, source_pixels(SOURCE/node.get('disabledImage')), x, 226, scale)
                else:
                    draw_button(canvas, node, scale, state, x, 226)
    return canvas


def converted(assets, layout_id, palette, state):
    layout = assets.tree.find(f'.//Layout[@id="{layout_id}"]')
    canvas = Image.new('RGBA', (int(layout.get('width')), int(layout.get('height'))))
    for node in layout:
        if node.tag == 'Text' or not visible(node.get('visible'), active=f'main_{palette}'):
            continue
        if node.get('tooltiptext') == 'About this VLC conversion':
            continue
        if node.get('id', '').startswith('clock_'):
            continue
        image = None
        if node.tag == 'Image':
            image = assets.image(node.get('image'))
            if node.get('width'):
                size = int(node.get('width')), int(node.get('height', image.height))
                image = tile(image, size) if node.get('resize') == 'mosaic' else image.resize(size)
        elif node.tag in ('Button', 'Checkbox'):
            key = node.get({'idle':'up', 'hover':'over', 'pressed':'down'}[state]) if node.tag == 'Button' else node.get({'idle':'up1', 'hover':'over1', 'pressed':'down1'}[state])
            key = key or node.get('up') or node.get('up1')
            image = assets.frame(key, int(assets.resources[key].get('nbframes', 1))-1)
        elif node.tag == 'Slider':
            background = node.find('SliderBackground')
            if background is not None:
                count = int(background.get('nbvert'))
                image = assets.frame(background.get('image'), count//2, count)
        if image is not None:
            canvas.alpha_composite(image, (int(node.get('x', 0)), int(node.get('y', 0))))
    return canvas


def residual(source, target):
    # RGB below zero alpha is unobservable. Compare the actual composites on
    # both extremes, plus alpha itself, so edge/opacity differences stay visible.
    mask = ImageChops.difference(source.getchannel('A'), target.getchannel('A'))
    for color in ('black', 'white'):
        a = Image.alpha_composite(Image.new('RGBA', source.size, color), source).convert('RGB')
        b = Image.alpha_composite(Image.new('RGBA', target.size, color), target).convert('RGB')
        for band in ImageChops.difference(a, b).split():
            mask = ImageChops.lighter(mask, band)
    count = sum(1 for value in mask.tobytes() if value)
    # Magenta shows every differing composite/alpha pixel.
    highlight = Image.new('RGBA', source.size)
    highlight.putalpha(mask.point(lambda value:255 if value else 0))
    highlight.paste((255, 80, 170), (0, 0, source.width, source.height), highlight.getchannel('A'))
    return count, mask.getbbox(), highlight


def check_residual():
    hidden_a = Image.new('RGBA', (1, 1), (255, 0, 255, 0))
    hidden_b = Image.new('RGBA', (1, 1))
    assert residual(hidden_a, hidden_b)[0] == 0, 'Hidden RGB is not visible damage'
    assert residual(hidden_a, Image.new('RGBA', (1, 1), 'red'))[0] == 1
    first = Image.new('RGBA', (3, 1)); shifted = first.copy()
    first.putpixel((0, 0), (255, 0, 0, 255))
    shifted.putpixel((1, 0), (255, 0, 0, 255))
    assert residual(first, shifted)[0] == 2, 'Moved visible layer must be detected'


def sheet(rows, path, scale, title, lanes=1):
    width = max(item[1].width for item in rows); height = max(item[1].height for item in rows)
    gap = 12*scale; label = 27*scale
    lane_width = width*3+gap*4
    canvas = Image.new('RGB', (lane_width*lanes, ((len(rows)+lanes-1)//lanes)*(height+label+gap)+label*2), '#171A20')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(str(ROOT/'vendor/FreeSans.ttf'), 12*scale)
    draw.text((gap, 3*scale), title+' | SOURCE / CONVERTED / RESIDUAL', font=font, fill='#DBE6F2')
    for index, (name, source, target, diff) in enumerate(rows):
        y = label*2+(index//lanes)*(height+label+gap)
        ox = (index%lanes)*lane_width
        draw.text((ox+gap, y-label), name, font=font, fill='#DBE6F2')
        for column, image in enumerate((source, target, diff)):
            canvas.paste(image, (ox+gap+column*(width+gap), y), image)
    canvas.save(path)
    overview = canvas.copy()
    overview.thumbnail((1500, 1800), Image.Resampling.LANCZOS)
    overview.save(path.with_stem(path.stem+'-overview'))


def main():
    check_residual()
    report = {'method':'Offline source-WMS and generated-XML asset composition; no native renderer or desktop use.',
              'residual':'Maximum channel difference over black and white composites, plus alpha difference; ignores RGB under zero alpha.',
              'self_checks':'Invisible RGB ignored; opaque pixel and one-pixel layer displacement mutations detected.',
              'menu_semantics':'WMP BUTTONGROUP.showBackground defaults false; no source override exists. Only mapped regions are composed.',
              'menu_semantics_source':'https://learn.microsoft.com/en-us/previous-versions/windows/desktop/wmp/buttongroup-showbackground',
              'omissions':['Dynamic metadata and clock text/font adaptation, including alpha-1 clock input mask', 'Conversion credit footer/button',
                           'Hover/pressed behavior of removed obsolete outbound links; their original idle overlay remains compared'],
              'limits':['Source z-order and tiled frame geometry are reconstructed, not executed in WMP.',
                        'All controls use a uniform feedback state for comparison; this does not simulate simultaneous hover.',
                        'Midpoint gauges, stopped playback and closed auxiliary panels; no native video/EQ rendering.'],
              'cases':[]}
    report['package_sha256'] = {str(scale):hashlib.sha256(
        (ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt').read_bytes()).hexdigest()
        for scale in (1, 2)}
    pages = ['menu']+[p.stem for p in sorted(SOURCE.glob('c_sub_*.jpg'))]
    for scale in (1, 2):
        assets = ThemeAssets(SKIN/f'vlc-{scale}x')
        main_rows = []; info_rows = []; menu_rows = []
        for palette in range(1, 8):
            for state in ('idle', 'hover', 'pressed'):
                for closed in (False, True):
                    name = f'main palette {palette} / {"closed" if closed else "open"} / {state}'
                    source = source_main(palette, closed, state, scale)
                    target = converted(assets, f'main_{palette}'+('_closed' if closed else ''), palette, state)
                    count, bounds, diff = residual(source, target)
                    case = dict(scale=scale, name=name, differing_composite_pixels=count, bounds=bounds)
                    if count and closed:
                        case['maximum_raw_channel_delta'] = max(pair[1] for pair in ImageChops.difference(source, target).getextrema())
                        adapted = source_main(palette, closed, state, scale, raise_outer=True)
                        adapted_count, _, _ = residual(adapted, target)
                        case['outer_controls_raised_residual_pixels'] = adapted_count
                        if adapted_count == 0:
                            case['classification'] = 'Only the documented outer-button layer raise needed for functional hit access.'
                    report['cases'].append(case)
                    if state == 'idle':
                        main_rows.append((name, source, target, diff))
                for page in pages:
                    name = f'{page} / palette {palette} / {state}'
                    source = source_info(page, palette, state, scale)
                    target = converted(assets, 'info_'+page, palette, state)
                    count, bounds, diff = residual(source, target)
                    report['cases'].append(dict(scale=scale, name=name, differing_composite_pixels=count, bounds=bounds))
                    if palette == 1 and state == 'idle':
                        info_rows.append((name, source, target, diff))
                    if page == 'menu' and state == 'hover':
                        menu_rows.append((name, source, target, diff))
        sheet(main_rows, DOCS/f'visual-main-{scale}x.png', scale, f'{scale}x MAIN ART / FONTS OMITTED', lanes=2)
        sheet(info_rows, DOCS/f'visual-info-{scale}x.png', scale, f'{scale}x ORIGINAL INFORMATION PAGES', lanes=2)
        sheet(menu_rows, DOCS/f'visual-menu-hover-{scale}x.png', scale, f'{scale}x MENU HOVER ART')
    cases = report['cases']; differences = [case for case in cases if case['differing_composite_pixels']]
    report['summary'] = dict(cases=len(cases), exact_cases=len(cases)-len(differences),
        residual_cases=len(differences), unexplained_residual_cases=sum(not case.get('classification') for case in differences))
    (DOCS/'visual-comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'{len(cases)} combined-layer cases; {len(differences)} have residual pixels; see docs/visual-comparison.json')


if __name__ == '__main__':
    main()
