"""Recover the supplied WMZ and build native VLC Skins2 packages."""
import argparse
import copy
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path

from lxml import etree as E
from PIL import Image, ImageChops, ImageDraw, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / 'skins/need-for-speed-underground'
SOURCE = SKIN / 'original'
MAGENTA = (255, 0, 255)


def recover(path):
    raw = path.read_bytes()
    # This particular WMZ replaces only the first local ZIP signature.
    repaired = b'PK\x03\x04' + raw[4:] if raw[:4] == b'\x01\x00\x01\x00' else raw
    with zipfile.ZipFile(io.BytesIO(repaired)) as z:
        for entry in z.infolist():
            dest = (SOURCE / entry.filename).resolve()
            if not dest.is_relative_to(SOURCE.resolve()):
                raise ValueError('Unsafe archive member: ' + entry.filename)
        assert z.testzip() is None, 'Archive CRC failure'
        SOURCE.mkdir(parents=True, exist_ok=True)
        z.extractall(SOURCE)
        manifest = {'source': path.name, 'sha256': hashlib.sha256(raw).hexdigest(),
                    'repair': 'First four bytes 01000100 replaced with ZIP local signature 504b0304 in memory only.',
                    'members': [{'name': e.filename, 'size': e.file_size, 'crc32': f'{e.CRC:08x}'} for e in z.infolist()]}
    (SKIN / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')


def rgba(name):
    im = Image.open(SOURCE / name).convert('RGBA')
    # The WMZ mixes real alpha and a magenta transparency key.
    r, g, b = ImageChops.difference(im.convert('RGB'), Image.new('RGB', im.size, MAGENTA)).split()
    mask = ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda x: 255 if x else 0)
    im.putalpha(ImageChops.multiply(im.getchannel('A'), mask))
    return im


class Builder:
    def __init__(self, scale):
        self.scale = scale
        self.out = SKIN / f'vlc-{scale}x'
        if self.out.exists():
            assert self.out.resolve().is_relative_to(SKIN.resolve())
            shutil.rmtree(self.out)
        (self.out / 'assets').mkdir(parents=True, exist_ok=True)
        self.theme = E.Element('Theme', version='2.0', tooltipfont='defaultfont')
        E.SubElement(self.theme, 'ThemeInfo', name='Need for Speed Underground', author='The Skins Factory / VLC conversion: Dead Signal Interactive')
        self.ids = {}
        font = ROOT / 'vendor/FreeSans.ttf'
        shutil.copyfile(font, self.out / 'assets/FreeSans.ttf')
        E.SubElement(self.theme, 'Font', id='ui', file='assets/FreeSans.ttf', size=str(10 * scale))
        E.SubElement(self.theme, 'Font', id='small', file='assets/FreeSans.ttf', size=str(8 * scale))

    def n(self, v):
        return str(round(v * self.scale))

    def bitmap(self, name, im=None, frames=1, fps=0, loop=0, gridframes=1):
        key = name.replace('.', '_')
        if key in self.ids:
            return key
        if im is None:
            im = rgba(name)
        if self.scale != 1:
            # Scale each frame separately so filtering cannot bleed between states.
            count = max(frames, gridframes)
            h = im.height // count
            target = Image.new('RGBA', (im.width * self.scale, im.height * self.scale))
            for i in range(count):
                frame = im.crop((0, i*h, im.width, (i+1)*h))
                target.paste(frame.resize((im.width*self.scale, h*self.scale), Image.Resampling.LANCZOS), (0, i*h*self.scale))
            im = target
        filename = key + '.png'
        im.save(self.out / 'assets' / filename)
        attrs = dict(id=key, file='assets/' + filename, alphacolor='#FF00FF')
        if frames > 1:
            attrs.update(nbframes=str(frames), fps=str(fps), loop=str(loop))
        E.SubElement(self.theme, 'Bitmap', **attrs)
        self.ids[key] = im.size
        return key

    def image(self, parent, name, x=0, y=0, **attrs):
        return E.SubElement(parent, 'Image', image=self.bitmap(name), x=self.n(x), y=self.n(y), **attrs)

    def text(self, parent, text, x, y, width, color='#00AEEF', small=False):
        return E.SubElement(parent, 'Text', text=text, x=self.n(x), y=self.n(y), width=self.n(width), font='small' if small else 'ui', color=color, alignment='center')

    def button(self, parent, prefix, x, y, action, tip, **attrs):
        return E.SubElement(parent, 'Button', x=self.n(x), y=self.n(y),
                            up=self.bitmap(prefix+'_no.png'), over=self.bitmap(prefix+'_hov.png'),
                            down=self.bitmap(prefix+'_do.png'), action=action, tooltiptext=tip, **attrs)

    def check(self, parent, prefix, x, y, state, on, off, tip, prefix2=None, **attrs):
        other = prefix2 or prefix
        return E.SubElement(parent, 'Checkbox', x=self.n(x), y=self.n(y), state=state,
                            up1=self.bitmap(prefix+'_no.png'), over1=self.bitmap(prefix+'_hov.png'), down1=self.bitmap(prefix+'_do.png'),
                            up2=self.bitmap(other+('_no.png' if prefix2 else '_do.png')), over2=self.bitmap(other+'_hov.png'), down2=self.bitmap(other+'_do.png'),
                            action1=on, action2=off, tooltiptext1=tip, tooltiptext2=tip, **attrs)

    @staticmethod
    def main_id(color, state='open', remaining=False):
        return f'main_{color}' + ('' if state=='open' else '_'+state) + ('_remaining' if remaining else '')

    def palette_visible(self, color):
        ids=[self.main_id(color,state,remaining) for state in ('open','opening','closed','closing') for remaining in (False,True)]
        if color==1:ids.append('main_start')
        return ' or '.join(lid+'.isActive' for lid in ids)

    def window(self, name, x, y, visible=False):
        return E.SubElement(self.theme, 'Window', id=name, x=self.n(x), y=self.n(y), visible=str(visible).lower())

    def layout(self, window, name, width, height, resizable=False):
        attrs = dict(id=name, width=self.n(width), height=self.n(height))
        if resizable:
            attrs.update(minwidth=self.n(width), minheight=self.n(height), maxwidth='3000', maxheight='2000')
        return E.SubElement(window, 'Layout', **attrs)

    def frame(self, layout, color, w, h, top='f_top_right', bottom='f_bot_right', resizable=False):
        if color is None:
            for c in range(1,8):
                self.frame(layout,c,w,h,top,bottom,resizable)
            return
        # WMP's logical height included 72 transparent pixels below the frame.
        parts = [('f_top_s',177,0,w-341,61),('f_bot_s',177,h-60,w-341,60),
                 ('f_left_s',0,61,177,h-118),('f_right_s',w-164,61,164,h-118),
                 ('f_top_left',0,0,177,61),(top,w-164,0,164,61),
                 ('f_bot_left',0,h-57,177,57),(bottom,w-164,h-57,164,57)]
        for p,x,y,pw,ph in parts:
            attrs = {}
            if resizable:
                if p == 'f_top_s': attrs['rightbottom']='righttop'
                if p == 'f_bot_s': attrs.update(lefttop='leftbottom', rightbottom='rightbottom')
                if p == 'f_left_s': attrs['rightbottom']='leftbottom'
                if p == 'f_right_s': attrs.update(lefttop='righttop', rightbottom='rightbottom')
                if p in (top,): attrs['lefttop']='righttop'
                if p == 'f_bot_left': attrs['lefttop']='leftbottom'
                if p == bottom: attrs['lefttop']='rightbottom'
            im = self.image(layout, f'{p}_{color}.png', x,y, action='move', visible=self.palette_visible(color), **attrs)
            if p.endswith('_s'):
                im.set('width',self.n(max(1,pw)));im.set('height',self.n(max(1,ph)));im.set('resize','mosaic')

    def dial(self, layout, color, name, x, y, size, sprite_y, frame_h, frames, amin, amax, variable):
        # WMP's position maps are horizontal grayscale ramps, not polar maps.
        # Keep the full background hit rectangle and the source needle sprites.
        points = [(3,51),(135,51)] if variable=='volume' else [(6,67),(150,67)]
        thumb=self.bitmap('invisible_cursor',Image.new('RGBA',(1,1)))
        slider=E.SubElement(layout,'Slider',x=self.n(x),y=self.n(y+sprite_y),up=thumb,points=','.join(f'({self.n(a)},{self.n(b)})' for a,b in points),value=variable,tooltiptext='Volume: $V%' if variable=='volume' else 'Seek: $T / $D')
        # Register frames as a static grid; VLC chooses its frame from the value.
        if variable=='time':
            original=rgba(name+'.png');seq=Image.new('RGBA',original.size)
            for i in range(frames):seq.paste(original.crop((0,(frames-1-i)*frame_h,size,(frames-i)*frame_h)),(0,i*frame_h))
            key=self.bitmap('seek_forward',seq,gridframes=frames)
        else:key=self.bitmap(name+'.png',gridframes=frames)
        E.SubElement(slider,'SliderBackground',image=key,nbvert=str(frames))

    def main(self):
        win = self.window('main',60,60,True)
        for c in range(1,8):
            for state in ('open','opening','closed','closing'):
                for remaining in (False,True):
                    shut=state in ('closed','closing')
                    l = self.layout(win,self.main_id(c,state,remaining),300,298)
                    self.image(l,f'main_back_{c}.png',action='move')
                    if state in ('opening','closing'):
                        light=self.shutter_sequence(shut,light_only=True)
                        E.SubElement(l,'Button',id=f'decorative_light_{c}_{state}_{int(remaining)}',up=light,x=self.n(21),y=self.n(32),action='none')
                    elif shut:self.image(l,'shutter_light.png',21,32,action='move')
                    self.button(l,'m_min',44,37,'vlc.minimize()','Minimize')
                    self.button(l,'m_full',55,11,'video.show();vlc.fullscreen()','Fullscreen video')
                    self.button(l,'m_close',87,10,'vlc.quit()','Close VLC')
                    self.button(l,'m_open',64,52,'dialogs.fileSimple()','Open media')
                    for p,x,y,w in [('m_vis',37,86,'video'),('m_pl',27,126,'tracks'),('m_eq',32,168,'equalizer')]:
                        self.check(l,p,x,y,w+'.isVisible',w+'.show()',w+'.hide()','Show / hide '+w)
                    if not shut:
                        self.dial(l,c,'volume',81,65,138,0,52,29,0,0,'volume')
                        self.dial(l,c,'seek',71,56,156,108,68,33,0,0,'time')
                        self.image(l,'vol_seek_mat.png',108,102)
                        self.text(l,'$N',62,117,177,small=True)
                        E.SubElement(l,'Button',x=self.n(58),y=self.n(134),up=self.bitmap('m_logo_no.png'),over=self.bitmap('m_logo_hov.png'),down=self.bitmap('m_logo_no.png'),action='info.show()',tooltiptext='Need for Speed information')
                        self.text(l,'$l' if remaining else '$t',129,168,60,small=True)
                        if remaining:self.image(l,'time_dash.png',120,168)
                        hit=self.bitmap('clock_hit',Image.new('RGBA',(69,16),(0,0,0,1)))
                        E.SubElement(l,'Button',id=f'clock_{c}_{state}_{int(remaining)}',x=self.n(120),y=self.n(167),up=hit,action=f'main.setLayout({self.main_id(c,"open",not remaining)})',tooltiptext='Show elapsed time' if remaining else 'Show remaining time')
                    self.button(l,'m_next',240,100,'playlist.next()','Next track')
                    self.button(l,'m_stop',244,142,'vlc.stop()','Stop')
                    self.check(l,'m_play',234,182,'vlc.isPlaying','vlc.play()','vlc.pause()','Play / pause',prefix2='m_pause')
                    self.button(l,'m_prev',208,217,'playlist.previous()','Previous track')
                    target=self.main_id(c%7+1,'closed' if shut else 'open',remaining)
                    self.button(l,'m_color',194,269,f'main.setLayout({target})','Cycle seven original color schemes')
                    self.check(l,'m_info',215,257,'info.isVisible','info.show()','info.hide()','Information / About')
                    action=f'main.setLayout({self.main_id(c,"opening" if shut else "closing",remaining)})'
                    if state in ('opening','closing'):
                        # A transparent lead-in prevents repeated clicks during travel.
                        self.image(l,'m_shutter_do.png' if shut else 'm_shutter_no.png',237,242)
                        prefix='shutter_locked_closed' if shut else 'shutter_locked'
                        for suffix,source in [('no','no'),('hov','hov'),('do','do')]:
                            if shut and suffix=='no':source='do'
                            im=rgba('m_shutter_'+source+'.png')
                            if suffix=='no':
                                seq=Image.new('RGBA',(im.width,im.height*11))
                                seq.paste(im,(0,im.height*10))
                                self.bitmap(prefix+'_'+suffix+'.png',seq,11,20,1)
                            else:
                                # VLC restarts animation on hover/press. Those masks
                                # must remain solid so a quick release still clicks.
                                self.bitmap(prefix+'_'+suffix+'.png',im)
                        self.button(l,prefix,237,242,action,'Open shutter' if shut else 'Close shutter')
                        key=self.shutter_sequence(shut)
                        E.SubElement(l,'Button',id=f'decorative_shutter_{c}_{state}_{int(remaining)}',up=key,x=self.n(54),y=self.n(52),action='none',help='Decorative shutter animation')
                    else:
                        button=self.button(l,'m_shutter',237,242,action,'Open shutter' if shut else 'Close shutter')
                        if shut:button.set('up',self.bitmap('m_shutter_do.png'))
                        if shut:
                            self.image(l,'shutter_f01.png',54,52)
                    # WMP decorations were pass-through. Skins2 lacks that flag;
                    # keep the functional outer controls above decorative hit masks.
                    for node in list(l):
                        key=node.get('up') or node.get('up1') or ''
                        if node.tag in ('Button','Checkbox') and (key.startswith('m_') and key!='m_logo_no_png' or key.startswith('shutter_locked')):
                            l.append(node)
        # VLC chooses the last layout declared as its initial layout.
        startup=copy.deepcopy(win[0]);startup.set('id','main_start')
        for e in startup.iter():
            if e is not startup and e.get('id'):e.set('id',e.get('id')+'_startup')
        key=self.startup_sequence()
        E.SubElement(startup,'Button',up=key,x=self.n(53),y=self.n(52),action='main.setLayout(main_1)',tooltiptext='Skip original startup animation')
        light=E.Element('Button',id='decorative_intro_light',up='intro_light_sequence',x=self.n(21),y=self.n(32),action='none')
        startup.insert(1,light)
        win.append(startup)

    def shutter_sequence(self,closing,light_only=False):
        name=('shutter_close' if closing else 'shutter_open')+('_light' if light_only else '')
        if name in self.ids:return name
        width,height=(258,231) if light_only else (193,193)
        seq=Image.new('RGBA',(width,height*11));light=rgba('shutter_light.png')
        indexes=range(11,0,-1) if closing else range(2,13)
        for i,frame in enumerate(indexes):
            if light_only:
                im=light.copy();alpha=min(1,i/10) if closing else max(0,1-i/10)
                im.putalpha(im.getchannel('A').point(lambda a:round(a*alpha)))
            else:im=rgba(f'shutter_f0{frame}.png')
            seq.paste(im,(0,i*height))
        return self.bitmap(name,seq,11,20,1)

    def startup_sequence(self):
        with Image.open(SOURCE/'intro_anim.gif') as gif:
            frames=[f.convert('RGBA').copy() for f in ImageSequence.Iterator(gif)]
            loop=gif.info.get('loop')==0
        # Source timers: 1.5 s static; GIF; light fades at 6.5 s; intro fades at 7.5 s.
        seq=Image.new('RGBA',(194,194*81));lightseq=Image.new('RGBA',(258,231*81))
        light=rgba('shutter_light.png');static=rgba('intro_static.png')
        for i in range(80):
            t=i/10;im=light.copy();alpha=max(0,min(1,(7-t)/.5))
            im.putalpha(im.getchannel('A').point(lambda a:round(a*alpha)))
            f=static.copy() if i<15 else frames[(i-15)%len(frames) if loop else min(i-15,len(frames)-1)].copy()
            alpha=max(0,min(1,(8-t)/.5));f.putalpha(f.getchannel('A').point(lambda a:round(a*alpha)))
            lightseq.paste(im,(0,i*231));seq.paste(f,(0,i*194))
        self.bitmap('intro_light_sequence',lightseq,81,10,1)
        return self.bitmap('intro_sequence',seq,81,10,1)

    def panels(self):
        # Remove the obsolete SRS/WOW rails using the source carbon texture.
        eq=rgba('eq_back.png');tile=eq.crop((2,128,18,136))
        for x in range(150,282,tile.width):
            for y in range(4,103,tile.height):eq.paste(tile,(x,y))
        eq.alpha_composite(rgba('eq_back.png').crop((200,11,270,28)),(198,30))
        self.bitmap('eq_vlc_back',eq)
        mapping=Image.open(SOURCE/'eq_set_map.png').convert('RGB')
        diff=ImageChops.difference(mapping,Image.new('RGB',mapping.size,(0,51,255)))
        r,g,b=diff.split();mask=ImageChops.lighter(ImageChops.lighter(r,g),b).point(lambda p:255 if p==0 else 0)
        box=mask.getbbox()
        for state in ('no','hov','do'):
            im=rgba('eq_set_'+state+'.png').crop(box);im.putalpha(mask.crop(box))
            self.bitmap('eq_power_'+state+'.png',im)
        for kind,w,h,x,y,top in [('tracks',420,320,380,60,'pl_top_right'),('equalizer',353,210,60,380,'eq_top_right'),('video',708,440,380,410,'f_top_right')]:
            win=self.window(kind,x,y)
            for c in (1,):
                resize=kind!='equalizer'
                l=self.layout(win,f'{kind}_{c}',w,h,resize)
                self.frame(l,None,w,h,top=top,resizable=resize)
                self.button(l,'m_close',w-68,6,kind+'.hide()','Close '+kind,**({'lefttop':'righttop'} if resize else {}))
                if kind in ('tracks','video'):
                    self.bitmap('screen_black',Image.new('RGBA',(1,1),'black'))
                    self.image(l,'screen_black',34,37,width=self.n(w-68),height=self.n(h-67),resize='mosaic',rightbottom='rightbottom')
                if kind=='tracks':
                    self.check(l,'pl_shuffle',w-110,6,'playlist.isRandom','playlist.setRandom(true)','playlist.setRandom(false)','Shuffle',lefttop='righttop')
                    self.check(l,'pl_repeat',w-89,6,'playlist.isLoop','playlist.setLoop(true)','playlist.setLoop(false)','Repeat playlist',lefttop='righttop')
                    tree=E.SubElement(l,'Playtree',id='track_list',x=self.n(34),y=self.n(37),width=self.n(w-86),height=self.n(h-67),font='ui',fgcolor='#9FA2B0',playcolor='#FFFFFF',bgcolor1='#000000',bgcolor2='#000000',selcolor='#A01A1A',flat='true',rightbottom='rightbottom')
                    E.SubElement(tree,'Slider',x=self.n(w-44),y=self.n(43),up=self.bitmap('eq_thumb2.png'),down=self.bitmap('eq_thumb2_do.png'),points=f'(0,0),(0,{self.n(h-90)})',lefttop='righttop',rightbottom='rightbottom')
                    self.button(l,'m_open',32,h-31,'playlist.add()','Add media',lefttop='leftbottom')
                elif kind=='video':
                    E.SubElement(l,'Video',x=self.n(34),y=self.n(37),width=self.n(w-68),height=self.n(h-67),rightbottom='rightbottom')
                    self.button(l,'vid_zoom',w-89,6,'vlc.fullscreen()','Fullscreen',lefttop='righttop')
                else:
                    self.image(l,'eq_vlc_back',33,35)
                    for i,(dx,hz) in enumerate(zip([14,27,39,52,64,77,90,102,115,128],['60 Hz','170 Hz','310 Hz','600 Hz','1 kHz','3 kHz','6 kHz','12 kHz','14 kHz','16 kHz'])):
                        E.SubElement(l,'Slider',x=self.n(33+dx+8),y=self.n(35+25),up=self.bitmap('eq_thumb.png'),down=self.bitmap('eq_thumb_do.png'),points=f'(0,{self.n(60)}),(0,0)',thickness=self.n(7),value=f'equalizer.band({i})',tooltiptext=f'{hz}: -20 to +20 dB')
                    self.check(l,'eq_power',233,142,'equalizer.isEnabled','equalizer.enable()','equalizer.disable()','Enable / disable equalizer')
                    self.text(l,'VLC EQUALIZER',67,144,110,color='#F8F8F8',small=True)
                    self.text(l,'PREAMP',191,48,113,color='#D1D1D1',small=True)
                    E.SubElement(l,'Slider',x=self.n(232),y=self.n(71),up=self.bitmap('eq_thumb2.png'),down=self.bitmap('eq_thumb2_do.png'),points=f'(0,0),({self.n(60)},0)',value='equalizer.preamp',tooltiptext='Equalizer preamplification')
                    self.text(l,'Dead Signal Interactive',60,174,235,color='#9FA2B0',small=True)
                if resize:
                    self.image(l,'f_resize.png',w-36,h-24,action='resizeSE',lefttop='rightbottom')
            win.append(win[0])

    def information(self):
        win=self.window('info',820,60)
        pages=['menu','about'] + [p.stem for p in sorted(SOURCE.glob('c_sub_*.jpg'))]
        for page in pages:
            l=self.layout(win,'info_'+page,413,282)
            self.frame(l,None,413,282,bottom='info_bot_right')
            self.button(l,'m_close',345,6,'info.hide()','Close information')
            self.image(l,'c_back.png',14,34)
            if page=='about':
                texture=rgba('eq_back.png').crop((200,90,220,106))
                key=self.bitmap('about_carbon',texture)
                E.SubElement(l,'Image',image=key,x=self.n(37),y=self.n(35),width=self.n(338),height=self.n(219),resize='mosaic')
                # Credit stays in the information panel, away from media.
                for y,t in [(91,'VLC conversion'),(112,'Dead Signal Interactive'),(143,'Original skin: The Skins Factory'),(164,'Need for Speed Underground'),(184,'Copyright 2003 Electronic Arts Inc.')]:
                    self.text(l,t,64,y,290,color='#00AEEF' if y<140 else '#D1D1D1',small=True)
                self.text(l,'Replay intro',222,229,90,color='#D1D1D1',small=True)
                self.button(l,'m_shutter',323,226,'main.setLayout(main_1);main.setLayout(main_start);main.show();info.hide()','Replay original startup animation')
            elif page=='menu':
                self.image(l,'c_back.jpg',37,35)
                mapping=Image.open(SOURCE/'c_menu_map.png').convert('RGB')
                for i,(color,target) in enumerate([((0,0,255),'c_sub_1_1'),((0,51,255),'c_sub_2_1'),((0,102,255),'c_sub_3_1'),((0,153,255),'c_sub_4_1')]):
                    r,g,b=ImageChops.difference(mapping,Image.new('RGB',mapping.size,color)).split()
                    mask=ImageChops.lighter(ImageChops.lighter(r,g),b).point(lambda x:255 if x==0 else 0)
                    box=mask.getbbox()
                    ids=[]
                    for state in ('no','hov','do'):
                        im=rgba('c_menu_'+state+'.jpg').crop(box)
                        im.putalpha(mask.crop(box))
                        ids.append(self.bitmap(f'menu_{i}_{state}',im))
                    E.SubElement(l,'Button',x=self.n(171+box[0]),y=self.n(103+box[1]),up=ids[0],over=ids[1],down=ids[2],action=f'info.setLayout(info_{target})',tooltiptext=['About the game','Story','Screenshots','Web destinations'][i])
            else:
                self.image(l,page+'.jpg',37,35)
            if page!='menu':
                self.button(l,'c_menu_return',47,226,'info.setLayout(info_menu)','Return to original menu')
                if page.startswith(('c_sub_2_','c_sub_3_')):
                    group=page[:8]; members=[p for p in pages if p.startswith(group)];i=members.index(page)
                    if i: self.button(l,'c_nav_prev',323,226,f'info.setLayout(info_{members[i-1]})','Previous page')
                    else:self.image(l,'c_nav_prev_dis.png',323,226)
                    if i+1<len(members):self.button(l,'c_nav_next',348,226,f'info.setLayout(info_{members[i+1]})','Next page')
                    else:self.image(l,'c_nav_next_dis.png',348,226)
            if page=='menu':
                self.text(l,'Dead Signal Interactive',93,257,225,color='#B7BBC8',small=True)
                # The original information button artwork opens conversion credits.
                self.button(l,'m_info',310,248,'info.setLayout(info_about)','About this VLC conversion')
        win.append(win[0])

    def save(self):
        # VLC 3's generateId() uses snprintf(..., 4, ...), truncating at 999.
        # Explicit IDs prevent its control owner map from deleting live controls.
        for i,node in enumerate(self.theme.iter()):
            if node.tag in ('Image','Button','Checkbox','Slider','Text','Video') and not node.get('id'):
                node.set('id',f'control_{i}')
        self.band_animations()
        self.pack_atlases()
        # XML requires resource declarations before windows; resources were discovered lazily.
        children=list(self.theme)
        for node in self.theme.iter():
            if node.get('lefttop') and not node.get('rightbottom'):
                node.set('rightbottom',node.get('lefttop'))
        for child in children:self.theme.remove(child)
        for tagset in [('ThemeInfo',),('Bitmap','Font'),('Window',)]:
            for child in children:
                if child.tag in tagset:self.theme.append(child)
        data=E.tostring(self.theme,pretty_print=True,xml_declaration=True,encoding='UTF-8',doctype='<!DOCTYPE Theme PUBLIC "-//VideoLAN//DTD VLC Skins V2.0//EN" "skin.dtd">')
        (self.out/'theme.xml').write_bytes(data)
        shutil.copyfile(ROOT/'vendor/skin.dtd',self.out/'skin.dtd')
        validate(self.out)
        dist=ROOT/'dist';dist.mkdir(exist_ok=True)
        path=dist/f'Need-for-Speed-Underground-{self.scale}x.vlt'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            files={'theme.xml','skin.dtd'}|{n.get('file') for n in self.theme if n.get('file')}
            for filename in sorted(files):z.write(self.out/filename,filename)
        return path

    def band_animations(self):
        # Win32 combines a region for every opaque run. Long sprite strips
        # make that work quadratic; small horizontal bands keep pixels intact.
        manifest={}
        for node in list(self.theme.findall('Bitmap')):
            frames=int(node.get('nbframes','1'))
            if frames<=1:continue
            im=Image.open(self.out/node.get('file')).convert('RGBA')
            if im.height<=4096:continue
            height=im.height//frames;bands=[]
            for index in range(16):
                y0=height*index//16;y1=height*(index+1)//16
                strip=Image.new('RGBA',(im.width,(y1-y0)*frames))
                for frame in range(frames):
                    strip.paste(im.crop((0,frame*height+y0,im.width,frame*height+y1)),(0,frame*(y1-y0)))
                key=node.get('id')+f'_band_{index}'
                filename=f'assets/{key}.png';strip.save(self.out/filename)
                resource=copy.deepcopy(node);resource.set('id',key);resource.set('file',filename)
                self.theme.insert(self.theme.index(node),resource)
                bands.append(dict(id=key,y=y0,height=y1-y0))
            manifest[node.get('id')]=dict(bitmap=dict(node.attrib),bands=bands)
            for layout in self.theme.findall('.//Layout'):
                for control in list(layout):
                    if control.get('up')!=node.get('id'):continue
                    assert control.tag=='Button' and not control.get('over') and not control.get('down')
                    for index,band in enumerate(bands):
                        part=copy.deepcopy(control);part.set('id',control.get('id')+f'_band_{index}')
                        part.set('up',band['id']);part.set('y',str(int(control.get('y','0'))+band['y']))
                        layout.insert(layout.index(control),part)
                    layout.remove(control)
            self.theme.remove(node)
        (self.out/'animation-bands.json').write_text(json.dumps(manifest,indent=2)+'\n')

    def pack_atlases(self):
        """Load static art in a few decoder calls without changing its pixels."""
        entries=[]
        for node in list(self.theme.findall('Bitmap')):
            im=Image.open(self.out/node.get('file')).convert('RGBA')
            if im.width<=2048 and im.height<=4096:entries.append((node,im))
        entries.sort(key=lambda item:item[1].height,reverse=True)
        pages=[];page=[];x=y=rowh=usedw=0
        for node,im in entries:
            if x+im.width>2048:x=0;y+=rowh;rowh=0
            if y+im.height>4096:
                pages.append((page,usedw,y+rowh));page=[];x=y=rowh=usedw=0
            page.append((node,im,x,y));x+=im.width;rowh=max(rowh,im.height);usedw=max(usedw,x)
        if page:pages.append((page,usedw,y+rowh))
        for i,(page,w,h) in enumerate(pages):
            atlas=Image.new('RGBA',(w,h));container=E.Element('Bitmap',id=f'atlas_{i}',file=f'assets/atlas_{i}.png',alphacolor='#FF00FF')
            for node,im,x,y in page:
                atlas.paste(im,(x,y))
                attrs={k:v for k,v in node.attrib.items() if k not in ('file','alphacolor')}
                attrs.update(x=str(x),y=str(y),width=str(im.width),height=str(im.height))
                E.SubElement(container,'SubBitmap',**attrs);self.theme.remove(node)
            atlas.save(self.out/container.get('file'));self.theme.append(container)


def validate(out):
    tree=E.parse(str(out/'theme.xml'))
    dtd=E.DTD(str(ROOT/'vendor/skin.dtd'))
    assert dtd.validate(tree), str(dtd.error_log)
    ids=[n.get('id') for n in tree.iter() if n.get('id')]
    assert len(ids)==len(set(ids)), 'Duplicate ids'
    known=set(ids)|{'defaultfont'}
    for node in tree.iter():
        for attr in ('image','sequence','up','down','over','up1','up2','down1','down2','over1','over2','font'):
            v=node.get(attr)
            if v:assert v in known,(node.tag,attr,v)
        if node.get('file'):assert (out/node.get('file')).is_file(),node.get('file')
        if node.tag=='Button' and not node.get('id','').startswith('decorative_'):
            assert node.get('action') not in ('none',None)
    print(f'PASS {out.name}: DTD, unique IDs, resources and button actions')


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--check',action='store_true');args=p.parse_args()
    if args.source:recover(args.source)
    if args.check:
        for scale in (1,2):validate(SKIN/f'vlc-{scale}x')
        return
    for scale in (1,2):
        b=Builder(scale);b.main();b.panels();b.information();print(b.save())


if __name__=='__main__':main()
