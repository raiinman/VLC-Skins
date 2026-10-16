"""Small source-matched dark beveled HUD faces and restrained inset glyphs.

The original 29px transport artwork remains untouched. These additional controls
borrow its neutral top highlight, dark lower face and subdued pressed treatment.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path(__file__).resolve().parents[1] / 'vendor/FreeSans.ttf'
SAMPLE = 8


def face(size, state):
    center = (size-1)/2
    radius = (size-3)/2
    image = Image.new('RGBA', (size*SAMPLE, size*SAMPLE))
    pixels = image.load()
    for y in range(image.height):
        dy = (y+.5)/SAMPLE-.5-center
        for x in range(image.width):
            dx = (x+.5)/SAMPLE-.5-center
            distance = math.hypot(dx,dy)
            if distance > radius:
                continue
            vertical = dy/radius
            if distance > radius-1:
                shade = 5+22*max(0,-vertical)+7*max(0,-dx/radius)
                if state == 'hov': shade += 8
                elif state == 'do': shade = 5+12*max(0,vertical)
            else:
                gloss = max(0,1-(dx/(radius*.95))**2-((dy+radius*.48)/(radius*.52))**2)
                shade = (24-15*vertical+23*gloss)*(.68+.32*(1-(distance/radius)**2))
                if state == 'hov': shade = shade*1.18+4
                elif state == 'do': shade = shade*.59
            value = round(shade)
            pixels[x,y] = (value,value+2,value+4,255)
    image = image.resize((size,size), Image.Resampling.LANCZOS)
    alpha = image.getchannel('A')
    ImageDraw.Draw(alpha).rectangle((0,0,size-1,size-1),outline=0)
    image.putalpha(alpha)
    return image


def glyph_mask(kind, size):
    center = (size-1)/2
    mask = Image.new('L',(size*SAMPLE,size*SAMPLE))
    draw = ImageDraw.Draw(mask)
    def coordinate(value):
        return (value+.5)*SAMPLE-.5
    def box(values):
        return tuple(coordinate(v) for v in values)
    if kind == 'speaker':
        draw.polygon([tuple(coordinate(v) for v in point) for point in
                      [(5,9),(8,9),(11,7),(11,15),(8,13),(5,13)]],fill=255)
        draw.arc(box((9,8,15,14)),-50,50,fill=255,width=SAMPLE)
        draw.arc(box((9,6,17,16)),-50,50,fill=255,width=SAMPLE)
    elif kind == 'settings':
        points = []
        for tooth in range(8):
            for fraction,radius in ((-.5,3.15),(-.26,4.2),(.26,4.2),(.5,3.15)):
                angle = (tooth+fraction)*math.tau/8
                points.append((coordinate(center+math.cos(angle)*radius),
                               coordinate(center+math.sin(angle)*radius)))
        draw.polygon(points,fill=255)
        draw.ellipse(box((center-1.45,center-1.45,center+1.45,center+1.45)),fill=0)
    elif kind in ('cc_off','cc_on'):
        font = ImageFont.truetype(str(FONT),8*SAMPLE)
        bounds = font.getbbox('CC')
        text = Image.new('L',(bounds[2]-bounds[0],bounds[3]-bounds[1]))
        ImageDraw.Draw(text).text((-bounds[0],-bounds[1]),'CC',font=font,fill=255, stroke_width=3, stroke_fill=255)
        text = text.resize((9*SAMPLE,5*SAMPLE),Image.Resampling.LANCZOS)
        mask.paste(text,((size*SAMPLE-text.width)//2,(size*SAMPLE-text.height)//2))
    else:
        raise ValueError('Unknown glyph: '+kind)
    mask = mask.resize((size,size),Image.Resampling.LANCZOS)
    # Clip even alpha1 resampling tails away from the inner bevel. Visible ink
    # is smaller still, but every nonzero glyph pixel has this radial clearance.
    limit = (size-3)/2-3
    for y in range(size):
        for x in range(size):
            if math.hypot(x-center,y-center) > limit:
                mask.putpixel((x,y),0)
    return mask


def button_icon(kind, state, size):
    if state not in ('no','hov','do') or (kind == 'speaker' and size != 23) or (kind != 'speaker' and size != 19):
        raise ValueError('Unsupported HUD button state/size')
    image = face(size,state)
    colors = {'no':(210,218,224),'hov':(246,250,252),'do':(167,181,190)}
    cyan = {'no':(99,185,210),'hov':(146,221,238),'do':(77,160,182)}
    color = (cyan if kind == 'cc_on' else colors)[state]
    glyph = Image.new('RGBA', image.size, color+(255,))
    glyph.putalpha(glyph_mask(kind,size))
    image.alpha_composite(glyph)
    return image
