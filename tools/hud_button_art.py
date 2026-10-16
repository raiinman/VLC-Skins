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
            root, tip = (4.2,5.6) if size == 25 else (3.15,4.2)
            for fraction,radius in ((-.5,root),(-.26,tip),(.26,tip),(.5,root)):
                angle = (tooth+fraction)*math.tau/8
                points.append((coordinate(center+math.cos(angle)*radius),
                               coordinate(center+math.sin(angle)*radius)))
        draw.polygon(points,fill=255)
        hole = 1.9 if size == 25 else 1.45
        draw.ellipse(box((center-hole,center-hole,center+hole,center+hole)),fill=0)
    elif kind == 'clear':
        draw.line(box((center-4,center-4,center+4,center-4)),fill=255,width=SAMPLE)
        draw.rectangle(box((center-1.5,center-6,center+1.5,center-4)),outline=255,width=SAMPLE)
        draw.line([tuple(coordinate(v) for v in p) for p in
                   [(center-3.5,center-2.5),(center-3,center+5),
                    (center+3,center+5),(center+3.5,center-2.5)]],fill=255,width=SAMPLE)
        for x in (center-1,center+1):
            draw.line(box((x,center-1.5,x,center+3)),fill=255,width=SAMPLE)
    elif kind in ('cc_off','cc_on'):
        font = ImageFont.truetype(str(FONT),(10 if size == 25 else 8)*SAMPLE)
        bounds = font.getbbox('CC')
        text = Image.new('L',(bounds[2]-bounds[0],bounds[3]-bounds[1]))
        ImageDraw.Draw(text).text((-bounds[0],-bounds[1]),'CC',font=font,fill=255, stroke_width=3, stroke_fill=255)
        text_size = (12,7) if size == 25 else (9,5)
        text = text.resize(tuple(v*SAMPLE for v in text_size),Image.Resampling.LANCZOS)
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
    allowed_sizes = (23,) if kind == 'speaker' else (29,) if kind == 'clear' else (19,25)
    if state not in ('no','hov','do') or size not in allowed_sizes:
        raise ValueError('Unsupported HUD button state/size')
    image = face(size,state)
    colors = {'no':(210,218,224),'hov':(246,250,252),'do':(167,181,190)}
    cyan = {'no':(99,185,210),'hov':(146,221,238),'do':(77,160,182)}
    color = (cyan if kind == 'cc_on' else colors)[state]
    glyph = Image.new('RGBA', image.size, color+(255,))
    glyph.putalpha(glyph_mask(kind,size))
    image.alpha_composite(glyph)
    return image


def snapping_button(state, enabled, native_text=False):
    """Readable footer pill with explicit SNAP and ON/OFF labels."""
    if state not in ('no','hov','do'):
        raise ValueError('Unsupported snapping button state')
    if native_text:
        # Crisp metal face, with lettering rendered by VLC at display size.
        width, height = 82*SAMPLE, 29*SAMPLE
        image = Image.new('RGBA',(width,height))
        mask = Image.new('L',image.size)
        ImageDraw.Draw(mask).rounded_rectangle((SAMPLE,2*SAMPLE,81*SAMPLE,27*SAMPLE),
                                              radius=12*SAMPLE,fill=255)
        draw = ImageDraw.Draw(image)
        for y in range(height):
            fraction=y/height
            shade=round(48-30*fraction+15*max(0,1-abs(fraction-.24)*9))
            if state=='hov':shade+=9
            elif state=='do':shade=round(shade*.56)
            draw.line((0,y,width,y),fill=(shade,shade+2,shade+4,255))
        image.putalpha(mask)
        draw=ImageDraw.Draw(image)
        draw.rounded_rectangle((SAMPLE,2*SAMPLE,81*SAMPLE,27*SAMPLE),radius=12*SAMPLE,
                               outline=(4,6,8,255),width=SAMPLE)
        draw.arc((2*SAMPLE,3*SAMPLE,80*SAMPLE,26*SAMPLE),185,355,
                 fill=(92,101,108,255) if state!='do' else (30,36,40,255),width=SAMPLE)
        draw.rounded_rectangle((48*SAMPLE,6*SAMPLE,75*SAMPLE,23*SAMPLE),radius=5*SAMPLE,
                               fill=(20,47,56,255) if enabled else (20,23,26,255),
                               outline=(68,109,121,255) if enabled else (56,62,67,255),width=SAMPLE)
        return image.resize((82,29),Image.Resampling.LANCZOS)
    image = Image.new('RGBA',(82*SAMPLE,29*SAMPLE))
    draw = ImageDraw.Draw(image)
    def rect(values):
        return tuple(round(v*SAMPLE) for v in values)
    fill = {'no':(26,29,32),'hov':(38,44,49),'do':(15,18,21)}[state]
    edge = {'no':(69,75,80),'hov':(102,119,128),'do':(43,49,54)}[state]
    draw.rounded_rectangle(rect((1.5,2,80.5,27)),radius=12*SAMPLE,
                           fill=fill,outline=(5,7,9),width=2*SAMPLE)
    draw.rounded_rectangle(rect((3,3.5,79,25.5)),radius=10*SAMPLE,
                           outline=edge,width=SAMPLE)
    font = ImageFont.truetype(str(FONT),12*SAMPLE)
    status_font = ImageFont.truetype(str(FONT),9*SAMPLE)
    color = (231,237,240) if state != 'do' else (176,188,197)
    draw.text((10*SAMPLE,14.5*SAMPLE),'SNAP',font=font,anchor='lm',fill=color)
    status_fill = (26,61,72) if enabled else (37,40,43)
    status_ink = (133,225,246) if enabled else (184,190,195)
    draw.rounded_rectangle(rect((48,7,74,22)),radius=5*SAMPLE,fill=status_fill)
    draw.text((61*SAMPLE,14.5*SAMPLE),'ON' if enabled else 'OFF',
              font=status_font,anchor='mm',fill=status_ink)
    return image.resize((82,29),Image.Resampling.LANCZOS)
