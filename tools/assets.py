"""Read standalone and atlas-backed theme bitmaps for review/checks."""
from functools import lru_cache
import json
from lxml import etree as E
from PIL import Image


class ThemeAssets:
    def __init__(self, directory):
        self.directory=directory
        self.tree=E.parse(str(directory/'theme.xml'))
        self.resources={n.get('id'):n for n in self.tree.iter() if n.get('id')}
        manifest=directory/'animation-bands.json'
        if manifest.exists():
            # Canonical strips are offline references; VLC loads only the bands.
            for key,item in json.loads(manifest.read_text()).items():
                self.resources[key]=E.Element('Bitmap',**item['bitmap'])

    @lru_cache(maxsize=32)
    def file(self, name):
        return Image.open(self.directory/name).convert('RGBA')

    @lru_cache(maxsize=512)
    def image(self, key):
        node=self.resources[key]
        if node.tag=='SubBitmap':
            x,y,w,h=[int(node.get(k)) for k in ('x','y','width','height')]
            return self.file(node.getparent().get('file')).crop((x,y,x+w,y+h))
        return self.file(node.get('file'))

    @lru_cache(maxsize=512)
    def frame(self, key, frame=0, count=None):
        node=self.resources[key];image=self.image(key)
        n=count or int(node.get('nbframes','1'));h=image.height//n
        return image.crop((0,frame*h,image.width,(frame+1)*h))


def visible(expression, active='main_1', windows=None, flags=None):
    windows=windows or {};flags=flags or {}
    import re
    match=re.fullmatch(r'main_([1-7])(?:_.*)?',active)
    color=match.group(1) if match else '1' if active=='main_start' else None
    palette={f'palette_{color}.isActive':True} if color else {}
    values={active+'.isActive':True,**palette,**{k+'.isVisible':v for k,v in windows.items()},**flags}
    parts=[]
    for token in re.findall(r'\(|\)|[A-Za-z0-9_.]+',expression or 'true'):
        if token in ('and','or','not','(',')'):parts.append(token)
        elif token=='true':parts.append('True')
        elif token=='false':parts.append('False')
        else:parts.append(str(bool(values.get(token,False))))
    return bool(eval(' '.join(parts),{'__builtins__':{}},{}))
