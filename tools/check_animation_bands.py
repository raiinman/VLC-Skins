"""Guard Windows startup cost while proving every animation pixel survives."""
import json
from PIL import Image
from build import SKIN
from assets import ThemeAssets

for scale in (1,2):
    root=SKIN/f'vlc-{scale}x';a=ThemeAssets(root)
    manifest=json.loads((root/'animation-bands.json').read_text())
    assert {'intro_sequence','intro_light_sequence'} <= manifest.keys()
    for node in a.tree.iter():
        if node.tag in ('Bitmap','SubBitmap') and int(node.get('nbframes','1'))>1:
            assert a.image(node.get('id')).height<=4096,'Oversized native animation mask'
    for key,item in manifest.items():
        original=Image.open(root/item['bitmap']['file']).convert('RGBA')
        frames=int(item['bitmap']['nbframes']);height=original.height//frames
        assert len(item['bands'])==(2 if frames<=11 else 16),'Excess animation timers'
        rebuilt=Image.new('RGBA',original.size)
        for band in item['bands']:
            node=a.resources[band['id']]
            for attr in ('nbframes','fps','loop'):
                assert node.get(attr)==item['bitmap'].get(attr),(key,attr)
            im=a.image(band['id']);h=band['height']
            for frame in range(frames):
                rebuilt.paste(im.crop((0,frame*h,im.width,(frame+1)*h)),(0,frame*height+band['y']))
        assert rebuilt.tobytes()==original.tobytes(),key
        origin=(53,52) if key=='intro_sequence' else (21,32) if 'light' in key else (54,52)
        for layout in a.tree.findall('.//Layout'):
            parts=[n for n in layout if n.get('up') in {b['id'] for b in item['bands']}]
            if not parts:continue
            assert len(parts)==len(item['bands']),(key,layout.get('id'))
            for part,band in zip(parts,item['bands']):
                assert part.get('up')==band['id']
                assert (int(part.get('x')),int(part.get('y')))==(origin[0]*scale,origin[1]*scale+band['y'])
                assert part.get('action')==('main.setLayout(main_1)' if key=='intro_sequence' else 'none')
    print(f'PASS {scale}x: bounded Windows masks; animation bands reconstruct every original frame exactly')
