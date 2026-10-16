"""Generate Settings/CC assets and XML templates for companion-derived skins.

This writes only the addon folder. It never changes core VLTs, the core helper,
installed profiles or a running player. The host owns actual caption/settings
behavior and enables these controls only for its ready managed YouTube entry.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as E

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'dist/skin-support/companion-hud'
FONT = ROOT / 'vendor/FreeSans.ttf'
STATES = ('no', 'hov', 'do')
COLORS = {'no': ((14,22,29),(62,76,85),(194,220,234)),
          'hov': ((20,34,43),(32,174,221),(242,250,255)),
          'do': ((8,14,20),(32,174,221),(242,250,255))}
ASSET_PREFIX = 'companion-hud/'
COMMANDS = [('reset', 0, 'yt_playback_actions.setLayout(yt_playback_ready)'),
            ('cc_on', 10, 'yt_cc_indicator.setLayout(yt_cc_on)'),
            ('cc_off', 20, 'yt_cc_indicator.setLayout(yt_cc_off)'),
            ('available', 30, 'yt_hud_availability.setLayout(yt_controls_available)'),
            ('unavailable', 40, 'yt_hud_availability.setLayout(yt_controls_unavailable)')]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def icon(kind, state):
    """Shared beveled face, small inset glyph and exact transparent margin."""
    from hud_button_art import button_icon
    return button_icon(kind,state,19)


def xml_template():
    root = E.Element('CompanionHudAddon', schemaVersion='1')
    resources = E.SubElement(root, 'Resources')
    for kind in ('settings','cc_off','cc_on'):
        for state in STATES:
            key = f'yt_hud_{kind}_{state}'
            E.SubElement(resources, 'Bitmap', id=key, file=ASSET_PREFIX+f'{kind}_{state}.png', alphacolor='#FF00FF')
    E.SubElement(resources, 'Bitmap', id='yt_hud_command_hit', file=ASSET_PREFIX+'command_hit.png', alphacolor='#FF00FF')
    controllers = E.SubElement(root, 'Controllers')
    for layout, prefix, gate in [('fullscreen_controls','yt_fullscreen','fullscreenController.isVisible'),
                                  ('video_hover_controls','yt_hover','video_hover_controls.isActive')]:
        parent = E.SubElement(controllers, 'Controller', layout=layout)
        visibility = gate+' and yt_controls_available.isActive'
        E.SubElement(parent,'Button', id=prefix+'_settings', x='307', y='2',
                     up='yt_hud_settings_no', over='yt_hud_settings_hov', down='yt_hud_settings_do',
                     action='yt_playback_actions.setLayout(yt_playback_settings)',
                     tooltiptext='Playback settings', visible=visibility)
        attrs = dict(id=prefix+'_cc', x='332', y='2', state='yt_cc_on.isActive',
                     action1='yt_playback_actions.setLayout(yt_playback_cc)',
                     action2='yt_playback_actions.setLayout(yt_playback_cc)',
                     tooltiptext1='Turn captions on', tooltiptext2='Turn captions off', visible=visibility)
        for value, kind in [('1','cc_off'),('2','cc_on')]:
            for attribute, state in [('up','no'),('over','hov'),('down','do')]:
                attrs[attribute+value] = f'yt_hud_{kind}_{state}'
        E.SubElement(parent,'Checkbox', **attrs)
    windows = E.SubElement(root, 'Windows')
    action = E.SubElement(windows,'Window', id='yt_playback_actions', x='-31000', y='-30600',
                          visible='true', dragdrop='false', playondrop='false')
    for suffix, width in [('settings',212),('cc',213),('ready',211)]:
        layout = E.SubElement(action,'Layout',id='yt_playback_'+suffix,width=str(width),height='17')
        for name, x, command in COMMANDS:
            E.SubElement(layout,'Image', id=f'yt_{suffix}_{name}_cell', image='yt_hud_command_hit',
                         x=str(x),y='0',width='3',height='3',resize='scale',action2=command)
    for window_id, y, states in [('yt_cc_indicator',-30500,[('yt_cc_on',222),('yt_cc_off',221)]),
                                 ('yt_hud_availability',-30400,[('yt_controls_available',223),('yt_controls_unavailable',224)])]:
        window = E.SubElement(windows,'Window',id=window_id,x='-31000',y=str(y),
                              visible='false',dragdrop='false',playondrop='false')
        for identifier, width in states:
            layout = E.SubElement(window,'Layout',id=identifier,width=str(width),height='1')
            E.SubElement(layout,'Image',id=identifier+'_marker',image='yt_hud_command_hit',
                         x='0',y='0',width='1',height='1',resize='scale')
    E.indent(root)
    return E.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'


def generate(output):
    output.mkdir(parents=True,exist_ok=True)
    assets = []
    for kind in ('settings','cc_off','cc_on'):
        for state in STATES:
            filename = f'{kind}_{state}.png'
            image = icon(kind,state)
            image.save(output/filename)
            assets.append(dict(id=f'yt_hud_{kind}_{state}',file=filename,
                               sha256=sha256((output/filename).read_bytes()),width=19,height=19))
    Image.new('RGBA',(3,3),(0,0,0,1)).save(output/'command_hit.png')
    assets.append(dict(id='yt_hud_command_hit',file='command_hit.png',
                       sha256=sha256((output/'command_hit.png').read_bytes()),width=3,height=3))
    template = xml_template()
    (output/'addon.xml').write_bytes(template)
    manifest = dict(schemaVersion=1,assetPrefix=ASSET_PREFIX,
                    scope='Companion-derived skins only; validated core VLT/helper remain unchanged.',
                    assets=assets,template=dict(file='addon.xml',sha256=sha256(template)),
                    physicalArtwork=dict(width=360,height=64),
                    controllers=[dict(layout='fullscreen_controls',width=360,height=64),
                                 dict(layout='video_hover_controls',width=361,height=64)],
                    seek=dict(x=12,y=12,length=288,oldLength=336,
                              sliderPoints='(0,0),(288,0)',railWidth=288),
                    rectangles=dict(settings=[307,2,19,19],cc=[332,2,19,19]),
                    commandWindow=dict(id='yt_playback_actions',x=-31000,y=-30600,visible=True,height=17,
                        layouts=dict(settings=dict(id='yt_playback_settings',width=212),
                                     cc=dict(id='yt_playback_cc',width=213),
                                     ready=dict(id='yt_playback_ready',width=211)),default='yt_playback_ready',
                        cellSize=[3,3],invoke={name:[x+1,1] for name,x,_ in COMMANDS},
                        actions={name:command for name,_,command in COMMANDS}),
                    captionIndicator=dict(window='yt_cc_indicator',x=-31000,y=-30500,visible=False,
                                          on=dict(id='yt_cc_on',width=222,height=1),
                                          off=dict(id='yt_cc_off',width=221,height=1),default='yt_cc_off',
                                          authority='Host queries actual native caption state; never infer from an invented subtitle boolean.'),
                    availability=dict(window='yt_hud_availability',x=-31000,y=-30400,visible=False,
                                      available=dict(id='yt_controls_available',width=223,height=1),
                                      unavailable=dict(id='yt_controls_unavailable',width=224,height=1),
                                      default='yt_controls_unavailable',
                                      policy='Enable only for ready managed YouTube entries; hide for unmanaged/no entry.'),
                    integration=['Copy Resources children before Window nodes; copy Windows children as root Windows.',
                                 'Append each Controller child to its matching existing layout without scaling.',
                                 'Shorten only its existing time Slider points and rail width to288; retain original thumb/resources.',
                                 'Preserve every lower transport/time/volume/fullscreen/close node and the existing bar bounds.',
                                 'Host scopes HWND discovery and commands to its owned VLC process; poll sentinel widths and reset by command cell.',
                                 'CC actions request a host toggle; only actual native caption observations update yt_cc_indicator.',
                                 'These templates are addon fragments, not a standalone VLC skin or a native test result.'])
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest


def preview(directory):
    directory.mkdir(parents=True,exist_ok=True)
    board = Image.new('RGB',(690,260),(13,17,21))
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype(str(FONT),13)
    draw.text((10,8),'Settings / CC off / CC on, native 19px and 3x asset preview',font=font,fill='white')
    for row,kind in enumerate(('settings','cc_off','cc_on')):
        y = 40+row*72
        draw.text((10,y),kind,font=font,fill='white')
        for column,state in enumerate(STATES):
            image = icon(kind,state)
            for light in (False,True):
                x = 120+column*185+(85 if light else 0)
                panel = Image.new('RGBA',(80,60),'white' if light else '#0D1115')
                panel.alpha_composite(image,(0,20))
                panel.alpha_composite(image.resize((57,57),Image.Resampling.NEAREST),(23,0))
                board.paste(panel.convert('RGB'),(x,y+4))
    # Exact4x views are separate from the compact overview's native/3x lanes.
    board.save(directory/'companion-hud-overview.png')
    for kind in ('settings','cc_off','cc_on'):
        sheet = Image.new('RGB',(6*88,100),'#0D1115')
        d = ImageDraw.Draw(sheet)
        for i,state in enumerate(STATES):
            for light in (False,True):
                x=(i*2+light)*88
                panel=Image.new('RGBA',(76,76),'white' if light else '#0D1115')
                panel.alpha_composite(icon(kind,state).resize((76,76),Image.Resampling.NEAREST))
                sheet.paste(panel.convert('RGB'),(x,20))
                d.text((x,2),state,font=font,fill='white')
        sheet.save(directory/(kind+'-4x.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    parser.add_argument('--preview-dir',type=Path)
    args = parser.parse_args()
    manifest = generate(args.output)
    if args.preview_dir:
        preview(args.preview_dir)
    print(f'{len(manifest["assets"])} PNGs and addon.xml/manifest.json: {args.output}')
    print('addon.xml SHA256: '+manifest['template']['sha256'])


if __name__ == '__main__':
    main()
