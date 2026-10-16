"""Explicit confirmed playlist clearing through a capable companion host.

Plain VLTs hide the control until its owning host arms the capability. Native
playlist.del() deletes selected rows only and cannot implement this command.
"""
from lxml import etree as E
from PIL import Image

from hud_button_art import button_icon


def add(builder):
    root = builder.theme
    for state in ('no', 'hov', 'do'):
        builder.bitmap('playlist_clear_'+state+'.png', button_icon('clear', state, 29))
    for layout in root.findall('./Window[@id="tracks"]/Layout'):
        height = int(layout.get('height')) // builder.scale
        button = builder.button(layout, 'playlist_clear', 64, height-31,
            'playlist_clear_command.setLayout(playlist_clear_requested)',
            'Clear playlist...', lefttop='leftbottom',
            visible='playlist_clear_enabled.isActive')
        button.set('id', 'playlist_clear_button_'+layout.get('id'))
    marker = builder.bitmap('playlist_clear_marker', Image.new('RGBA', (1, 1), (0, 0, 0, 1)), prescaled=True)
    command = E.SubElement(root, 'Window', id='playlist_clear_command', x='-31000', y='-30100',
                          visible='true', dragdrop='false', playondrop='false')
    for suffix, width in [('requested', 162), ('ready', 161)]:
        layout = E.SubElement(command, 'Layout', id='playlist_clear_'+suffix, width=str(width), height='17')
        for name, x, action in [('ack', 0, 'playlist_clear_command.setLayout(playlist_clear_ready)'),
                                ('enable', 10, 'playlist_clear_capability.setLayout(playlist_clear_enabled)'),
                                ('disable', 20, 'playlist_clear_capability.setLayout(playlist_clear_disabled)')]:
            E.SubElement(layout, 'Image', id='playlist_clear_'+suffix+'_'+name,
                         image=marker, x=str(x), y='0', action2=action)
    capability = E.SubElement(root, 'Window', id='playlist_clear_capability', x='-31000', y='-30000',
                             visible='true', dragdrop='false', playondrop='false')
    for suffix, width in [('enabled', 172), ('disabled', 171)]:
        layout = E.SubElement(capability, 'Layout', id='playlist_clear_'+suffix, width=str(width), height='1')
        E.SubElement(layout, 'Image', id='playlist_clear_'+suffix+'_marker', image=marker, x='0', y='0')
