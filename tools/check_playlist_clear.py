"""Check both actual playlist clear controls and reject broken protocol/placement.

No queue, desktop or running-player access. Confirmation dispatch belongs to
the companion host; these checks establish packaged native controls only.
"""
import copy
import zipfile

from lxml import etree as E

from assets import ThemeAssets
from build import ROOT, SKIN
from check_panels import verify as verify_panel_hits


def verify(tree, assets, scale):
    command = tree.find('./Window[@id="playlist_clear_command"]')
    assert command is not None and command.get('x') == '-31000' and command.get('y') == '-30100'
    assert command.get('visible') == 'true'
    assert [(n.get('id'), n.get('width'), n.get('height')) for n in command] == [
        ('playlist_clear_requested', '162', '17'), ('playlist_clear_ready', '161', '17')]
    expected = [(0, 'playlist_clear_command.setLayout(playlist_clear_ready)'),
                (10, 'playlist_clear_capability.setLayout(playlist_clear_enabled)'),
                (20, 'playlist_clear_capability.setLayout(playlist_clear_disabled)')]
    for layout in command:
        assert [(int(n.get('x')), n.get('action2')) for n in layout] == expected
        for n in layout:
            assert n.get('y') == '0' and assets.image(n.get('image')).size == (1, 1)
            assert assets.image(n.get('image')).getpixel((0, 0))[3] == 1
    capability = tree.find('./Window[@id="playlist_clear_capability"]')
    assert capability is not None and capability.get('visible') == 'true'
    assert (capability.get('x'), capability.get('y')) == ('-31000', '-30000')
    assert [(n.get('id'), n.get('width'), n.get('height')) for n in capability] == [
        ('playlist_clear_enabled', '172', '1'), ('playlist_clear_disabled', '171', '1')]
    for layout in tree.findall('./Window[@id="tracks"]/Layout'):
        buttons = layout.findall('./Button[@tooltiptext="Clear playlist..."]')
        assert len(buttons) == 1
        b = buttons[0]
        assert b.get('action') == 'playlist_clear_command.setLayout(playlist_clear_requested)'
        assert b.get('visible') == 'playlist_clear_enabled.isActive'
        assert b.get('lefttop') == b.get('rightbottom') == 'leftbottom'
        assert int(b.get('x')) == 64*scale and int(b.get('y')) == int(layout.get('height'))-31*scale
        states = [assets.image(b.get(key)) for key in ('up', 'over', 'down')]
        assert all(im.size == (29*scale, 29*scale) for im in states)
        assert len({im.tobytes() for im in states}) == 3
        for im in states:
            assert im.getchannel('A').getbbox() and im.getpixel((0, 0))[3] == 0
        # Folder right edge60, clear left64; both stay in the bottom margin.
        assert int(b.get('x')) > 61*scale
        assert int(b.get('y')) >= int(layout.get('height'))-31*scale
        assert int(b.get('y'))+29*scale <= int(layout.get('height'))
        armed = copy.deepcopy(layout)
        armed.find('./Button[@tooltiptext="Clear playlist..."]').set('visible', 'true')
        for width, height in [(int(layout.get('width')), int(layout.get('height'))),
                              (int(layout.get('minwidth')), int(layout.get('minheight'))),
                              (900*scale, 650*scale)]:
            for checked in (False, True):
                verify_panel_hits(assets, armed, 1, (width, height), checked, scale)


def main():
    for scale in (1, 2):
        assets = ThemeAssets(SKIN/f'vlc-{scale}x')
        with zipfile.ZipFile(ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt') as z:
            tree = E.fromstring(z.read('theme.xml'))
        verify(tree, assets, scale)
        mutations = [
            ('.//Button[@tooltiptext="Clear playlist..."]', 'visible', 'true'),
            ('.//Button[@tooltiptext="Clear playlist..."]', 'action', 'playlist.del()'),
            ('.//Button[@tooltiptext="Clear playlist..."]', 'x', str(40*scale)),
            ('.//Layout[@id="playlist_clear_ready"]', 'width', '160'),
            ('.//Image[@id="playlist_clear_ready_ack"]', 'action2', 'none'),
            ('.//Window[@id="playlist_clear_capability"]', 'visible', 'false')]
        for selector, attr, value in mutations:
            bad = copy.deepcopy(tree); bad.find(selector).set(attr, value)
            try:
                verify(bad, assets, scale)
            except AssertionError:
                continue
            raise AssertionError('Accepted mutation: '+selector+' '+attr)
        print(f'PASS {scale}x: clear button geometry, 3 feedback states, capability default, request/ACK protocol; 6 mutations rejected')


if __name__ == '__main__':
    main()
