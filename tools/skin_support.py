"""Bridge original effects to the optional, process-scoped Windows helper.

Skins2 has no sound action or windowed video hover event. Offscreen native
windows carry commands without covering media or replacing playback actions.
"""
import json
import re
import shutil

from lxml import etree as E
from PIL import Image


SOUNDS = [('button', 'button.wav'), ('shutter', 'shutter.wav'),
          ('intro', 'intro4.wav'), ('info', 'imode.wav'), ('logo', 'eagames.wav')]


def playback_action(value):
    """Retain the complete original action sequence for independent audits."""
    return re.sub(r'^(?:nfs_fx_(button|shutter|intro|info|logo)\.setLayout\(nfs_fx_\1_trigger\);)+', '', value)


def add_support(builder):
    root, out, source = builder.theme, builder.out, builder.out.parent / 'original'
    # Recover click sound assignments from the supplied WMP document rather
    # than assuming every control originally made a noise.
    wms = E.fromstring((source / 'nfs.wms').read_bytes(), E.XMLParser(recover=True))
    by_image = {}
    for node in wms.iter():
        match = re.search(r"checkSoundPref\('([^']+)'\)", node.get('onClick') or '')
        if match and node.get('image'):
            by_image[node.get('image').replace('.', '_')] = next(key for key, name in SOUNDS if name == match[1])
    for node in list(root.iter()):
        if node.tag not in ('Button', 'Checkbox'):
            continue
        key = node.get('up', node.get('up1', ''))
        if key.startswith('compact_'):key=key.removeprefix('compact_')
        effect = by_image.get(key)
        if key.startswith('shutter_locked'):
            effect = 'shutter'
        for attr in ('action', 'action1', 'action2'):
            action = node.get(attr)
            if not action or action == 'none':
                continue
            sound = effect
            if 'main.setLayout(main_start)' in action:
                sound = 'intro'
            if sound:
                events = f'nfs_fx_{sound}.setLayout(nfs_fx_{sound}_trigger);'
                if key == 'm_info_no_png' and 'info.show()' in action:
                    # WMP plays the click, then the information-view load sound.
                    events += 'nfs_fx_info.setLayout(nfs_fx_info_trigger);'
                node.set(attr, events + action)

    marker = builder.bitmap('nfs_effect_marker', Image.new('RGBA', (1, 1), (0, 0, 0, 255)), prescaled=True)
    sounds = []
    (out / 'sounds').mkdir(exist_ok=True)
    for index, (key, filename) in enumerate(SOUNDS):
        ready_width, width, height = 41 + index, 51 + index, 17
        window = E.SubElement(root, 'Window', id='nfs_fx_' + key, x='-31000', y='-31000',
                              visible='true', dragdrop='false', playondrop='false')
        # Layout changes resize an already shown offscreen window. Unlike
        # Window.show(), this does not call Win32 ShowWindow(SW_SHOW).
        states = [('ready', ready_width), ('trigger', width)]
        if key != 'intro':
            states.reverse()
        for state, state_width in states:
            layout = E.SubElement(window, 'Layout', id=f'nfs_fx_{key}_{state}', width=str(state_width), height=str(height))
            E.SubElement(layout, 'Image', image=marker, x='0', y='0', width=str(state_width), height=str(height),
                         resize='scale', action2=f'nfs_fx_{key}.setLayout(nfs_fx_{key}_ready)')
        path = 'sounds/' + filename
        shutil.copyfile(source / filename, out / path)
        sounds.append(dict(id=key, file=path, width=width, readyWidth=ready_width, height=height))
    command = E.SubElement(root, 'Window', id='nfs_hover_command', x='-31000', y='-30900',
                           visible='true', dragdrop='false', playondrop='false')
    layout = E.SubElement(command, 'Layout', id='nfs_hover_command_layout', width='133', height='17')
    for x, target, window in [(0, 'video_hover_controls', 'videoHoverController'), (33, 'video_hover_closed', 'videoHoverController'),
                              (66, 'hover_volume_expanded', 'hover_volume_state'), (99, 'hover_volume_collapsed', 'hover_volume_state')]:
        E.SubElement(layout, 'Image', image=marker, x=str(x), y='0', width='33', height='17',
                     resize='scale', action2=f'{window}.setLayout({target})')
    manifest = dict(schemaVersion=2, scale=builder.scale, sounds=sounds,
                    command=dict(width=133, height=17, showX=2, hideX=35, y=2,volumeShowX=68,volumeHideX=101),
                    hover=dict(width=361, height=64,closedWidth=362, closedHeight=1),
                    video=dict(width=708 * builder.scale, height=440 * builder.scale))
    (out / 'nfs-effects.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return {'nfs-effects.json'} | {s['file'] for s in sounds}
