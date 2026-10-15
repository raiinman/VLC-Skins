"""Check pixel preservation, source controls, and state transitions."""
import re
from lxml import etree as E
from PIL import Image
from build import SKIN, SOURCE, Builder, validate, rgba
from assets import ThemeAssets, visible

for scale in (1,2):
    out=SKIN/f'vlc-{scale}x';validate(out);assets=ThemeAssets(out);tree=assets.tree
    windows={w.get('id'):w for w in tree.findall('Window')}
    layouts={l.get('id'):w.get('id') for w in windows.values() for l in w}
    assert windows['main'][-1].get('id')=='main_start'
    assert windows['info'][-1].get('id')=='info_menu'
    for node in tree.iter():
        if node.tag in ('Image','Button','Checkbox','Slider','Text','Video'):
            assert node.get('id') and node.get('id')!='none','VLC generated-ID collision risk'
        for attr in ('action','action1','action2'):
            for act in node.get(attr,'').split(';'):
                if '.setLayout(' in act:
                    w,l=re.fullmatch(r'(\w+)\.setLayout\((\w+)\)',act).groups()
                    assert layouts[l]==w,(act,layouts.get(l))
                    assert w not in ('video','tracks','equalizer')
                elif act.endswith(('.show()','.hide()')):assert act.split('.')[0] in windows,act
        if node.tag in ('Bitmap','SubBitmap'):
            image=assets.image(node.get('id'));frames=int(node.get('nbframes','1'))
            assert image.height%frames==0
            if node.tag=='SubBitmap':
                unpacked=Image.open(out/'assets'/f'{node.get("id")}.png').convert('RGBA')
                assert image.size==unpacked.size and image.tobytes()==unpacked.tobytes(),node.get('id')
        if node.tag=='Button' and not node.get('id','').startswith(('decorative_','clock_')):
            assert node.get('over') or node.get('tooltiptext')=='Skip original startup animation'
    for tag in ('Video','Playtree'):
        assert len(tree.findall('.//'+tag))==1,'Duplicate playback widget: '+tag
    assert len(tree.findall('.//Slider[@value="equalizer.band(0)"]'))==1
    original=E.fromstring((SOURCE/'nfs.wms').read_bytes(),E.XMLParser(recover=True))
    main=next(v for v in original.findall('view') if v.get('id')=='mainView')
    prefixes=['m_min','m_full','m_close','m_open','m_vis','m_pl','m_eq','m_next','m_stop','m_play','m_prev','m_color','m_info']
    for c in range(1,8):
        for state in ('open','opening','closed','closing'):
            for remaining in (False,True):
                lid=Builder.main_id(c,state,remaining);layout=tree.find(f'.//Layout[@id="{lid}"]')
                assert layout is not None,lid
                for prefix in prefixes:
                    source=next(n for n in main.iter() if n.get('image')==prefix+'_no.png')
                    node=next(n for n in layout if n.get('up')==prefix+'_no_png' or n.get('up1')==prefix+'_no_png')
                    assert (int(node.get('x')),int(node.get('y')))==(int(source.get('left'))*scale,int(source.get('top'))*scale),(lid,prefix)
                if state in ('open','opening'):
                    clock=next(n for n in layout if n.get('id','').startswith('clock_'))
                    assert clock.get('action')==f'main.setLayout({Builder.main_id(c,"open",not remaining)})'
                    token='$l' if remaining else '$t'
                    assert layout.find(f'Text[@text="{token}"]') is not None
                    assert (layout.find('Image[@image="time_dash_png"]') is not None)==remaining
                palette=next(n for n in layout if n.get('up')=='m_color_no_png')
                target=Builder.main_id(c%7+1,'closed' if state in ('closed','closing') else 'open',remaining)
                assert palette.get('action')==f'main.setLayout({target})'
        for lid in [Builder.main_id(c),Builder.main_id(c,'closing',True)]:
            for frame in tree.findall('.//Image[@image="f_top_left_1_png"]'):
                assert visible(frame.get('visible'),lid)==(c==1)
    for key,name,n,h,reverse in [('volume_png','volume.png',29,52,False),('seek_forward','seek.png',33,68,True)]:
        source=rgba(name)
        for i in range(n):
            index=n-1-i if reverse else i
            expected=source.crop((0,index*h,source.width,(index+1)*h))
            if scale==2:expected=expected.resize((expected.width*2,expected.height*2),Image.Resampling.LANCZOS)
            actual=assets.frame(key,i,n)
            assert actual.tobytes()==expected.tobytes(),(key,i,scale)
    for key in ('shutter_open','shutter_close'):
        assert assets.resources[key].get('fps')=='20'
        assert assets.resources[key].get('nbframes')=='11'
    for prefix in ('shutter_locked','shutter_locked_closed'):
        for suffix in ('hov','do'):
            key=prefix+'_'+suffix+'_png'
            assert assets.resources[key].get('nbframes','1')=='1'
            expected=rgba('m_shutter_'+suffix+'.png')
            if scale==2:expected=expected.resize((expected.width*2,expected.height*2),Image.Resampling.LANCZOS)
            assert assets.image(key).tobytes()==expected.tobytes(),key
    assert assets.resources['intro_sequence'].get('nbframes')=='81'
    assert assets.resources['intro_sequence'].get('fps')=='10'
    for seq in ('intro_sequence','intro_light_sequence','shutter_open','shutter_open_light'):
        node=assets.resources[seq];last=assets.frame(seq,int(node.get('nbframes'))-1)
        assert last.getchannel('A').getbbox() is None,(seq,'final frame must release input')
    for group,total in [(2,4),(3,9)]:
        first=tree.find(f'.//Layout[@id="info_c_sub_{group}_1"]')
        last=tree.find(f'.//Layout[@id="info_c_sub_{group}_{total}"]')
        assert first.find('Image[@image="c_nav_prev_dis_png"]') is not None
        assert last.find('Image[@image="c_nav_next_dis_png"]') is not None
    print(f'PASS {scale}x: lossless atlases, source coordinates, clock/palette states, frame isolation, source timing and menu boundaries')
