"""Independent offline native corner-docking oracle; never launches VLC.

Models VLC3.0.23 Position, Anchor and WindowManager dependency rules. Passing
models do not certify native drag smoothness or arbitrary sliding-edge docking.
"""
import argparse
from copy import deepcopy
from itertools import combinations
from pathlib import Path
import zipfile

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
REAL = ('main', 'tracks', 'equalizer', 'video', 'info')
REFS = ('lefttop', 'righttop', 'leftbottom', 'rightbottom')
SUFFIXES = ('tl', 'tr', 'bl', 'br')


def position(anchor, original, current):
    """Native Builder::makePosition then Position::getLeft/getTop."""
    ow, oh = original
    cw, ch = current
    x, y = int(anchor.get('x')), int(anchor.get('y'))
    reference = anchor.get('lefttop')
    if reference in ('righttop', 'rightbottom'):
        x = (x - ow + 1) + cw - 1
    if reference in ('leftbottom', 'rightbottom'):
        y = (y - oh + 1) + ch - 1
    return x, y


def can_snap(stationary, moving, offset=(0, 0), visible=True):
    # WindowManager excludes invisible stationary/moving windows before
    # comparing anchors. Point-to-point canHang uses a strict Euclidean range.
    if not visible:
        return None
    dx = stationary[0] - moving[0] - offset[0]
    dy = stationary[1] - moving[1] - offset[1]
    if dx*dx + dy*dy < 15*15:
        return stationary[0]-moving[0], stationary[1]-moving[1]
    return None


def hangs(parent, child, parent_priority, child_priority):
    return parent_priority > child_priority and parent == child


def dimensions(layout):
    w, h = int(layout.get('width')), int(layout.get('height'))
    low = (int(layout.get('minwidth', w)), int(layout.get('minheight', h)))
    high = (int(layout.get('maxwidth', w)), int(layout.get('maxheight', h)))
    assert low[0] <= w <= high[0] and low[1] <= h <= high[1]
    return tuple(dict.fromkeys((low, (w, h), ((low[0]+high[0])//2, (low[1]+high[1])//2),
                               high, (low[0],high[1]), (high[0],low[1]))))


def verify(tree, include_youtube=False):
    assert tree.get('magnet', '15') == '15', 'Screen edge magnetism changed'
    real = (*REAL, 'youtube') if include_youtube else REAL
    ids = [n.get('id') for n in tree.iter() if n.get('id')]
    assert len(ids) == len(set(ids)), 'Duplicate explicit IDs'
    counts = dict(layouts=0, anchors=0, positions=0, pairs=0)
    selected = {}
    for window in tree.findall('Window'):
        name = window.get('id')
        if name not in real:
            assert not window.findall('.//Anchor'), ('Excluded window has docking anchors',name)
            continue
        layouts = window.findall('Layout')
        assert layouts
        selected[name] = layouts
        for layout in layouts:
            anchors = layout.findall('Anchor')
            assert len(anchors) == 4, ('Four corner anchors required',layout.get('id'))
            w, h = int(layout.get('width')), int(layout.get('height'))
            expected_points = ((0,0),(w,0),(0,h),(w,h))
            for i, anchor in enumerate(anchors):
                expected = dict(id='dock_'+layout.get('id')+'_'+SUFFIXES[i],
                    x=str(expected_points[i][0]),y=str(expected_points[i][1]),
                    lefttop=REFS[i],points='(0,0)',range='15',
                    priority='2' if name == 'main' else '1')
                assert dict(anchor.attrib) == expected and len(anchor) == 0, ('Docking contract changed',layout.get('id'),i)
                for cw, ch in dimensions(layout):
                    assert position(anchor,(w,h),(cw,ch)) == ((0,cw,0,cw)[i],(0,0,ch,ch)[i])
                    counts['positions'] += 1
            counts['layouts'] += 1
            counts['anchors'] += 4
    assert set(selected) == set(real), 'Missing real pane'
    # Exercise every distinct real-pane pair and all of their layout variants.
    # The right boundary of A snaps to B's left boundary with no shared pixel.
    for a_name,b_name in combinations(real,2):
        for a in selected[a_name]:
            aw,ah = int(a.get('width')),int(a.get('height'))
            for b in selected[b_name]:
                bw,bh = int(b.get('width')),int(b.get('height'))
                for a_size in dimensions(a):
                    for b_size in dimensions(b):
                        ac=[position(n,(aw,ah),a_size) for n in a.findall('Anchor')]
                        bc=[position(n,(bw,bh),b_size) for n in b.findall('Anchor')]
                        # Right, left, above and below contacts. Resized outer
                        # bounds meet exactly, never sharing a painted pixel.
                        contacts=((ac[1],bc[0],(14,0)),(ac[0],bc[1],(-14,0)),
                                  (ac[0],bc[2],(0,-14)),(ac[2],bc[0],(0,14)))
                        for side,(stationary,local_moving,delta) in enumerate(contacts):
                            desired_origin=(stationary[0]-local_moving[0],stationary[1]-local_moving[1])
                            moving=(stationary[0]+delta[0],stationary[1]+delta[1])
                            assert can_snap(stationary,moving)==(-delta[0],-delta[1])
                            if side==0: assert desired_origin[0]==a_size[0]
                            elif side==1: assert desired_origin[0]==-b_size[0]
                            elif side==2: assert desired_origin[1]==-b_size[1]
                            else: assert desired_origin[1]==a_size[1]
                            pa,pb=(2 if a_name=='main' else 1),(2 if b_name=='main' else 1)
                            assert hangs(stationary,stationary,pa,pb)==(a_name=='main')
                            assert not hangs(stationary,stationary,pb,pa)
                            counts['pairs']+=1
    return counts


def source_semantics():
    samples = 0
    for origin in ((0,0),(-1920,-1080),(2560,1440)):
        for delta in ((14,0),(-14,0),(0,14),(0,-14),(10,10),(-10,-10)):
            moving = (origin[0]+delta[0],origin[1]+delta[1])
            assert can_snap(origin,moving) == (-delta[0],-delta[1])
            assert can_snap(origin,moving,visible=False) is None
            samples += 1
        for delta in ((15,0),(-15,0),(0,15),(0,-15),(9,12),(11,11),(16,0)):
            assert can_snap(origin,(origin[0]+delta[0],origin[1]+delta[1])) is None
            samples += 1
    assert hangs((0,0),(0,0),2,1)
    assert not hangs((0,0),(0,0),1,2)
    assert not hangs((0,0),(0,0),1,1)
    assert not hangs((0,0),(1,0),2,1)
    # Dependency direction: dragging main carries its directly aligned child;
    # dragging that child never includes main or another equal-priority pane.
    dependencies = {'main': {'tracks'}, 'tracks': set(), 'video': set()}
    def moving_set(name):
        found={name}
        for child in dependencies[name]: found.update(moving_set(child))
        return found
    assert moving_set('main') == {'main','tracks'}
    assert moving_set('tracks') == {'tracks'}
    # stopMove builds dependencies even for hidden aligned real panes. This is
    # intentionally NOT a claim that hidden attached children never move.
    assert hangs((0,0),(0,0),2,1)  # independent of visibility by native design
    for reference, expected in zip(REFS,((0,0),(120,0),(0,80),(120,80))):
        initial=(500,400)
        x=500 if 'right' in reference else 0
        y=400 if 'bottom' in reference else 0
        anchor=E.Element('Anchor',x=str(x),y=str(y),lefttop=reference)
        before=position(anchor,initial,initial)
        after=position(anchor,initial,(620,480))
        assert (after[0]-before[0],after[1]-before[1]) == expected
    return samples


def mutations(tree):
    failures=('missing','oversized-curve','wrong-reference','pixel-overlap','range','priority','excluded','duplicate','screen-magnet')
    for failure in failures:
        changed=deepcopy(tree)
        layout=changed.find("Window[@id='main']/Layout")
        anchors=layout.findall('Anchor')
        if failure=='missing': layout.remove(anchors[-1])
        elif failure=='oversized-curve': anchors[0].set('points','(0,0),(8192,0)')
        elif failure=='wrong-reference': anchors[1].set('lefttop','lefttop')
        elif failure=='pixel-overlap': anchors[1].set('x',str(int(anchors[1].get('x'))-1))
        elif failure=='range': anchors[0].set('range','30')
        elif failure=='priority': anchors[0].set('priority','1')
        elif failure=='excluded':
            window=E.SubElement(changed,'Window',id='nfs_test_state')
            other=E.SubElement(window,'Layout',id='nfs_test_state_layout',width='1',height='1')
            other.append(deepcopy(anchors[0]))
        elif failure=='duplicate': anchors[1].set('id',anchors[0].get('id'))
        elif failure=='screen-magnet': changed.set('magnet','0')
        try: verify(changed)
        except AssertionError: pass
        else: raise AssertionError('Unsafe docking mutation escaped: '+failure)
    return len(failures)


def self_test(tree):
    # The generator is used only as the candidate. Expectations above are
    # independent and never import its coordinate/priority tables.
    from docking import add_to_theme,add_window
    before=E.tostring(tree,method='c14n')
    candidate=deepcopy(tree)
    # Built packages already contain anchors. Strip only this candidate so
    # self-test still exercises fresh insertion rather than retention alone.
    for node in candidate.findall('.//Anchor'): node.getparent().remove(node)
    pristine=E.tostring(candidate,method='c14n')
    try: add_to_theme(candidate,('main','youtube'))
    except ValueError: pass
    else: raise AssertionError('Missing requested pane was accepted')
    assert E.tostring(candidate,method='c14n')==pristine, 'Failed request partially changed the theme'
    count=add_to_theme(candidate)
    result=verify(candidate)
    assert count==result['anchors']
    first=E.tostring(candidate,method='c14n')
    assert add_to_theme(candidate)==count and E.tostring(candidate,method='c14n')==first
    stripped=deepcopy(candidate)
    for node in stripped.findall('.//Anchor'): node.getparent().remove(node)
    original=deepcopy(tree)
    for node in original.findall('.//Anchor'): node.getparent().remove(node)
    assert E.tostring(stripped,method='c14n')==E.tostring(original,method='c14n'),'Existing controls/IDs/art changed'
    count_mutations=mutations(candidate)
    window=E.SubElement(candidate,'Window',id='youtube',x='0',y='0',visible='true')
    E.SubElement(window,'Layout',id='youtube_layout',width='708',height='640',minwidth='708',minheight='400',maxwidth='2000',maxheight='2000')
    assert add_window(candidate,'youtube')==4
    web=verify(candidate,True)
    for excluded in ('videoHoverController','palette_state','fullscreenController'):
        frozen=E.tostring(candidate,method='c14n')
        try: add_window(candidate,excluded)
        except ValueError: pass
        else: raise AssertionError('Excluded docking pane accepted')
        assert E.tostring(candidate,method='c14n')==frozen
    assert E.tostring(tree,method='c14n')==before
    return result,count_mutations,web['anchors']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    samples=source_semantics()
    for scale in (1,2):
        with zipfile.ZipFile(ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt') as z:
            tree=E.fromstring(z.read('theme.xml'))
        if args.self_test:
            counts,rejected,web=self_test(tree)
            print(f'PASS {scale}x memory candidate: {counts}, {rejected} rejected mutations, companion anchors={web}')
        else:
            counts=verify(tree)
            canonical=E.parse(str(ROOT/f'skins/need-for-speed-underground/vlc-{scale}x/theme.xml')).getroot()
            assert E.tostring(canonical,method='c14n')==E.tostring(tree,method='c14n')
            print(f'PASS {scale}x actual package: {counts}, {mutations(tree)} rejected mutations')
    print(f'PASS {samples} strict range/hidden eligibility cases; native-source corner/group models only, no VLC launch')


if __name__=='__main__': main()
