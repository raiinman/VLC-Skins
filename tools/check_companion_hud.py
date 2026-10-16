"""Independent optional companion HUD contract and actual-VLT fixtures, offline."""
from copy import deepcopy
from functools import lru_cache
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from lxml import etree as E
from PIL import Image, ImageChops

from companion_hud_apply import AddonError, apply_companion_hud

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT/'dist/skin-support/companion-hud'
LAYOUTS = ('fullscreen_controls', 'video_hover_controls')
RESOURCES = {'yt_hud_settings_'+s for s in ('no', 'hov', 'do')} | {
    'yt_hud_cc_'+state+'_'+s for state in ('off', 'on') for s in ('no', 'hov', 'do')} | {'yt_hud_command_hit'}
WINDOWS = {'yt_playback_actions', 'yt_cc_indicator', 'yt_hud_availability'}
CONTROLS = {'yt_'+prefix+'_'+name for prefix in ('fullscreen', 'hover') for name in ('settings', 'cc')}


def parse(data):
    return E.fromstring(data, E.XMLParser(remove_blank_text=True, no_network=True, resolve_entities=False))


def canonical(tree):
    return E.tostring(tree, method='c14n')


def active(expression, flags):
    # The addon has only these two-term positive gates, not an arbitrary eval.
    return all(flags.get(token, False) for token in expression.split(' and '))


def validate(original_xml, changed_xml, payloads, frame):
    original, changed = parse(original_xml), parse(changed_xml)
    dtd = E.DTD(str(ROOT/'vendor/skin.dtd'))
    assert dtd.validate(changed), dtd.error_log
    nodes = {n.get('id'): n for n in changed.iter() if n.get('id')}
    assert len(nodes) == len([n for n in changed.iter() if n.get('id')]), 'ID collision'
    source_ids = {n.get('id') for n in original.iter() if n.get('id')}
    assert not source_ids & (RESOURCES | WINDOWS | CONTROLS)
    assert {n.get('id') for n in changed.findall('Bitmap') if n.get('id') not in source_ids} == RESOURCES
    for key in RESOURCES:
        node = nodes[key]
        assert node.tag == 'Bitmap' and node.get('file') in payloads
        image = Image.open(io.BytesIO(payloads[node.get('file')])).convert('RGBA')
        if key == 'yt_hud_command_hit':
            assert image.size == (3, 3) and set(image.getchannel('A').tobytes()) == {1}
        else:
            assert image.size == (25, 25)
            bounds = image.getchannel('A').getbbox()
            assert bounds and bounds[0]+bounds[2] == 25 and bounds[1]+bounds[3] == 25, ('Centered button region', key)
            ink = [(x,y) for y in range(25) for x in range(25)
                   if max(image.getpixel((x,y))[:3]) >= 110 and image.getpixel((x,y))[3]]
            assert ink, ('Missing readable glyph',key)
            width = max(x for x,y in ink)-min(x for x,y in ink)+1
            height = max(y for x,y in ink)-min(y for x,y in ink)+1
            readable = (width,height) == (11,11) if 'settings' in key else 11 <= width <= 13 and height == 7
            assert readable, ('Readable enlarged glyph',key,width,height)
            assert all((x-12)**2+(y-12)**2 <= 8**2 for x,y in ink), ('Inset glyph clearance',key)

    for family in ('settings', 'cc_off', 'cc_on'):
        assert len({payloads[nodes[f'yt_hud_{family}_{s}'].get('file')] for s in ('no', 'hov', 'do')}) == 3, 'Distinct native feedback states'
    actions = ('yt_playback_actions.setLayout(yt_playback_ready)', 'yt_cc_indicator.setLayout(yt_cc_on)',
               'yt_cc_indicator.setLayout(yt_cc_off)', 'yt_hud_availability.setLayout(yt_controls_available)',
               'yt_hud_availability.setLayout(yt_controls_unavailable)')
    requests = nodes['yt_playback_actions']
    assert dict(requests.attrib) == dict(id='yt_playback_actions', x='-31000', y='-30600', visible='true', dragdrop='false', playondrop='false')
    expected_routes = [('settings', 212), ('cc', 213), ('ready', 211)]
    assert [(n.get('id'), n.get('width'), n.get('height')) for n in requests] == [(f'yt_playback_{name}', str(width), '17') for name, width in expected_routes], 'Route widths/default'
    fingerprints = set()
    for name, width in expected_routes:
        layout = nodes['yt_playback_'+name]
        assert len(layout) == 5
        for index, (cell, action) in enumerate(zip(layout, actions)):
            suffix = ('reset', 'cc_on', 'cc_off', 'available', 'unavailable')[index]
            assert dict(cell.attrib) == dict(id=f'yt_{name}_{suffix}_cell', image='yt_hud_command_hit',
                    x=str(index*10), y='0', width='3', height='3', resize='scale', action2=action), 'Native command mapping'
            assert cell.tag == 'Image'
            assert index*10 <= index*10+1 < index*10+3
        fingerprints.add((width, 17))
    for window, y, layouts in (
        ('yt_cc_indicator', -30500, [('yt_cc_on', 222), ('yt_cc_off', 221)]),
        ('yt_hud_availability', -30400, [('yt_controls_available', 223), ('yt_controls_unavailable', 224)])):
        node = nodes[window]
        assert dict(node.attrib) == dict(id=window, x='-31000', y=str(y), visible='false', dragdrop='false', playondrop='false')
        assert [(n.get('id'), n.get('width'), n.get('height')) for n in node] == [(key, str(width), '1') for key, width in layouts]
        for key, width in layouts:
            layout = nodes[key]
            assert len(layout) == 1 and layout[0].tag == 'Image'
            assert dict(layout[0].attrib) == dict(id=key+'_marker', image='yt_hud_command_hit', x='0', y='0', width='1', height='1', resize='scale')
            fingerprints.add((width, 1))
    for window in changed.findall('Window'):
        if window.get('id') not in WINDOWS:
            assert not fingerprints & {(int(n.get('width')), int(n.get('height'))) for n in window}, 'Signal geometry collision'
    restored = deepcopy(changed)
    for layout_id, prefix, gate in (
        ('fullscreen_controls', 'fullscreen', 'fullscreenController.isVisible'),
        ('video_hover_controls', 'hover', 'video_hover_controls.isActive')):
        layout = nodes[layout_id]
        new = [nodes[f'yt_{prefix}_{name}'] for name in ('settings', 'cc')]
        assert list(layout)[-2:] == new, 'Addon controls must be above retained controls'
        for node, name, x in zip(new, ('settings', 'cc'), (300, 330)):
            assert (node.get('x'), node.get('y')) == (str(x), '0')
            assert node.get('visible') == gate+' and yt_controls_available.isActive'
            assert not active(node.get('visible'), {gate: True, 'yt_controls_unavailable.isActive': True}), 'Unavailable controls must be hidden'
            assert active(node.get('visible'), {gate: True, 'yt_controls_available.isActive': True})
            assert not active(node.get('visible'), {'yt_controls_available.isActive': True})
            if name == 'settings':
                assert node.tag == 'Button' and node.get('action') == 'yt_playback_actions.setLayout(yt_playback_settings)'
                assert [node.get(attr) for attr in ('up', 'over', 'down')] == ['yt_hud_settings_'+s for s in ('no', 'hov', 'do')]
            else:
                assert node.tag == 'Checkbox' and node.get('state') == 'yt_cc_on.isActive'
                assert node.get('action1') == node.get('action2') == 'yt_playback_actions.setLayout(yt_playback_cc)'
                for state, color in (('1', 'off'), ('2', 'on')):
                    assert [node.get(attr+state) for attr in ('up', 'over', 'down')] == [f'yt_hud_cc_{color}_{s}' for s in ('no', 'hov', 'do')]
        seek = layout.find('Slider[@value="time"]')
        assert seek.get('points') == '(0,0),(281,0)' and seek.get('x') == seek.get('y') == '12'
        # Native CtrlSlider centers the ORIGINAL thumb with integer half sizes.
        # Test all feedback masks at both endpoints against the added buttons.
        for resource in {seek.get('up'), seek.get('down'), seek.get('over', seek.get('up'))}:
            thumb = frame(resource)
            assert thumb.size == (15, 17), 'Retain full original seek thumb'
            for endpoint in (12, 293):
                footprint = Image.new('L', (361, 64))
                # Win32 regions include every nonzero-alpha pixel, even alpha1.
                # Raw alpha multiplication would round 1*1/255 down to zero.
                footprint.paste(thumb.getchannel('A').point(lambda a: 255 if a else 0),
                                (endpoint-thumb.width//2, 12-thumb.height//2))
                assert footprint.getbbox() is not None
                for button in new:
                    references = [button.get(a) for a in ('up', 'over', 'down', 'up1', 'over1', 'down1', 'up2', 'over2', 'down2') if button.get(a)]
                    for key in references:
                        icon = Image.open(io.BytesIO(payloads[nodes[key].get('file')])).convert('RGBA')
                        mask = Image.new('L', footprint.size)
                        mask.paste(icon.getchannel('A').point(lambda a: 255 if a else 0),
                                   (int(button.get('x')), int(button.get('y'))))
                        assert ImageChops.multiply(footprint, mask).getbbox() is None, ('Seek thumb overlaps addon', key, endpoint)
        for button in new:
            references = [button.get(a) for a in ('up','over','down','up1','over1','down1','up2','over2','down2') if button.get(a)]
            for key in references:
                alpha = Image.open(io.BytesIO(payloads[nodes[key].get('file')])).convert('RGBA').getchannel('A')
                assert all(alpha.getpixel((x,y)) == 0 for x in range(25) for y in range(25)
                           if x in (0,24) or y in (0,24)), ('Transparent addon margin',key)
        mirror = restored.find(f'.//Layout[@id="{layout_id}"]')
        for node in list(mirror):
            if node.get('id') in CONTROLS: mirror.remove(node)
        old_seek = mirror.find('Slider[@value="time"]')
        old_seek.set('points', '(0,0),(336,0)')
        list(mirror)[list(mirror).index(old_seek)-1].set('width', '336')
    for node in list(restored):
        if node.get('id') in RESOURCES | WINDOWS: restored.remove(node)
    assert canonical(restored) == canonical(original), 'An unrelated native node/asset/transport/action changed'
    return changed


def mutations(xml, original, payloads, frame):
    for kind in ('signal-collision', 'trigger-default', 'overlap', 'native-moved', 'availability', 'cc-boolean', 'low-alpha-overlap'):
        tree = parse(xml)
        candidate_payloads, candidate_frame = payloads, frame
        if kind == 'signal-collision':
            tree.find('Window[@id="yt_playback_actions"]/Layout').set('width', '133')
        elif kind == 'trigger-default':
            window = tree.find('Window[@id="yt_playback_actions"]'); window.append(window[0])
        elif kind == 'overlap': tree.find('.//Button[@id="yt_hover_settings"]').set('x', '292')
        elif kind == 'native-moved': tree.find('.//Layout[@id="video_hover_controls"]/Button').set('x', '9')
        elif kind == 'availability': tree.find('.//Button[@id="yt_hover_settings"]').set('visible', 'true')
        elif kind == 'cc-boolean': tree.find('.//Checkbox[@id="yt_hover_cc"]').set('state', 'vlc.hasSubtitles')
        else:
            candidate_payloads = dict(payloads)
            name = tree.find('Bitmap[@id="yt_hud_settings_no"]').get('file')
            icon = Image.open(io.BytesIO(payloads[name])).convert('RGBA')
            # Symmetric edge pixels retain centered bounds. Only the left one
            # intersects the max-position thumb, at global (300,12).
            for x in (0, 24): icon.putpixel((x, 12), icon.getpixel((x, 12))[:3]+(1,))
            encoded = io.BytesIO(); icon.save(encoded, format='PNG')
            candidate_payloads[name] = encoded.getvalue()
            def candidate_frame(key):
                thumb = frame(key).copy()
                thumb.putpixel((14, 8), thumb.getpixel((14, 8))[:3]+(1,))
                return thumb
        try: validate(original, E.tostring(tree), candidate_payloads, candidate_frame)
        except AssertionError as error:
            if kind == 'low-alpha-overlap':
                assert error.args and error.args[0][0] == 'Seek thumb overlaps addon', 'Low-alpha mutation must reach overlap oracle'
        else: raise AssertionError('Mutation accepted: '+kind)
    return 7


def main():
    with tempfile.TemporaryDirectory(prefix='companion-hud-check-', dir=ROOT.parent/'work') as temporary:
        temporary = Path(temporary)
        for scale in (1, 2):
            source = ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt'
            with zipfile.ZipFile(source) as archive:
                original = archive.read('theme.xml')
                xml, payloads = apply_companion_hud(original, ADDON)
                tree = parse(original)
                resources = {n.get('id'): n for n in tree.iter() if n.get('id')}
                @lru_cache(maxsize=2)
                def image(name):
                    return Image.open(io.BytesIO(archive.read(name))).convert('RGBA')
                @lru_cache(maxsize=32)
                def frame(key):
                    node = resources[key]
                    if node.tag == 'SubBitmap':
                        x,y,w,h = (int(node.get(k)) for k in ('x', 'y', 'width', 'height'))
                        return image(node.getparent().get('file')).crop((x,y,x+w,y+h))
                    return image(node.get('file'))
                validate(original, xml, payloads, frame)
                rejected = mutations(xml, original, payloads, frame)
                derived = temporary/f'derived-{scale}x.vlt'
                with zipfile.ZipFile(derived, 'w') as target:
                    for member in archive.infolist():
                        target.writestr(deepcopy(member), xml if member.filename == 'theme.xml' else archive.read(member))
                    for name, data in payloads.items(): target.writestr(name, data)
                with zipfile.ZipFile(derived) as target:
                    assert target.testzip() is None
                    assert set(target.namelist()) == set(archive.namelist()) | set(payloads)
                    for name in archive.namelist():
                        assert target.getinfo(name).compress_type == archive.getinfo(name).compress_type, ('Original compression method changed', name)
                        if name != 'theme.xml': assert archive.read(name) == target.read(name), ('Original payload changed', name)
                try: apply_companion_hud(xml, ADDON)
                except AddonError: pass
                else: raise AssertionError('Duplicate injection accepted')
                bad = temporary/f'bad-{scale}'
                shutil.copytree(ADDON, bad)
                manifest_path = bad/'manifest.json'
                manifest = json.loads(manifest_path.read_text())
                manifest['assets'][0]['file'] = '../escape.png'
                manifest_path.write_text(json.dumps(manifest))
                try: apply_companion_hud(original, bad)
                except AddonError: pass
                else: raise AssertionError('Unsafe path accepted')
                assert bad.resolve() != temporary.resolve() and bad.resolve().is_relative_to(temporary.resolve()), 'Unsafe private fixture deletion'
                shutil.rmtree(bad); shutil.copytree(ADDON, bad)
                asset = next(bad.glob('settings_no.png')); asset.write_bytes(asset.read_bytes()+b'corrupt')
                try: apply_companion_hud(original, bad)
                except AddonError: pass
                else: raise AssertionError('Modified asset accepted')
                print(f'PASS {scale}x: actual VLT, DTD, unchanged source XML/payloads, native routes, gated controls, feedback and endpoint masks; {rejected+3} mutations rejected')
    print('Offline only. Host dispatch, caption/availability synchronization and native interaction require companion integration tests.')


if __name__ == '__main__': main()
