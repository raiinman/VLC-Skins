"""Offline palette stability and explicit-profile migration checks; no VLC."""
from pathlib import Path
import re
import tempfile
import zipfile

from lxml import etree as E
from assets import ThemeAssets, visible
from build import ROOT, SKIN
from migrate_palette import migrate, migrate_file
from skin_support import playback_action


def check_theme(assets):
    state = assets.tree.find('Window[@id="palette_state"]')
    assert state is not None and state.get('visible') == 'false'
    assert (state.get('x'), state.get('y')) == ('0', '0')
    assert {node.get('id') for node in state} == {f'palette_{c}' for c in range(1, 8)}
    assert state[-1].get('id') == 'palette_1', 'Fresh themes must start blue'
    for layout in state:
        assert (layout.get('width'), layout.get('height')) == ('1', '1')
        assert len(layout) == 1 and layout[0].tag == 'Image'
        assert assets.image(layout[0].get('image')).getchannel('A').getbbox() is None
    panes = [w for w in assets.tree.findall('Window') if w.get('id') not in ('main', 'palette_state')]
    pane_nodes = [node for window in panes for node in window.iter() if node.tag not in ('Window', 'Layout')]
    for node in pane_nodes:
        expression = node.get('visible', 'true')
        assert not re.search(r'\bmain_\w*\.isActive', expression), 'Pane paint must not depend on transient main layout activity'
        if 'palette_' in expression:
            assert re.fullmatch(r'palette_[1-7]\.isActive', expression), expression
    main = assets.tree.find('Window[@id="main"]')
    temporal = 0
    for layout in main:
        lid = layout.get('id')
        c = 1 if lid == 'main_start' else int(re.fullmatch(r'main_([1-7]).*', lid).group(1))
        for node in layout:
            actions = [node.get(key, '') for key in ('action', 'action1', 'action2')]
            is_color = node.get('up') == 'm_color_no_png'
            if is_color:
                expected = f'palette_state.setLayout(palette_{c%7+1});'
                assert playback_action(actions[0]).startswith(expected), (lid, 'Palette state must change before the main color')
            else:
                assert not any('palette_state.setLayout(' in action for action in actions), (lid, node.get('id'), 'Clock/shutter must leave palette state untouched')
        if lid == 'main_start':
            continue
        flags = {f'palette_{color}.isActive': color == c for color in range(1, 8)}
        # VLC deactivates the previous main layout before activating its target.
        # The independent palette remains fixed through this all-main-inactive gap.
        destination = f'main_{c}_closing' if '_closing' not in lid else f'main_{c}'
        for node in pane_nodes:
            expression = node.get('visible')
            before = visible(expression, lid, flags=flags)
            gap = visible(expression, '__no_main_layout__', flags=flags)
            after = visible(expression, destination, flags=flags)
            assert before == gap == after, (lid, node.get('id'), 'Auxiliary pane visibility changed during main transition')
        temporal += 1
    assert temporal == 56
    replay = assets.tree.find('.//Button[@tooltiptext="Replay original startup animation"]')
    assert playback_action(replay.get('action')).startswith('palette_state.setLayout(palette_1);')
    return temporal


def check_migrations():
    suffixes = ('', '_remaining', '_opening', '_opening_remaining', '_closed', '_closed_remaining', '_closing', '_closing_remaining')
    count = 0
    for c in range(1, 8):
        for suffix in suffixes:
            prefix = '\ufeff# keep Unicode: 路径\r\n[core]\r\nvolume=123\r\n[skins2]\r\nskins2-config='
            saved = f'["main" "main_{c}{suffix}" -30 42 300 298 1] ["video" "video_1" 800 -9 1400 900 0]'
            tail = '\r\nskins2-last=C:/skin.vlt\r\n# untouched\r\n'
            text = prefix+saved+tail
            added = f'["palette_state" "palette_{c}" 0 0 1 1 0]'
            result = migrate(text)
            assert result == prefix+saved+added+tail
            assert migrate(result) == result, 'Migration must be idempotent'
            stale = prefix+saved+'["palette_state" "palette_7" 8 9 2 3 1]'+tail
            assert migrate(stale) == result
            count += 1
    assert migrate('skins2-config=["main" "main_start" 60 60 300 298 1]\n') == 'skins2-config=["main" "main_start" 60 60 300 298 1]["palette_state" "palette_1" 0 0 1 1 0]\n'
    invalid = ('', '[skins2]\n', 'skins2-config=\r\n', 'skins2-config=garbage\n',
               'skins2-config=["main" "unknown" 1 2 3 4 1]\n',
               'skins2-config=["main" "main_3" 1 2 3 4 1]trailing\n',
               'skins2-config=["main" "main_3" 1 2 3 4 1]["main" "main_4" 1 2 3 4 1]\n',
               'skins2-config=["main" "main_3" 1 2 3 4 1]\nskins2-config=\n')
    for text in invalid:
        assert migrate(text) == text, 'Unrecognized saved state must remain unchanged'
    scratch = ROOT.parent/'work'
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='palette-migration-check-', dir=scratch) as folder:
        path = Path(folder)/'explicit-fixture.ini'
        original = '\ufeff# 路径\r\n[skins2]\r\nskins2-config=["main" "main_4_closed_remaining" 15 25 300 298 1]\r\n'.encode('utf-8')
        path.write_bytes(original)
        backup = migrate_file(path)
        assert backup.read_bytes() == original
        assert path.read_bytes() == migrate(original.decode('utf-8')).encode('utf-8')
        assert migrate_file(path) is None
        assert len(list(Path(folder).glob('*.palette-backup-*'))) == 1
    return count+1


def main():
    for scale in (1, 2):
        assets = ThemeAssets(SKIN/f'vlc-{scale}x')
        count = check_theme(assets)
        with zipfile.ZipFile(ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt') as archive:
            assert E.tostring(E.fromstring(archive.read('theme.xml')), method='c14n') == E.tostring(assets.tree, method='c14n')
        print(f'PASS {scale}x: independent palette state; {count} main states preserve every auxiliary visibility through inactive gaps')
    print(f'PASS palette migration: {check_migrations()} main palette/state variants; exact preference/position preservation, backup and idempotence')


if __name__ == '__main__':
    main()
