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
    mask = ImageChops.difference(im.convert('RGB'), Image.new('RGB', im.size, MAGENTA)).convert('L').point(lambda x: 255 if x else 0)
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

    def bitmap(self, name, im=None, frames=1, fps=0, loop=0):
        key = name.replace('.', '_')
        if key in self.ids:
            return key
        if im is None:
            im = rgba(name)
        if self.scale != 1:
            # Scale each frame separately so filtering cannot bleed between states.
            h = im.height // frames
            target = Image.new('RGBA', (im.width * self.scale, im.height * self.scale))
            for i in range(frames):
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

    def check(self, parent, prefix, x, y, state, on, off, tip, prefix2=None):
        other = prefix2 or prefix
        return E.SubElement(parent, 'Checkbox', x=self.n(x), y=self.n(y), state=state,
                            up1=self.bitmap(prefix+'_no.png'), over1=self.bitmap(prefix+'_hov.png'), down1=self.bitmap(prefix+'_do.png'),
                            up2=self.bitmap(other+('_no.png' if prefix2 else '_do.png')), over2=self.bitmap(other+'_hov.png'), down2=self.bitmap(other+'_do.png'),
                            action1=on, action2=off, tooltiptext1=tip, tooltiptext2=tip)

    def window(self, name, x, y, visible=False):
        return E.SubElement(self.theme, 'Window', id=name, x=self.n(x), y=self.n(y), visible=str(visible).lower())

    def layout(self, window, name, width, height, resizable=False):
        attrs = dict(id=name, width=self.n(width), height=self.n(height))
        if resizable:
            attrs.update(minwidth=self.n(width), minheight=self.n(height), maxwidth='3000', maxheight='2000')
        return E.SubElement(window, 'Layout', **attrs)

    def frame(self, layout, color, w, h, top='f_top_right', bottom='f_bot_right', resizable=False):
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
            im = self.image(layout, f'{p}_{color}.png', x,y, action='move', **attrs)
            if p.endswith('_s'):
                im.set('width',self.n(max(1,pw)));im.set('height',self.n(max(1,ph)));im.set('resize','mosaic')

    def dial(self, layout, color, name, x, y, size, sprite_y, frame_h, frames, amin, amax, variable):
        # VLC radial sliders cannot cross angle zero. A curved Slider with the
        # original sprite backgrounds preserves both needles and full travel.
        points = [(4,48),(9,27),(24,9),(46,0),(69,0),(92,0),(114,9),(129,27),(134,48)] if variable=='volume' else [(4,1),(9,29),(25,53),(50,67),(78,68),(106,67),(131,53),(147,29),(152,1)]
        thumb=self.bitmap('invisible_cursor',Image.new('RGBA',(1,1)))
        slider=E.SubElement(layout,'Slider',x=self.n(x),y=self.n(y+sprite_y),up=thumb,points=','.join(f'({self.n(a)},{self.n(b)})' for a,b in points),value=variable,tooltiptext='Volume: $V%' if variable=='volume' else 'Seek: $T / $D')
        # Register frames as a static grid; VLC chooses its frame from the value.
        if variable=='time':
            original=rgba(name+'.png');seq=Image.new('RGBA',original.size)
            for i in range(frames):seq.paste(original.crop((0,(frames-1-i)*frame_h,size,(frames-i)*frame_h)),(0,i*frame_h))
            key=self.bitmap('seek_forward',seq)
        else:key=self.bitmap(name+'.png')
        E.SubElement(slider,'SliderBackground',image=key,nbvert=str(frames))

    def main(self):
        win = self.window('main',60,60,True)
        for c in range(1,8):
            for shut in (False,True):
                lid = f'main_{c}' + ('_closed' if shut else '')
                l = self.layout(win,lid,300,298)
                self.image(l,f'main_back_{c}.png',action='move')
                self.button(l,'m_min',44,37,'vlc.minimize()','Minimize')
                self.button(l,'m_full',55,11,'video.show();vlc.fullscreen()','Fullscreen video')
                self.button(l,'m_close',87,10,'vlc.quit()','Close VLC')
                self.button(l,'m_open',64,52,'dialogs.fileSimple()','Open media')
                for p,x,y,w in [('m_vis',37,86,'video'),('m_pl',27,126,'tracks'),('m_eq',32,168,'equalizer')]:
                    self.check(l,p,x,y,w+'.isVisible',w+'.show()',w+'.hide()','Show / hide '+w)
                self.dial(l,c,'volume',81,65,138,0,52,29,110,250,'volume')
                self.dial(l,c,'seek',71,56,156,108,68,33,290,430,'time')
                self.image(l,'vol_seek_mat.png',108,102)
                self.text(l,'$N',62,117,177,small=True)
                # Preserve the logo artwork; open the retained information menu.
                E.SubElement(l,'Button',x=self.n(58),y=self.n(134),up=self.bitmap('m_logo_no.png'),over=self.bitmap('m_logo_hov.png'),down=self.bitmap('m_logo_no.png'),action='info.show()',tooltiptext='Need for Speed information')
                self.text(l,'$t',120,168,68,small=True)
                self.button(l,'m_next',240,100,'playlist.next()','Next track')
                self.button(l,'m_stop',244,142,'vlc.stop()','Stop')
                self.check(l,'m_play',234,182,'vlc.isPlaying','vlc.play()','vlc.pause()','Play / pause',prefix2='m_pause')
                self.button(l,'m_prev',208,217,'playlist.previous()','Previous track')
                nxt = c%7+1
                actions = ';'.join([f'main.setLayout(main_{nxt})']+[f'{w}.setLayout({w}_{nxt})' for w in ('tracks','equalizer','video')])
                self.button(l,'m_color',194,269,actions,'Cycle seven original color schemes')
                self.check(l,'m_info',215,257,'info.isVisible','info.show()','info.hide()','Information / About')
                self.button(l,'m_shutter',237,242,f'main.setLayout(main_{c}'+(')' if shut else '_closed)'), 'Open shutter' if shut else 'Close shutter')
                files = [f'shutter_f0{i}.png' for i in range(1,13)]
                if shut: files.reverse()
                seq=Image.new('RGBA',(193,193*12))
                for i,n in enumerate(files): seq.paste(rgba(n),(0,i*193))
                key=self.bitmap('shutter_close' if shut else 'shutter_open',seq,12,30,1)
                E.SubElement(l,'Button',up=key,x=self.n(54),y=self.n(52),action=f'main.setLayout(main_{c}'+(')' if shut else '_closed)'),tooltiptext='Open shutter' if shut else 'Close shutter')
        # VLC chooses the last layout declared as its initial layout.
        startup=copy.deepcopy(win[0]);startup.set('id','main_start')
        with Image.open(SOURCE/'intro_anim.gif') as gif:
            frames=[f.convert('RGBA').copy() for f in ImageSequence.Iterator(gif)]
            duration=sum(f.info.get('duration',100) for f in ImageSequence.Iterator(gif))
        seq=Image.new('RGBA',(194,194*(len(frames)+1)))
        for i,frame in enumerate(frames):seq.paste(frame,(0,194*i))
        key=self.bitmap('intro_sequence',seq,len(frames)+1,round(len(frames)*1000/duration),1)
        E.SubElement(startup,'Button',up=key,x=self.n(53),y=self.n(52),action='main.setLayout(main_1)',tooltiptext='Skip original startup animation')
        win.append(startup)

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
            for c in range(1,8):
                resize=kind!='equalizer'
                l=self.layout(win,f'{kind}_{c}',w,h,resize)
                self.frame(l,c,w,h,top=top,resizable=resize)
                self.button(l,'m_close',w-68,6,kind+'.hide()','Close '+kind,**({'lefttop':'righttop'} if resize else {}))
                if kind=='tracks':
                    self.check(l,'pl_shuffle',w-110,6,'playlist.isRandom','playlist.setRandom(true)','playlist.setRandom(false)','Shuffle')
                    self.check(l,'pl_repeat',w-89,6,'playlist.isLoop','playlist.setLoop(true)','playlist.setLoop(false)','Repeat playlist')
                    tree=E.SubElement(l,'Playtree',id=f'tree_{c}',x=self.n(34),y=self.n(37),width=self.n(w-68),height=self.n(h-67),font='ui',fgcolor='#9FA2B0',playcolor='#FFFFFF',bgcolor1='#000000',bgcolor2='#000000',selcolor='#A01A1A',flat='true',rightbottom='rightbottom')
                    E.SubElement(tree,'Slider',x=self.n(w-79),y=self.n(43),up=self.bitmap('eq_thumb2.png'),down=self.bitmap('eq_thumb2_do.png'),points=f'(0,0),(0,{self.n(h-90)})',value=f'tree_{c}.slider',lefttop='righttop',rightbottom='rightbottom')
                    self.button(l,'m_open',32,h-31,'playlist.add()','Add media',lefttop='leftbottom')
                elif kind=='video':
                    E.SubElement(l,'Video',x=self.n(34),y=self.n(37),width=self.n(w-68),height=self.n(h-67),rightbottom='rightbottom')
                    self.button(l,'vid_zoom',w-89,6,'vlc.fullscreen()','Fullscreen',lefttop='righttop')
                else:
                    self.image(l,'eq_vlc_back',33,35)
                    for i,dx in enumerate([14,27,39,52,64,77,90,102,115,128]):
                        E.SubElement(l,'Slider',x=self.n(33+dx+8),y=self.n(35+25),up=self.bitmap('eq_thumb.png'),down=self.bitmap('eq_thumb_do.png'),points=f'(0,{self.n(60)}),(0,0)',thickness=self.n(13),value=f'equalizer.band({i})',tooltiptext=f'VLC equalizer band {i+1}')
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
            self.frame(l,1,413,282,bottom='info_bot_right')
            self.button(l,'m_close',345,6,'info.hide()','Close information')
            self.image(l,'c_back.png',14,34)
            if page=='about':
                texture=rgba('eq_back.png').crop((200,90,220,106))
                key=self.bitmap('about_carbon',texture)
                E.SubElement(l,'Image',image=key,x=self.n(37),y=self.n(35),width=self.n(338),height=self.n(219),resize='mosaic')
                # Credit stays in the information panel, away from media.
                for y,t in [(91,'VLC conversion'),(112,'Dead Signal Interactive'),(143,'Original skin: The Skins Factory'),(164,'Need for Speed Underground'),(184,'Copyright 2003 Electronic Arts Inc.')]:
                    self.text(l,t,64,y,290,color='#00AEEF' if y<140 else '#D1D1D1',small=True)
            elif page=='menu':
                self.image(l,'c_back.jpg',37,35)
                mapping=Image.open(SOURCE/'c_menu_map.png').convert('RGB')
                for i,(color,target) in enumerate([((0,0,255),'c_sub_1_1'),((0,51,255),'c_sub_2_1'),((0,102,255),'c_sub_3_1'),((0,153,255),'c_sub_4_1')]):
                    mask=Image.eval(ImageChops.difference(mapping,Image.new('RGB',mapping.size,color)).convert('L'),lambda x:255 if x==0 else 0)
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
                    if i+1<len(members):self.button(l,'c_nav_next',348,226,f'info.setLayout(info_{members[i+1]})','Next page')
            if page=='menu':
                self.text(l,'Dead Signal Interactive',93,257,225,color='#B7BBC8',small=True)
                # The original information button artwork opens conversion credits.
                self.button(l,'m_info',310,248,'info.setLayout(info_about)','About this VLC conversion')
        win.append(win[0])

    def save(self):
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
            for p in sorted(self.out.rglob('*')):
                if p.is_file():z.write(p,p.relative_to(self.out).as_posix())
        return path


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
        if node.tag=='Button':assert node.get('action') not in ('none',None)
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
