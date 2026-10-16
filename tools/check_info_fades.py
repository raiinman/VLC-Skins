"""Independent Info fade pixels, routes and hit checks; never launches VLC.

This verifies completed-page transitions. It does not emulate interrupted WMP
fades or native timer scheduling. Timed alpha-one buttons forward menu clicks
until the return fade ends; original hover feedback resumes after release.
"""
import argparse
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import re
import tempfile
from types import MethodType
import zipfile

from lxml import etree as E
from PIL import Image, ImageChops

from assets import ThemeAssets, visible
from build import Builder, ROOT, SKIN, SOURCE
from check_panels import ownership
from check_source_art import source_pixels, scaled, native_menu_crop
from skin_support import playback_action

PAGES = tuple(sorted(p.stem for p in SOURCE.glob('c_sub_*.jpg')))
PARTS = (('f_top_s', 177, 0, 72, 61), ('f_bot_s', 177, 222, 72, 60),
         ('f_left_s', 0, 61, 177, 164), ('f_right_s', 249, 61, 164, 164),
         ('f_top_left', 0, 0, 177, 61), ('f_top_right', 249, 0, 164, 61),
         ('f_bot_left', 0, 225, 177, 57), ('info_bot_right', 249, 225, 164, 57))


@lru_cache(maxsize=256)
def source(name, scale):
    return scaled(source_pixels(SOURCE/name), scale)


def same(actual, expected, label):
    assert actual.size == expected.size and actual.tobytes() == expected.tobytes(), label


def state(target, previous=None):
    return 'info_state_' + target + ('_from_' + previous if previous else '')


def routes():
    result = [('about', None)] + [(p, None) for p in PAGES]
    for previous in PAGES:
        group, index = previous.rsplit('_', 1)
        result += [(target, previous) for target in PAGES
                   if target.rsplit('_', 1)[0] == group
                   and abs(int(target.rsplit('_', 1)[1])-int(index)) == 1]
        result.append(('menu', previous))
    return result + [('menu', None)]


def physical(assets, key, bands):
    return bands.get(key, {}).get('bands', [{'id': key, 'y': 0,
                                           'height': assets.frame(key).height}])


def check_strip(assets, key, expected, alphas, bands):
    """Check both offline canonical pixels and every runtime band independently."""
    for item in physical(assets, key, bands):
        resource = assets.resources[item['id']]
        assert tuple(resource.get(a) for a in ('nbframes', 'fps', 'loop')) == (str(len(alphas)), '20', '1'), key
        if not getattr(assets, 'synthetic', False):
            assert assets.image(item['id']).height <= 4096, ('Native mask size', key)
    for index, alpha in enumerate(alphas):
        wanted = expected.copy()
        wanted.putalpha(expected.getchannel('A').point(lambda a: (a*alpha+127)//255))
        same(assets.frame(key, index), wanted, (key, index))
        for band in physical(assets, key, bands):
            crop = wanted.crop((0, band['y'], wanted.width, band['y']+band['height']))
            same(assets.frame(band['id'], index), crop, (band['id'], index))


def check_animation(assets, hub, key, gate, x, y, bands):
    indexes = []
    for band in physical(assets, key, bands):
        controls = [n for n in hub if n.get('up') == band['id'] and n.get('visible') == gate]
        assert len(controls) == 1, (key, gate, 'one animation control per band')
        node = controls[0]
        assert node.tag == 'Button' and node.get('over') == node.get('down') == node.get('up'), (key, 'non-restarting feedback')
        assert node.get('action') == 'none', (key, 'decorative action')
        assert (int(node.get('x')), int(node.get('y'))) == (x, y+band['y']), key
        indexes.append(hub.index(node))
    assert indexes == list(range(min(indexes), max(indexes)+1)), (key, 'contiguous bands')
    return indexes


@lru_cache(maxsize=8)
def source_menu_mask(scale, index):
    """Derive the forwarder's exact region/RGB from the original full mapping."""
    mapping = Image.open(SOURCE/'c_menu_map.png').convert('RGB')
    expected, bounds = native_menu_crop(source_pixels(SOURCE/'c_menu_no.jpg'), mapping,
                                       (0, index*51, 255), scale)
    expected.putalpha(expected.getchannel('A').point(lambda a: 1 if a else 0))
    return expected, bounds


def menu_mask(assets, scale, index):
    expected, bounds = source_menu_mask(scale, index)
    key = f'info_menu_hit_{index}'
    resource = assets.resources[key]
    assert tuple(resource.get(a) for a in ('nbframes', 'fps', 'loop')) == ('2', '2', '1'), '500ms menu forwarder'
    assert assets.image(key).size == (expected.width, expected.height*2)
    same(assets.frame(key, 0), expected, ('Source mapped hit mask', index))
    same(assets.frame(key, 1), Image.new('RGBA', expected.size), ('Menu mask must release', index))
    return ((171+bounds[0])*scale, (103+bounds[1])*scale)


def art(assets, scale, report, bands):
    for index in range(4):
        menu_mask(assets, scale, index)
    for page in PAGES:
        for direction, alphas in [('in', [round(50+205*i/8) for i in range(9)]),
                                  ('out', [round(255*(10-i)/10) for i in range(11)])]:
            check_strip(assets, 'info_page_'+direction+'_'+page, source(page+'.jpg', scale), alphas, bands)
    check_strip(assets, 'info_link_in', source('c_link_no.jpg', scale), [0]*8+[255], bands)
    expected_records = []
    for color in range(1, 8):
        previous = color-1 if color > 1 else 7
        for index, (part, x, y, width, height) in enumerate(PARTS):
            current = source(f'{part}_{color}.png', scale)
            old = source(f'{part}_{previous}.png', scale)
            if part.endswith('_s'):
                def tile(image):
                    result = Image.new('RGBA', (width*scale, height*scale))
                    for ty in range(0, result.height, image.height):
                        for tx in range(0, result.width, image.width):
                            result.paste(image, (tx, ty))
                    return result
                old, current = tile(old), tile(current)
            assert old.getchannel('A').tobytes() == current.getchannel('A').tobytes(), part
            mask = Image.new('L', old.size)
            # Changing opaque source pixels can safely cover cached CtrlImage
            # RGB. Do not make Lanczos edge pixels opaque during the fade.
            mask.putdata([255 if a[:3] != b[:3] and b[3] == 255 else 0
                          for a, b in zip(old.getdata(), current.getdata())])
            bounds = mask.getbbox()
            if bounds is None:
                continue
            key = f'info_frame_{color}_{index}'
            patch = old.crop(bounds)
            patch.putalpha(mask.crop(bounds))
            check_strip(assets, key, patch, [round(255*(14-i)/14) for i in range(15)], bands)
            expected_records.append(dict(color=color, previous=previous, part=index,
                source=f'{part}_{color}.png', resource=key, crop=list(bounds),
                x=x*scale+bounds[0], y=y*scale+bounds[1]))
    assert report['frames'] == expected_records, 'Frame manifest differs from source geometry'


def structure(assets, scale, report, bands):
    assert {k: report[k] for k in ('version', 'scale', 'fps', 'page_in_ms', 'page_out_ms', 'frame_ms')} == dict(version=1, scale=scale, fps=20, page_in_ms=400, page_out_ms=500, frame_ms=700)
    window = assets.tree.find('Window[@id="info"]')
    hub = window.find('Layout[@id="info_menu"]')
    assert (int(hub.get('width')), int(hub.get('height'))) == (413*scale, 282*scale)
    assert window[-1] is hub, 'Fresh menu default'
    states = assets.tree.find('Window[@id="info_page_state"]')
    assert states is not None and states.get('visible') == 'false'
    assert states.get('x') == states.get('y') == '0'
    expected_routes = routes()
    assert [n.get('id') for n in states] == [state(*r) for r in expected_routes], 'State list/default'
    frame_states = assets.tree.find('Window[@id="info_frame_state"]')
    assert frame_states is not None and frame_states.get('visible') == 'false'
    assert frame_states.get('x') == frame_states.get('y') == '0'
    assert [n.get('id') for n in frame_states] == [f'info_frame_{i}' for i in range(1, 8)]+['info_frame_idle'], 'Frame idle must be the initial state'
    for node in list(states)+list(frame_states):
        assert node.get('width') == node.get('height') == '1' and len(node) == 1
        assert node[0].tag == 'Image' and node[0].get('action') in (None, 'none')
        same(assets.image(node[0].get('image')), Image.new('RGBA', (1, 1)), 'Invisible state marker')
    assert len(report['routes']) == len(expected_routes)
    for record, (target, previous) in zip(report['routes'], expected_routes):
        sid = state(target, previous)
        gate = sid+'.isActive'
        key = 'info_page_in_'+target if target in PAGES else 'info_page_out_'+previous if target == 'menu' and previous else None
        assert record == dict(state=sid, target=target, previous=previous, resource=key, visible=gate), record
        contents = [n for n in hub if n.get('visible') == gate]
        assert contents, sid
        forwarders = [n for n in contents if n.get('up', '').startswith('info_menu_hit_')]
        buttons = [n for n in contents if n.tag == 'Button' and n.get('action') != 'none' and n not in forwarders]
        actions = [playback_action(n.get('action')) for n in buttons]
        assert not any('info.setLayout' in a for a in actions), ('Page change restarts frame', sid)
        if key:
            indexes = check_animation(assets, hub, key, gate, 37*scale, 35*scale, bands)
            backing = (previous if target in PAGES and previous else 'c_back')+'_jpg'
            candidates = [n for n in contents if n.get('image') == backing]
            assert len(candidates) == 1 and hub.index(candidates[0]) < min(indexes), ('Page backing', sid)
            assert (candidates[0].get('x'), candidates[0].get('y')) == (str(37*scale), str(35*scale))
            for node in buttons:
                if target == 'menu' and node.get('up', '').startswith('menu_'):
                    assert hub.index(node) < min(indexes), ('Menu art must remain below return fade', sid)
                else:
                    assert hub.index(node) > max(indexes), ('Navigation hidden by fade', sid)
        if target == 'menu' and previous:
            assert len(forwarders) == 4, ('Four timed menu forwarders required', sid)
            for index in range(4):
                source_buttons = [n for n in buttons if n.get('up') == f'menu_{index}_no']
                assert len(source_buttons) == 1, ('Original mapped menu button', sid, index)
                matches = [n for n in forwarders if n.get('up') == f'info_menu_hit_{index}']
                assert len(matches) == 1, ('Unique matching forwarder', sid, index)
                node, original = matches[0], source_buttons[0]
                assert node.tag == 'Button' and node.get('id') == f'info_menu_hit_{sid}_{index}'
                assert node.get('up') == node.get('over') == node.get('down'), 'Menu hit animation must not restart on hover'
                assert hub.index(node) > max(indexes), ('Forwarder above outgoing page', sid, index)
                for attr in ('action', 'tooltiptext', 'visible', 'x', 'y'):
                    assert node.get(attr) == original.get(attr), ('Menu forwarding mismatch', sid, index, attr)
                assert (int(node.get('x')), int(node.get('y'))) == menu_mask(assets, scale, index)
        else:
            assert not forwarders, ('Forwarders only belong to menu return states', sid)
        if target == 'menu':
            expected = [f'info_page_state.setLayout({state(f"c_sub_{g}_1")})' for g in range(1, 5)]
            expected.append('info_page_state.setLayout(info_state_about)')
            assert sorted(actions) == sorted(expected), (sid, actions)
        else:
            returning = state('menu', target) if target in PAGES else state('menu')
            assert f'info_page_state.setLayout({returning})' in actions, ('Return route', sid)
            if target in PAGES:
                expected = [f'info_page_state.setLayout({returning})']
                group, index = target.rsplit('_', 1)
                for neighbor in PAGES:
                    if neighbor.rsplit('_', 1)[0] == group and abs(int(neighbor.rsplit('_', 1)[1])-int(index)) == 1:
                        expected.append(f'info_page_state.setLayout({state(neighbor, target)})')
                assert sorted(actions) == sorted(expected), ('Adjacent routes', sid, actions)
        if target == 'c_sub_4_1':
            link = check_animation(assets, hub, 'info_link_in', gate, 127*scale, 118*scale, bands)
            assert min(link) > max(indexes), 'Web destination appears above page'
    for frame in report['frames']:
        gate = f'palette_{frame["color"]}.isActive and info_frame_{frame["color"]}.isActive'
        indexes = check_animation(assets, hub, frame['resource'], gate, frame['x'], frame['y'], bands)
        for color in range(1, 8):
            assert not visible(gate, f'main_{color}', flags={'info_frame_idle.isActive': True}), 'Initial palette must not animate'
            assert visible(gate, f'main_{color}', flags={f'info_frame_{color}.isActive': True}) == (color == frame['color'])
        before = hub[min(indexes)-1]
        assert before.tag == 'Image' and before.get('image') == frame['source'].replace('.', '_'), 'Original frame backing preserved'
        assert before.get('visible') == f'palette_{frame["color"]}.isActive'
    for node in assets.tree.iter('Button'):
        action = playback_action(node.get('action', ''))
        if node.get('up') == 'm_color_no_png':
            match = re.match(r'palette_state\.setLayout\(palette_([1-7])\);', action)
            assert match, 'Color cycle retains palette selection'
            assert action[match.end():].startswith(f'info_frame_state.setLayout(info_frame_{match[1]});'), 'Color cycle synchronizes the frame state'
        if 'main.setLayout(main_start)' in action:
            assert action.startswith('info_frame_state.setLayout(info_frame_idle);'), 'Replay clears frame animation before blue'
    for layout in window:
        if layout is hub:
            continue
        for node in layout:
            action = playback_action(node.get('action', ''))
            if 'info_page_state.setLayout' in action:
                assert action.startswith('info.setLayout(info_menu);'), 'Legacy navigation must enter shared layout'
    return hub


def hits(assets, scale, hub):
    """First/last frame ownership of retained controls in every content state."""
    count = 0
    for target, previous in routes():
        gate = state(target, previous)+'.isActive'
        for endpoint in ('first', 'last'):
            items = []
            for node in hub:
                if not visible(node.get('visible'), 'main_1', flags={gate: True, 'info_frame_1.isActive': True}):
                    continue
                if node.tag not in ('Image', 'Button'):
                    continue
                key = node.get('image') if node.tag == 'Image' else node.get('up')
                frames = int(assets.resources[key].get('nbframes', '1'))
                image = assets.frame(key, 0 if endpoint == 'first' else frames-1)
                box = (int(node.get('x', 0)), int(node.get('y', 0)),
                       int(node.get('width', image.width)), int(node.get('height', image.height)))
                items.append((node, box, image.getchannel('A')))
            canvas = ownership(items, (413*scale, 282*scale))
            for index, (node, (x, y, w, h), alpha) in enumerate(items, 1):
                if node.tag != 'Button' or node.get('action') == 'none':
                    continue
                found = canvas.crop((x, y, x+w, y+h))
                allowed = {index}
                if target == 'menu' and previous and node.get('up', '').startswith('menu_'):
                    menu_index = int(node.get('up').split('_')[1])
                    # Equivalent click forwarding is allowed only for the
                    # independently checked, same-region menu helper.
                    allowed.update(i for i, (other, _, _) in enumerate(items, 1)
                                   if other.get('up') == f'info_menu_hit_{menu_index}'
                                   and other.get('action') == node.get('action'))
                threshold = 0 if node.get('up', '').startswith('info_menu_hit_') else 100
                assert all(a <= threshold or owner in allowed for a, owner in zip(alpha.getdata(), found.getdata())), ('Blocked Info control', gate, endpoint, node.get('up'))
                count += 1
    return count


def mutations(assets, scale, report, bands):
    original = assets.tree
    cases = ('default', 'layout-switch', 'restart', 'under-fade', 'missing-backing', 'frame-gate', 'marker', 'frame-default', 'color-trigger', 'forward-action', 'forward-under-fade', 'menu-over-fade')
    for case in cases:
        assets.tree = deepcopy(original)
        hub = assets.tree.find('.//Layout[@id="info_menu"]')
        animation = next(n for n in hub if n.get('up', '').startswith('info_page_in_'))
        button = next(n for n in hub if n.tag == 'Button' and n.get('visible') == animation.get('visible') and n.get('action') != 'none')
        if case == 'default':
            states = assets.tree.find('Window[@id="info_page_state"]'); states.append(states[0])
        elif case == 'layout-switch': button.set('action', 'info.setLayout(info_menu);'+button.get('action'))
        elif case == 'restart': animation.set('over', 'c_back_jpg')
        elif case == 'under-fade': hub.remove(button); hub.insert(hub.index(animation), button)
        elif case == 'missing-backing':
            backing = next(n for n in hub if n.get('visible') == animation.get('visible') and n.get('image') == 'c_back_jpg'); hub.remove(backing)
        elif case == 'frame-gate': next(n for n in hub if n.get('up', '').startswith('info_frame_')).set('visible', 'true')
        elif case == 'marker': assets.tree.find('.//Layout[@id="info_state_menu"]/Image').set('image', 'c_back_jpg')
        elif case == 'frame-default':
            states = assets.tree.find('Window[@id="info_frame_state"]'); states.append(states[0])
        elif case == 'color-trigger':
            color = next(n for n in assets.tree.iter('Button') if n.get('up') == 'm_color_no_png')
            color.set('action', re.sub(r'info_frame_state.setLayout\(info_frame_[1-7]\);', '', color.get('action')))
        elif case.startswith('forward-') or case == 'menu-over-fade':
            forwarder = next(n for n in hub if n.get('up') == 'info_menu_hit_0')
            fade = next(n for n in hub if n.get('visible') == forwarder.get('visible') and n.get('up', '').startswith('info_page_out_'))
            if case == 'forward-action': forwarder.set('action', 'none')
            elif case == 'forward-under-fade': hub.remove(forwarder); hub.insert(hub.index(fade), forwarder)
            else:
                original_menu = next(n for n in hub if n.get('visible') == forwarder.get('visible') and n.get('up') == 'menu_0_no')
                hub.remove(original_menu); hub.insert(hub.index(fade)+1, original_menu)
        try:
            structure(assets, scale, report, bands)
        except AssertionError:
            pass
        else:
            raise AssertionError('Mutation escaped: '+case)
        finally:
            assets.tree = original
    # Prove the pixel oracle rejects corruption, rather than trusting metadata.
    original_frame = assets.frame
    def corrupt(key, frame=0, count=None):
        image = original_frame(key, frame, count)
        if key == 'info_page_in_c_sub_1_1' and frame == 4:
            image = image.copy(); r, g, b, a = image.getpixel((0, 0)); image.putpixel((0, 0), (r ^ 1, g, b, a))
        return image
    assets.frame = corrupt
    try:
        check_strip(assets, 'info_page_in_c_sub_1_1', source('c_sub_1_1.jpg', scale), [round(50+205*i/8) for i in range(9)], bands)
    except AssertionError:
        pass
    else:
        raise AssertionError('Pixel mutation escaped')
    finally:
        assets.frame = original_frame
    # A fractional Lanczos edge must never become an opaque animated region.
    record = next(r for r in report['frames'] if r['color'] == 1 and r['part'] == 4)
    key = record['resource']
    expected = original_frame(key, 0)
    candidates = [(x, y) for y in range(expected.height) for x in range(expected.width)
                  if expected.getpixel((x, y))[3] == 0]
    assert candidates, 'Sparse frame must retain transparent holes'
    point = candidates[0]
    if scale == 2:
        raw = source(record['source'], scale)
        left, top, _, _ = record['crop']
        fractional = [(x, y) for x, y in candidates if 0 < raw.getpixel((x+left, y+top))[3] < 255]
        assert fractional, '2x fixture must exercise partial-alpha edges'
        point = fractional[0]
    def opaque_edge(candidate, frame=0, count=None):
        image = original_frame(candidate, frame, count)
        if candidate == key and frame == 0:
            image = image.copy(); image.putpixel(point, image.getpixel(point)[:3]+(255,))
        return image
    assets.frame = opaque_edge
    try:
        check_strip(assets, key, expected, [round(255*(14-i)/14) for i in range(15)], bands)
    except AssertionError:
        pass
    else:
        raise AssertionError('Opaque fringe mutation escaped')
    finally:
        assets.frame = original_frame
    key = 'info_page_out_c_sub_1_1'
    resource = assets.resources[physical(assets, key, bands)[0]['id']]
    old_fps = resource.get('fps')
    resource.set('fps', '19')
    try:
        check_strip(assets, key, source('c_sub_1_1.jpg', scale), [round(255*(10-i)/10) for i in range(11)], bands)
    except AssertionError:
        pass
    else:
        raise AssertionError('Timing mutation escaped')
    finally:
        resource.set('fps', old_fps)
    def never_releases(key, frame=0, count=None):
        return original_frame(key, 0 if key == 'info_menu_hit_0' and frame == 1 else frame, count)
    assets.frame = never_releases
    try:
        menu_mask(assets, scale, 0)
    except AssertionError:
        pass
    else:
        raise AssertionError('Non-releasing menu forwarder mutation escaped')
    finally:
        assets.frame = original_frame
    return len(cases)+4


def memory_assets(scale, out):
    builder = Builder.__new__(Builder)
    builder.scale, builder.out, builder.ids = scale, Path(out), {}
    builder.theme = E.Element('Theme', version='2.0')
    main = E.SubElement(builder.theme, 'Window', id='main')
    for color in range(1, 8):
        layout = E.SubElement(main, 'Layout', id=f'main_{color}')
        target = color % 7+1
        E.SubElement(layout, 'Button', up='m_color_no_png', action=f'palette_state.setLayout(palette_{target});main.setLayout(main_{target})')
    images = {}
    def bitmap(self, name, im=None, frames=1, fps=0, loop=0, gridframes=1, prescaled=False):
        key = name.replace('.', '_')
        if key not in images:
            im = source_pixels(SOURCE/name) if im is None else im
            images[key] = im if prescaled else scaled(im, scale)
            self.ids[key] = images[key].size
            E.SubElement(self.theme, 'Bitmap', id=key, nbframes=str(frames), fps=str(fps), loop=str(loop))
        return key
    builder.bitmap = MethodType(bitmap, builder)
    builder.information()
    assets = ThemeAssets.__new__(ThemeAssets)
    assets.synthetic = True
    assets.tree = E.ElementTree(builder.theme)
    assets.resources = {n.get('id'): n for n in builder.theme.iter() if n.get('id')}
    assets.image = lambda key: images[key]
    def frame(key, frame=0, count=None):
        image = images[key]; height = image.height//(count or int(assets.resources[key].get('nbframes', '1')))
        return image.crop((0, frame*height, image.width, (frame+1)*height))
    assets.frame = frame
    return assets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    for scale in (1, 2):
        with tempfile.TemporaryDirectory(prefix='nfs-info-check-') as temporary:
            directory = Path(temporary) if args.self_test else SKIN/f'vlc-{scale}x'
            assets = memory_assets(scale, directory) if args.self_test else ThemeAssets(directory)
            report = json.loads((directory/'info-fades.json').read_text())
            bands = {} if args.self_test else json.loads((directory/'animation-bands.json').read_text())
            if not args.self_test:
                with zipfile.ZipFile(ROOT/'dist'/f'Need-for-Speed-Underground-{scale}x.vlt') as package:
                    assert E.tostring(E.fromstring(package.read('theme.xml')), method='c14n') == E.tostring(assets.tree, method='c14n'), 'Package differs from checked XML'
                    assert json.loads(package.read('info-fades.json')) == report, 'Packaged fade metadata differs'
                    # Runtime art lives in shared atlases. Comparing their bytes
                    # prevents a correct XML paired with stale packaged pixels.
                    for bitmap in assets.tree.findall('Bitmap'):
                        name = bitmap.get('file')
                        assert package.read(name) == (directory/name).read_bytes(), ('Packaged bitmap differs', name)
            art(assets, scale, report, bands)
            hub = structure(assets, scale, report, bands)
            count = hits(assets, scale, hub)
            rejected = mutations(assets, scale, report, bands)
            print(f'PASS {scale}x: all page/frame pixels and timings, {len(report["routes"])} states, {count} endpoint button checks, {rejected} rejected mutations')
    print('Offline limits: no native timer/input verification; interrupted fades are not reproduced; timed alpha-one menu buttons forward clicks during the 500ms return fade, then restore native hover feedback.')


if __name__ == '__main__':
    main()
