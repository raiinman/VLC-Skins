"""Offline input-layer regression check using VLC's documented control hit rules.

This checks the built XML and pixels; it is not native mouse automation.
"""
from collections import Counter
from PIL import Image
from assets import ThemeAssets, visible
from build import SKIN

SOURCE_BUTTONS={'m_'+p for p in ('min','full','close','open','vis','pl','eq','next','stop','play','prev','color','info','shutter')}

def source_button(node):
    if node is None or node.tag not in ('Button','Checkbox'):return None
    key=node.get('up') or node.get('up1') or ''
    if key.startswith('shutter_locked'):return 'm_shutter'
    return next((p for p in SOURCE_BUTTONS if key==p+'_no_png' or p=='m_shutter' and key==p+'_do_png'),None)


def hit_layers(assets,layout,active,flags=None):
    layers=[]
    for node in reversed(list(layout)):
        if not visible(node.get('visible'),active,flags=flags):continue
        key=None
        if node.tag=='Image':key=node.get('image')
        elif node.tag=='Button':key=node.get('up')
        elif node.tag=='Checkbox':
            key=node.get('up2') if visible(node.get('state'),active,flags=flags) else node.get('up1')
        elif node.tag=='Slider':
            bg=node.find('SliderBackground')
            if bg is not None:
                im=assets.frame(bg.get('image'),count=int(bg.get('nbvert','1')))
                layers.append((node,int(node.get('x',0)),int(node.get('y',0)),im.width,im.height,im.getchannel('A'),False,True,True))
            continue
        else:continue
        resource=assets.resources[key];im=assets.frame(key,int(resource.get('nbframes','1'))-1)
        w=int(node.get('width',im.width));h=int(node.get('height',im.height))
        tile=node.tag=='Image' and node.get('resize','mosaic')=='mosaic'
        if not tile and (w,h)!=im.size:im=im.resize((w,h))
        alpha=im.getchannel('A')
        layers.append((node,int(node.get('x',0)),int(node.get('y',0)),w,h,alpha,tile,False,alpha.getextrema()[1]>1))
    return layers


def pick(layers,x,y):
    for node,ox,oy,w,h,alpha,tile,rect,painted in layers:
        px=x-ox;py=y-oy
        if not (0<=px<w and 0<=py<h):continue
        if tile:px%=alpha.width;py%=alpha.height
        opacity=alpha.getpixel((px,py))
        if rect or opacity>0:return node,opacity,painted
    return None,0,False


for scale in (1,2):
    a=ThemeAssets(SKIN/f'vlc-{scale}x');stats=Counter();worst=1
    for layout in a.tree.findall('.//Window[@id="main"]/Layout'):
        active=layout.get('id')
        layers=hit_layers(a,layout,active)
        for node in layout:
            if node.tag not in ('Button','Checkbox') or node.get('action')=='none':continue
            if node.get('tooltiptext')=='Skip original startup animation':continue
            key=node.get('up') or node.get('up1');resource=a.resources[key]
            im=a.frame(key,int(resource.get('nbframes','1'))-1);mask=im.getchannel('A')
            points=[(x,y) for y in range(im.height) for x in range(im.width) if mask.getpixel((x,y))>100]
            if not points:  # Clock click surface has an intentionally invisible alpha mask.
                points=[(im.width//2,im.height//2)]
            if '_closing' in active and (node.get('id','').startswith('clock_') or key=='m_logo_no_png'):
                for x,y in points:
                    hit,_,_=pick(layers,x+int(node.get('x',0)),y+int(node.get('y',0)))
                    assert hit is not None and hit.get('id','').startswith('decorative_endpoint_'),(active,key,'closed interior remains interactive')
                continue
            correct=0;painted=0
            for x,y in points:
                hit,opacity,paint=pick(layers,x+int(node.get('x',0)),y+int(node.get('y',0)))
                # Source buttons can overlap physically; count the visible shape.
                # Invisible slider hit rectangles and clock masks cannot hide failures.
                if hit is not node and paint and opacity>0 and source_button(node) and source_button(hit):continue
                painted+=1
                if hit is node:correct+=1
            assert painted>0,(active,key,'control is fully covered')
            coverage=correct/painted
            worst=min(worst,coverage)
            assert coverage==1,(scale,active,key,round(coverage,5))
            stats['controls']+=1;stats['pixels']+=painted
    print(f'PASS {scale}x: {stats["controls"]} control instances, {stats["pixels"]} source-visible pixels; minimum coverage {worst:.4%}')
