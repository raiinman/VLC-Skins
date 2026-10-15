"""Check action targets, original state coverage, sliders, and animation bounds."""
import re
from lxml import etree as E
from PIL import Image
from build import SKIN, ROOT, validate

for scale in (1,2):
    out=SKIN/f'vlc-{scale}x';validate(out)
    tree=E.parse(str(out/'theme.xml'))
    windows={w.get('id'):w for w in tree.findall('Window')}
    layouts={l.get('id'):w.get('id') for w in windows.values() for l in w}
    assert windows['main'][-1].get('id')=='main_start'
    assert windows['info'][-1].get('id')=='info_menu'
    for node in tree.iter():
        for attr in ('action','action1','action2'):
            for act in node.get(attr,'').split(';'):
                if '.setLayout(' in act:
                    w,l=re.fullmatch(r'(\w+)\.setLayout\((\w+)\)',act).groups()
                    assert layouts[l]==w,(act,layouts.get(l))
                elif act.endswith(('.show()','.hide()')):assert act.split('.')[0] in windows,act
        if node.tag=='Bitmap':
            with Image.open(out/node.get('file')) as im:
                frames=int(node.get('nbframes','1'));assert im.height%frames==0
        if node.tag=='Button':assert node.get('over') or node.get('tooltiptext') in ('Open shutter','Close shutter','Skip original startup animation')
    assert len(tree.findall('.//Slider[@value="volume"]'))==15
    assert len(tree.findall('.//Slider[@value="time"]'))==15
    assert len(tree.findall('.//Video'))==7
    assert len(tree.findall('.//Playtree'))==7
    assert len(tree.findall('.//Slider[@value="equalizer.band(0)"]'))==7
    for c in range(1,8):assert f'main_{c}' in layouts
    print(f'PASS {scale}x: action ownership, initial layouts, animation frames, palettes and control coverage')
