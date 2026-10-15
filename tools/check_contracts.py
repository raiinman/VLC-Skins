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
    assert assets.resources['clock'].get('size')==str(14*scale)
    for panel in ('tracks','video'):
        handle=windows[panel].find('.//Image[@action="resizeSE"]')
        assert handle is not None and handle.get('image')=='resize_hit'
        assert assets.image('resize_hit').getchannel('A').getextrema()==(1,1),'Transparent resize handle cannot receive VLC input'
    for layout in windows['main']:
        for node in layout.findall('Text'):
            assert node.get('visible')==layout.get('id')+'.isActive','Inactive clock rasterization'
    replay=tree.find('.//Layout[@id="info_about"]/Button[@tooltiptext="Replay original startup animation"]')
    assert replay is not None,'Restored layouts need a way to replay the original intro'
    assert replay.get('action')=='main.setLayout(main_1);main.setLayout(main_start);main.show();info.hide()'
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
    scroll=tree.find('.//Playtree/Slider')
    assert scroll.get('points')==f'(0,{230*scale}),(0,0)','Playlist top must map to native value 1'
    eq=tree.find('.//Layout[@id="equalizer_1"]')
    for c in range(1,8):
        assert eq.find(f'Image[@image="info_bot_right_{c}_png"]') is not None,'Source EQ corner is smooth'
        assert eq.find(f'Image[@image="f_bot_right_{c}_png"]') is None
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
                if state in ('open','opening','closing'):
                    clock=next(n for n in layout if n.get('id','').startswith('clock_'))
                    clock_state='closing' if state=='closing' else 'open'
                    assert clock.get('action')==f'main.setLayout({Builder.main_id(c,clock_state,not remaining)})'
                    token='$l' if remaining else '$t'
                    assert layout.find(f'Text[@text="{token}"]') is not None
                    assert (layout.find('Image[@image="time_dash_png"]') is not None)==remaining
                    metadata=layout.find('Text[@text="$N"]')
                    assert metadata is not None
                    assert metadata.get('color')==['#00AEEF','#00AEEF','#C4DF9B','#A864A8','#F26D7D','#F69679','#FFF568'][c-1]
                    if state=='closing':
                        assert layout.find(f'Button[@up="shutter_endpoint_{c}"]') is not None or layout.find(f'Button[@up="shutter_endpoint_{c}_band_0"]') is not None
                palette=next(n for n in layout if n.get('up')=='m_color_no_png')
                target=Builder.main_id(c%7+1,'closed' if state in ('closed','closing') else 'open',remaining)
                assert palette.get('action')==f'main.setLayout({target})'
        for lid in [Builder.main_id(c),Builder.main_id(c,'closing',True)]:
            for frame in tree.findall('.//Image[@image="f_top_left_1_png"]'):
                assert visible(frame.get('visible'),lid)==(c==1)
    for key,name,n,h,reverse in [('volume_forward','volume.png',29,52,True),('seek_forward','seek.png',33,68,True)]:
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
    for c in range(1,8):
        key=f'shutter_endpoint_{c}'
        for frame in range(10):assert assets.frame(key,frame).getchannel('A').getbbox() is None
        expected=assets.image(f'main_back_{c}_png').copy()
        expected.alpha_composite(assets.image('shutter_light_png'),(21*scale,32*scale))
        expected.alpha_composite(assets.image('shutter_f01_png'),(54*scale,52*scale))
        last=assets.frame(key,10)
        for x,y,w,h in [(81,65,138,52),(71,164,156,68),(108,102,85,93),(58,134,182,31),(62,117,177,18),(120,167,69,18)]:
            actual=last.crop(tuple(v*scale for v in (x-54,y-52,x+w-54,y+h-52)))
            closed=expected.crop(tuple(v*scale for v in (x,y,x+w,y+h)))
            assert actual.tobytes()==closed.tobytes(),(c,'closed endpoint pixels')
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
