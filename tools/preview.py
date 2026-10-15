"""Render an asset comparison for review; this is not a VLC screenshot."""
from pathlib import Path
from lxml import etree as E
from PIL import Image, ImageDraw, ImageFont
from build import ROOT, SKIN, rgba

OUT=ROOT/'docs/preview.png'
base=SKIN/'vlc-2x'
tree=E.parse(str(base/'theme.xml'))
resources={e.get('id'):e for e in tree.getroot() if e.tag in ('Bitmap','Font')}


def bitmap(key,frame=0,count=None):
    e=resources[key];im=Image.open(base/e.get('file')).convert('RGBA')
    n=count or int(e.get('nbframes','1'));h=im.height//n
    return im.crop((0,frame*h,im.width,(frame+1)*h))


def render(lid):
    layout=tree.find(f'.//Layout[@id="{lid}"]')
    out=Image.new('RGBA',(int(layout.get('width')),int(layout.get('height'))))
    for e in layout:
        x=int(e.get('x',0));y=int(e.get('y',0));im=None
        if e.tag=='Image':
            im=bitmap(e.get('image'))
            if e.get('width'):
                size=(int(e.get('width')),int(e.get('height',im.height)))
                if e.get('resize')=='mosaic':
                    tile=Image.new('RGBA',size)
                    for a in range(0,size[0],im.width):
                        for b in range(0,size[1],im.height):tile.paste(im,(a,b))
                    im=tile
                else:im=im.resize(size)
        elif e.tag in ('Button','Checkbox'):
            key=e.get('up') or e.get('up1');n=int(resources[key].get('nbframes','1'))
            im=bitmap(key,n-1)
        elif e.tag=='Slider':
            bg=e.find('SliderBackground')
            if bg is not None:im=bitmap(bg.get('image'),0,int(bg.get('nbvert','1')))
            else:
                im=bitmap(e.get('up'));y+=60 if 'band' in e.get('value','') else 0
        elif e.tag=='Text':
            text=e.get('text').replace('$N','Need for Speed Underground').replace('$t','00:00')
            f=resources[e.get('font')];font=ImageFont.truetype(str(base/f.get('file')),int(f.get('size')))
            d=ImageDraw.Draw(out);d.text((x+int(e.get('width'))/2,y),text,font=font,fill=e.get('color'),anchor='mt')
        elif e.tag in ('Video','Playtree'):
            ImageDraw.Draw(out).rectangle((x,y,x+int(e.get('width')),y+int(e.get('height'))),fill='#000000')
        if im is not None:out.alpha_composite(im,(x,y))
    return out


canvas=Image.new('RGB',(1580,1390),'#171A20');d=ImageDraw.Draw(canvas)
font=ImageFont.truetype(str(base/'assets/FreeSans.ttf'),24)
d.text((36,24),'NEED FOR SPEED UNDERGROUND / VLC CONVERSION',font=font,fill='#D7E5F0')
d.text((36,63),'Asset-rendered review preview — not a runtime screenshot',font=font,fill='#8A9AAB')
reference=rgba('preview.png').resize((480,480),Image.Resampling.LANCZOS)
canvas.paste(reference,(32,135),reference)
d.text((36,108),'Original WMP preview',font=font,fill='#8A9AAB')
main=render('main_1');canvas.paste(main,(550,130),main)
d.text((550,108),'VLC / 2x assets',font=font,fill='#8A9AAB')
eq=render('equalizer_1');canvas.paste(eq,(36,820),eq)
info=render('info_menu');info.thumbnail((690,480));canvas.paste(info,(850,820),info)
d.text((36,1335),'Original menu art, button states and seven palettes retained. Visual and click review pending.',font=font,fill='#8A9AAB')
canvas.save(OUT)
print(OUT)
