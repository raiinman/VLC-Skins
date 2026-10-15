"""Offline shutter timing, input gate and layout-transition regression checks."""
from PIL import Image, ImageChops
from assets import ThemeAssets
from build import SKIN, SOURCE, Builder
from check_source_art import source_pixels, scaled


def destination(node):
    action=node.get('action').split(';')[-1]
    assert action.startswith('main.setLayout(') and action.endswith(')'), action
    return action[len('main.setLayout('):-1]


for scale in (1,2):
    assets=ThemeAssets(SKIN/f'vlc-{scale}x')
    for state,order in (('open',range(2,13)),('close',range(11,0,-1))):
        for light in (False,True):
            key='shutter_'+state+('_light' if light else '')
            resource=assets.resources[key]
            assert (resource.get('nbframes'),resource.get('fps'),resource.get('loop'))==('11','20','1')
            for index,frame in enumerate(order):
                expected=source_pixels(SOURCE/('shutter_light.png' if light else f'shutter_f0{frame}.png'))
                if light:
                    opacity=index/10 if state=='close' else 1-index/10
                    expected.putalpha(expected.getchannel('A').point(lambda a:round(a*opacity)))
                assert assets.frame(key,index).tobytes()==scaled(expected,scale).tobytes(),(scale,key,index)

    gate=assets.resources['shutter_transition_blocker']
    assert (gate.get('nbframes'),gate.get('fps'),gate.get('loop'))==('2','2','1')
    # One 500 ms hold, then no hit pixels. Hover/press must use this same bitmap.
    union=Image.new('L',assets.frame('shutter_transition_blocker').size)
    for suffix in ('no','hov','do'):
        mask=scaled(source_pixels(SOURCE/f'm_shutter_{suffix}.png'),scale).getchannel('A')
        union=ImageChops.lighter(union,mask)
    expected=union.point(lambda a:1 if a else 0)
    assert assets.frame('shutter_transition_blocker',0).getchannel('A').tobytes()==expected.tobytes()
    assert assets.frame('shutter_transition_blocker',1).getchannel('A').getbbox() is None

    count=0
    for color in range(1,8):
        for state in ('open','opening','closed','closing'):
            for remaining in (False,True):
                lid=Builder.main_id(color,state,remaining)
                layout=assets.tree.find(f'.//Layout[@id="{lid}"]')
                shut=state in ('closed','closing')
                target=Builder.main_id(color,'opening' if shut else 'closing',remaining)
                shutter=layout.find('Button[@tooltiptext="Open shutter"]' if shut else 'Button[@tooltiptext="Close shutter"]')
                assert destination(shutter)==target,(lid,'shutter destination')
                for attr in ('up','over','down'):
                    assert assets.resources[shutter.get(attr)].get('nbframes','1')=='1',(lid,'hover leave restarts shutter lock')
                palette=layout.find('Button[@up="m_color_no_png"]')
                assert destination(palette)==Builder.main_id(color%7+1,'closed' if shut else 'open',remaining)
                if state!='closed':
                    clock=next(n for n in layout if n.get('id','').startswith('clock_'))
                    assert destination(clock)==Builder.main_id(color,'closing' if state=='closing' else 'open',not remaining)
                if state in ('opening','closing'):
                    blocker=layout.find('Button[@up="shutter_transition_blocker"]')
                    assert blocker is not None and blocker.get('action')=='none'
                    assert not blocker.get('over') and not blocker.get('down'),'Changing gate state would restart its timer'
                    assert list(layout).index(blocker)>list(layout).index(shutter)
                    assert (blocker.get('x'),blocker.get('y'))==(shutter.get('x'),shutter.get('y'))
                else:
                    assert layout.find('Button[@up="shutter_transition_blocker"]') is None
                count+=1
    print(f'PASS {scale}x: 44 source shutter/light frames, 500 ms one-shot input gate, {count} clock/palette/shutter states')
