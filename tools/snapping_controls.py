"""Capability-gated native snapping toggle, shared by both skin scales."""
from lxml import etree as E
from PIL import Image

from hud_button_art import snapping_button


def add(builder):
    root = builder.theme
    native_text = builder.scale == 1
    if native_text:
        for name,size in [('snap_label',13),('snap_status',12)]:
            E.SubElement(root,'Font',id=name,file='assets/FreeSans.ttf',size=str(size))
    for mode in ('off', 'on'):
        for state in ('no', 'hov', 'do'):
            builder.bitmap(f'snapping_{mode}_{state}.png',
                           snapping_button(state, mode == 'on', native_text=native_text))
    action = 'snapping_command.setLayout(snapping_requested)'
    for layout in root.findall('./Window[@id="tracks"]/Layout'):
        height = int(layout.get('height')) // builder.scale
        button = builder.check(layout, 'snapping_off', 96, height-31,
            'snapping_enabled.isActive', action, action,
            'Enable pane and screen snapping', prefix2='snapping_on',
            lefttop='leftbottom',
            visible='snapping_enabled.isActive or snapping_disabled.isActive')
        button.set('tooltiptext2', 'Disable pane and screen snapping')
        button.set('id', 'snapping_button_'+layout.get('id'))
        if native_text:
            for name,text,x,width,font,gate,color in [
                ('label','SNAP',103,39,'snap_label',button.get('visible'),'#E7EDF0'),
                ('on','ON',144,27,'snap_status','snapping_enabled.isActive','#8FE1F3'),
                ('off','OFF',144,27,'snap_status','snapping_disabled.isActive','#D5DBDF')]:
                E.SubElement(layout,'Text',id='snapping_'+name+'_'+layout.get('id'),
                    text=text,x=str(x),y=str(height-(22 if name=='label' else 21)),width=str(width),font=font,
                    alignment='center',scrolling='none',focus='false',color=color,
                    visible=gate,lefttop='leftbottom')
    marker = builder.bitmap('snapping_marker',
        Image.new('RGBA', (1, 1), (0, 0, 0, 1)), prescaled=True)
    command = E.SubElement(root, 'Window', id='snapping_command', x='-31000', y='-29800',
                          visible='true', dragdrop='false', playondrop='false')
    cells = [('ack', 0, 'snapping_command.setLayout(snapping_ready)'),
             ('on', 10, 'snapping_state.setLayout(snapping_enabled)'),
             ('off', 20, 'snapping_state.setLayout(snapping_disabled)'),
             ('unavailable', 30, 'snapping_state.setLayout(snapping_unavailable)')]
    for suffix, width in [('requested', 192), ('ready', 191)]:
        layout = E.SubElement(command, 'Layout', id='snapping_'+suffix,
                              width=str(width), height='17')
        for name, x, dispatch in cells:
            E.SubElement(layout, 'Image', id='snapping_'+suffix+'_'+name,
                         image=marker, x=str(x), y='0', action2=dispatch)
    state = E.SubElement(root, 'Window', id='snapping_state', x='-31000', y='-29700',
                        visible='true', dragdrop='false', playondrop='false')
    for suffix, width in [('enabled', 202), ('disabled', 203), ('unavailable', 201)]:
        layout = E.SubElement(state, 'Layout', id='snapping_'+suffix,
                              width=str(width), height='1')
        E.SubElement(layout, 'Image', id='snapping_'+suffix+'_marker',
                     image=marker, x='0', y='0')
