"""Offline independent time-mode/phase regression checks. Never launches VLC."""
import argparse
from copy import deepcopy
from pathlib import Path
from types import MethodType
import zipfile
from lxml import etree as E
from assets import visible
from build import Builder

ROOT=Path(__file__).resolve().parents[1]
STATES=('clock_elapsed_a','clock_elapsed_b','clock_remaining_a','clock_remaining_b')
REMAINING='(clock_remaining_a.isActive or clock_remaining_b.isActive)'


def flags(owner,mode,phase,active=True):
    return {owner:active,**{s+'.isActive':s=='clock_'+mode+'_'+phase for s in STATES}}


def verify(tree,scale,baseline=None):
    windows=tree.findall("Window[@id='clock_state']")
    assert len(windows)==1
    state=windows[0]
    assert dict(state.attrib)==dict(id='clock_state',x='-31000',y='-30200',visible='true',dragdrop='false',playondrop='false')
    assert [n.get('id') for n in state]==['clock_elapsed_b','clock_remaining_a','clock_remaining_b','clock_elapsed_a']
    sizes={'clock_elapsed_a':151,'clock_elapsed_b':152,'clock_remaining_a':153,'clock_remaining_b':154}
    for layout in state:
        lid=layout.get('id')
        assert dict(layout.attrib)==dict(id=lid,width=str(sizes[lid]),height='17')
        assert len(layout)==1
        marker=layout[0]
        other=lid[:-1]+('b' if lid.endswith('a') else 'a')
        assert dict(marker.attrib)==dict(id='clock_marker_'+lid.removeprefix('clock_'),image='clock_refresh_hit',x='0',y='0',action2='clock_state.setLayout('+other+')')
    command=tree.find("Window[@id='clock_refresh_command']")
    assert command is not None and dict(command.attrib)==dict(id='clock_refresh_command',x='-31000',y='-29900',visible='true',dragdrop='false',playondrop='false')
    assert len(command)==1 and dict(command[0].attrib)==dict(id='clock_refresh_commands',width='181',height='17')
    assert len(command[0])==2
    for node,(mode,x) in zip(command[0],[('elapsed',0),('remaining',10)]):
        assert dict(node.attrib)==dict(id='clock_refresh_'+mode,image='clock_refresh_hit',x=str(x),y='0',
            action2=f'clock_state.setLayout(clock_{mode}_a);clock_state.setLayout(clock_{mode}_b)')
    ids=[n.get('id') for n in tree.iter() if n.get('id')]
    assert len(ids)==len(set(ids))
    count=0
    for layout in tree.findall("Window[@id='main']/Layout"):
        lid=layout.get('id');owner=lid+'.isActive'
        clocks=[n for n in layout if n.tag=='Checkbox' and n.get('id','').startswith('clock_')]
        texts=layout.findall('Text[@font="clock"]')
        if not clocks:
            assert '_closed' in lid and not texts
            continue
        assert len(clocks)==1 and len(texts)==4
        clock=clocks[0]
        assert clock.get('state')==REMAINING
        assert clock.get('action1')=='clock_state.setLayout(clock_remaining_a)'
        assert clock.get('action2')=='clock_state.setLayout(clock_elapsed_a)'
        assert clock.get('action') is None and clock.get('up1')==clock.get('up2')=='clock_hit'
        assert clock.get('tooltiptext') is None and clock.get('tooltiptext1')=='Show remaining time' and clock.get('tooltiptext2')=='Show elapsed time'
        assert (clock.get('x'),clock.get('y'))==(str(120*scale),str(167*scale))
        for text in texts:
            assert (text.get('x'),text.get('y'),text.get('width'))==(str(129*scale),str(165*scale),str(60*scale))
        assert [n.get('text') for n in texts].count('$t')==2 and [n.get('text') for n in texts].count('$l')==2
        dash=layout.findall('Image[@image="time_dash_png"]');assert len(dash)==1
        for mode in ('elapsed','remaining'):
            selected=[]
            for phase in ('a','b'):
                current=flags(owner,mode,phase)
                shown=[n for n in texts if visible(n.get('visible'),flags=current)]
                assert len(shown)==1 and shown[0].get('text')==('$l' if mode=='remaining' else '$t')
                selected.append(shown[0].get('id'))
                assert visible(dash[0].get('visible'),flags=current)==(mode=='remaining')
                assert visible(clock.get('state'),flags=current)==(mode=='remaining')
                current[owner]=False
                assert not any(visible(n.get('visible'),flags=current) for n in texts+dash)
            assert selected[0]!=selected[1], 'Phase must switch native Text visibility'
        for node in layout:
            if node is not clock:
                assert not any('clock_state.' in v for k,v in node.attrib.items() if k.startswith('action'))
        count+=1
    assert count==43
    for wid,lid in (('fullscreenController','fullscreen_controls'),('videoHoverController','video_hover_controls')):
        layout=tree.find("Window[@id='%s']/Layout[@id='%s']"%(wid,lid))
        texts=layout.findall('Text[@text="$t / $d"]');assert len(texts)==2
        owner=wid+'.isVisible' if wid=='fullscreenController' else lid+'.isActive'
        shown_ids=[]
        for phase in ('a','b'):
            for mode in ('elapsed','remaining'):
                current=flags(owner,mode,phase)
                shown=[n for n in texts if visible(n.get('visible'),flags=current)]
                assert len(shown)==1
                if mode=='elapsed':shown_ids.append(shown[0].get('id'))
                current[owner]=False
                assert not any(visible(n.get('visible'),flags=current) for n in texts)
        assert shown_ids[0]!=shown_ids[1]
    if baseline is not None:
        oldids={n.get('id') for n in baseline.iter() if n.get('id')}
        assert oldids<=set(ids),'Existing IDs lost'
        for window in baseline.findall('Window'):
            actual=tree.find("Window[@id='%s']"%window.get('id'))
            assert dict(actual.attrib)==dict(window.attrib)
            for layout in window.findall('Layout'):
                current=actual.find("Layout[@id='%s']"%layout.get('id'));assert dict(current.attrib)==dict(layout.attrib)
                for node in layout:
                    skip=node.get('id','').startswith('clock_') or node.get('font')=='clock' or node.get('image')=='time_dash_png' or (window.get('id') in ('fullscreenController','videoHoverController') and node.get('text')=='$t / $d')
                    if skip:continue
                    match=current.find("*[@id='%s']"%node.get('id'))
                    assert match is not None and E.tostring(match,method='c14n',with_tail=False)==E.tostring(node,method='c14n',with_tail=False),('Non-clock node changed',node.get('id'))
        assert [E.tostring(n,method='c14n') for n in tree.findall('Bitmap') if n.get('id')!='clock_refresh_hit']==[E.tostring(n,method='c14n') for n in baseline.findall('Bitmap')]
    return count


def legacy_input(tree):
    baseline=deepcopy(tree)
    existing=baseline.find("Window[@id='clock_state']")
    if existing is None:return baseline
    baseline.remove(existing)
    command=baseline.find("Window[@id='clock_refresh_command']")
    if command is not None:baseline.remove(command)
    for resource in baseline.findall(".//*[@id='clock_refresh_hit']"):resource.getparent().remove(resource)
    for window in baseline.findall('Window'):
        for layout in window.findall('Layout'):
            for node in list(layout):
                identifier=node.get('id','')
                if identifier.startswith(('clock_alternate_','clock_dash_','clock_phase_b_')):layout.remove(node)
                elif node.tag=='Text' and node.get('font')=='clock':node.set('visible',layout.get('id')+'.isActive')
                elif node.tag=='Text' and node.get('text')=='$t / $d' and window.get('id') in ('fullscreenController','videoHoverController'):
                    node.set('visible',window.get('id')+'.isVisible' if window.get('id')=='fullscreenController' else layout.get('id')+'.isActive')
                elif node.tag=='Image' and node.get('image')=='time_dash_png':node.attrib.pop('visible',None)
                elif node.tag=='Checkbox' and identifier.startswith('clock_'):
                    node.tag='Button'
                    for attr in ('state','action1','action2','up1','up2'):node.attrib.pop(attr,None)
                    node.set('up','clock_hit');node.set('action','main.setLayout(main_1)')
    return baseline


def self_test(tree,scale):
    baseline=legacy_input(tree)
    builder=Builder.__new__(Builder);builder.theme=deepcopy(baseline);builder.scale=scale
    def bitmap(self,name,im=None,**kwargs):
        assert name=='clock_refresh_hit' and im.size==(1,1) and im.getpixel((0,0))==(0,0,0,1) and kwargs=={'prescaled':True}
        E.SubElement(self.theme,'Bitmap',id=name,file='assets/'+name+'.png',alphacolor='#FF00FF')
        return name
    builder.bitmap=MethodType(bitmap,builder)
    builder.independent_clock();candidate=builder.theme
    dtd=E.DTD(str(ROOT/'vendor/skin.dtd'))
    assert dtd.validate(E.ElementTree(candidate)),str(dtd.error_log)
    count=verify(candidate,scale,baseline)
    failures=('layout-jump','wrong-state','always-visible','missing-text','dash','shutter','palette-reset','id-loss','phase-reset-mode','hud-phase','clock-geometry',
              'fixed-command-mode','fixed-command-cell','fixed-command-single-phase')
    for failure in failures:
        changed=deepcopy(candidate);layout=changed.find("Window[@id='main']/Layout[@id='main_1_opening']")
        clock=next(n for n in layout if n.tag=='Checkbox' and n.get('id','').startswith('clock_'))
        if failure=='layout-jump':clock.set('action1','main.setLayout(main_1)')
        elif failure=='wrong-state':clock.set('state','main_1_remaining.isActive')
        elif failure=='always-visible':layout.find('Text[@font="clock"]').set('visible','true')
        elif failure=='missing-text':layout.remove(layout.find('Text[@font="clock"]'))
        elif failure=='dash':layout.find('Image[@image="time_dash_png"]').set('visible','true')
        elif failure=='shutter':layout.find('Button[@help="Decorative shutter animation"]').set('action','main.setLayout(main_1)')
        elif failure=='palette-reset':layout.find('Button[@up="m_color_no_png"]').set('action','clock_state.setLayout(clock_elapsed_a)')
        elif failure=='id-loss':clock.set('id','lost_original_clock_id')
        elif failure=='phase-reset-mode':changed.find("Window[@id='clock_state']/Layout[@id='clock_remaining_a']/Image").set('action2','clock_state.setLayout(clock_elapsed_b)')
        elif failure=='clock-geometry':layout.find('Text[@font="clock"]').set('x','0')
        elif failure=='hud-phase':changed.find("Window[@id='videoHoverController']/Layout/Text[@text='$t / $d']").set('visible','true')
        elif failure=='fixed-command-mode':changed.find(".//Image[@id='clock_refresh_remaining']").set('action2','clock_state.setLayout(clock_elapsed_a);clock_state.setLayout(clock_elapsed_b)')
        elif failure=='fixed-command-cell':changed.find(".//Image[@id='clock_refresh_elapsed']").set('x','1')
        elif failure=='fixed-command-single-phase':changed.find(".//Image[@id='clock_refresh_elapsed']").set('action2','clock_state.setLayout(clock_elapsed_b)')
        try:verify(changed,scale,baseline)
        except AssertionError:pass
        else:raise AssertionError('Clock regression escaped: '+failure)
    return count,len(failures)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    for scale in (1,2):
        with zipfile.ZipFile(ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt') as archive:tree=E.fromstring(archive.read('theme.xml'))
        if args.self_test:
            count,rejected=self_test(tree,scale)
            print(f'PASS {scale}x memory: {count} clocks +2HUDs, four native visibility phases, {rejected} mutations; original controls/art/timing/IDs preserved')
        else:
            count=verify(tree,scale)
            from assets import ThemeAssets
            assets=ThemeAssets(ROOT/f'skins/need-for-speed-underground/vlc-{scale}x')
            assert assets.image('clock_refresh_hit').getpixel((0,0))==(0,0,0,1)
            print(f'PASS {scale}x package: {count} clocks +2HUDs, mode-preserving refresh commands and alpha1 offscreen cell')
    print('Offline scope: no native paused-seek display/latency or animation timer continuity certification.')


if __name__=='__main__':main()
