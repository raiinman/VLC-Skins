"""Check actual packaged snapping UI and protocol without a desktop/profile."""
import copy
import zipfile

from lxml import etree as E
from assets import ThemeAssets
from build import ROOT, SKIN


def verify(tree, assets, scale):
    command = tree.find('./Window[@id="snapping_command"]')
    assert command is not None
    assert (command.get('x'), command.get('y'), command.get('visible')) == ('-31000','-29800','true')
    assert [(n.get('id'),n.get('width'),n.get('height')) for n in command] == [
        ('snapping_requested','192','17'),('snapping_ready','191','17')]
    cells = [(0,'snapping_command.setLayout(snapping_ready)'),
             (10,'snapping_state.setLayout(snapping_enabled)'),
             (20,'snapping_state.setLayout(snapping_disabled)'),
             (30,'snapping_state.setLayout(snapping_unavailable)')]
    for layout in command:
        assert [(int(n.get('x')),n.get('action2')) for n in layout] == cells
        for n in layout:
            assert n.tag == 'Image' and n.get('y') == '0'
            im = assets.image(n.get('image'))
            assert im.size == (1,1) and im.getpixel((0,0))[3] == 1
    state = tree.find('./Window[@id="snapping_state"]')
    assert state is not None
    assert (state.get('x'),state.get('y'),state.get('visible')) == ('-31000','-29700','true')
    assert [(n.get('id'),n.get('width'),n.get('height')) for n in state] == [
        ('snapping_enabled','202','1'),('snapping_disabled','203','1'),('snapping_unavailable','201','1')]
    for window in (command,state):
        assert window.get('dragdrop') == window.get('playondrop') == 'false'
        assert not window.findall('.//Anchor')
    for layout in tree.findall('./Window[@id="tracks"]/Layout'):
        buttons = layout.findall('./Checkbox[@state="snapping_enabled.isActive"]')
        assert len(buttons) == 1
        b = buttons[0]
        assert b.get('id') == 'snapping_button_'+layout.get('id')
        assert b.get('visible') == 'snapping_enabled.isActive or snapping_disabled.isActive'
        assert b.get('lefttop') == b.get('rightbottom') == 'leftbottom'
        assert int(b.get('x')) == 96*scale
        assert int(b.get('y')) == int(layout.get('height'))-31*scale
        for key in ('action1','action2'):
            assert b.get(key) == 'snapping_command.setLayout(snapping_requested)'
        assert b.get('tooltiptext1') == 'Enable pane and screen snapping'
        assert b.get('tooltiptext2') == 'Disable pane and screen snapping'
        states = [assets.image(b.get(key)) for key in ('up1','over1','down1','up2','over2','down2')]
        assert all(im.size == (82*scale,29*scale) for im in states)
        assert len({im.tobytes() for im in states}) == 6
        for im in states:
            assert im.getchannel('A').getbbox() and im.getpixel((0,0))[3] == 0
        if scale == 1:
            assert tree.find('./Font[@id="snap_label"]').get('size')=='13'
            assert tree.find('./Font[@id="snap_status"]').get('size')=='12'
            texts=[n for n in layout.findall('Text') if n.get('id','').startswith('snapping_')]
            assert [(n.get('text'),n.get('font'),n.get('visible')) for n in texts]==[
                ('SNAP','snap_label','snapping_enabled.isActive or snapping_disabled.isActive'),
                ('ON','snap_status','snapping_enabled.isActive'),('OFF','snap_status','snapping_disabled.isActive')]
            for n in texts:
                assert n.get('focus')=='false' and n.get('scrolling')=='none'
                assert n.get('lefttop')==n.get('rightbottom')=='leftbottom'
                assert int(n.get('y'))==int(layout.get('height'))-(22 if n.get('text')=='SNAP' else 21)
        clear = layout.find('./Button[@tooltiptext="Clear playlist..."]')
        assert int(clear.get('x'))+29*scale < int(b.get('x'))
        # Footer buttons retain their separation when resizing, as both edges
        # use leftbottom. They cannot overlap the Playtree above them.
        assert int(b.get('y'))+29*scale <= int(layout.get('height'))


def main():
    for scale in (1,2):
        assets = ThemeAssets(SKIN/f'vlc-{scale}x')
        with zipfile.ZipFile(ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt') as z:
            tree = E.fromstring(z.read('theme.xml'))
        verify(tree,assets,scale)
        mutations = [
            ('.//Checkbox[@state="snapping_enabled.isActive"]','visible','true'),
            ('.//Checkbox[@state="snapping_enabled.isActive"]','x',str(80*scale)),
            ('.//Checkbox[@state="snapping_enabled.isActive"]','action2','vlc.onTop()'),
            ('.//Layout[@id="snapping_ready"]','width','190'),
            ('.//Image[@id="snapping_ready_ack"]','action2','none'),
            ('.//Image[@id="snapping_ready_off"]','x','10'),
            ('.//Window[@id="snapping_state"]','visible','false'),
            ('.//Layout[@id="snapping_unavailable"]','width','202')]
        for selector,attr,value in mutations:
            bad = copy.deepcopy(tree); bad.find(selector).set(attr,value)
            try:
                verify(bad,assets,scale)
            except AssertionError:
                continue
            raise AssertionError('Accepted mutation: '+selector+' '+attr)
        print(f'PASS {scale}x: snapping toggle placement, six feedback states, unavailable default, request/state protocol; 8 mutations rejected')


if __name__ == '__main__':
    main()
