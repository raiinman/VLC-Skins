"""Guard Windows startup cost while proving every animation pixel survives."""
import json
import re
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
        count = (4 if scale == 2 and re.fullmatch(r'info_frame_[1-7]_[23]', key) and frames == 15 and original.height > 4096
                 else 2 if frames <= 15 else 16)
        assert len(item['bands']) == count, 'Unexpected animation timers'
        assert [(b['y'], b['height']) for b in item['bands']] == [
            (height*i//count, height*(i+1)//count-height*i//count) for i in range(count)
        ], ('Exact contiguous animation band boundaries', key)
        rebuilt=Image.new('RGBA',original.size)
        for band in item['bands']:
            node=a.resources[band['id']]
            for attr in ('nbframes','fps','loop'):
                assert node.get(attr)==item['bitmap'].get(attr),(key,attr)
            im=a.image(band['id']);h=band['height']
            for frame in range(frames):
                rebuilt.paste(im.crop((0,frame*h,im.width,(frame+1)*h)),(0,frame*height+band['y']))
        assert rebuilt.tobytes()==original.tobytes(),key
        origin=(37*scale,35*scale) if key.startswith('info_page_') else tuple(v*scale for v in ((53,52) if key=='intro_sequence' else (21,32) if 'light' in key else (54,52)))
        if key.startswith('info_frame_'):
            info=json.loads((root/'info-fades.json').read_text())
            part=next(p for p in info['frames'] if p['resource']==key)
            origin=(part['x'],part['y'])
        for layout in a.tree.findall('.//Layout'):
            parts=[n for n in layout if n.get('up') in {b['id'] for b in item['bands']}]
            if not parts:continue
            groups={p.get('visible') for p in parts}
            for group in groups:
                matching=[p for p in parts if p.get('visible')==group]
                assert len(matching)==len(item['bands']),(key,layout.get('id'),group)
                for part,band in zip(matching,item['bands']):
                    assert part.get('up')==band['id']
                    assert (int(part.get('x')),int(part.get('y')))==(origin[0],origin[1]+band['y'])
                    assert part.get('action')==('main.setLayout(main_1)' if key=='intro_sequence' else 'none')
    print(f'PASS {scale}x: bounded Windows masks; animation bands reconstruct every original frame exactly')
