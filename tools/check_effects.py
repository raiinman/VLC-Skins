"""Offline sound/hover command contracts; never starts a player or helper."""
import argparse
from copy import deepcopy
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from lxml import etree as E

from assets import ThemeAssets
from build import ROOT, SKIN, SOURCE
from skin_support import add_support, playback_action


SOUNDS = [('button', 'button.wav'), ('shutter', 'shutter.wav'),
          ('intro', 'intro4.wav'), ('info', 'imode.wav'), ('logo', 'eagames.wav')]
ACTION_KEYS = ('action', 'action1', 'action2')
SIGNAL = re.compile(r'\bnfs_fx_\w+\.(?:show\(\)|setLayout\(nfs_fx_\w+_trigger\))')


def trigger(event):
    return f'nfs_fx_{event}.setLayout(nfs_fx_{event}_trigger);'


def source_mapping():
    wms = E.fromstring((SOURCE/'nfs.wms').read_bytes(), E.XMLParser(recover=True))
    mapping = {}
    filenames = {filename:key for key, filename in SOUNDS}
    for node in wms.iter():
        onclick = node.get('onClick') or ''
        found = re.search(r"checkSoundPref\('([^']+)'\)", onclick)
        if found and node.get('image'):
            mapping[node.get('image').replace('.', '_')] = filenames[found.group(1)]
    assert mapping['m_info_no_png'] == 'button'
    assert mapping['m_logo_no_png'] == 'logo'
    assert mapping['m_shutter_no_png'] == 'shutter'
    info = wms.find('view[@id="infoView"]')
    assert info.get('onLoad') == 'loadInfoPrefs()'
    script = (SOURCE/'nfs.js').read_text(encoding='utf-16')
    body = re.search(r'function\s+loadInfoPrefs\s*\([^)]*\)([\s\S]*?)(?=\nfunction |\Z)', script)
    assert body and "checkSoundPref('imode.wav')" in body.group(1)
    return mapping


def verify_actions(tree):
    mapping = source_mapping()
    signals = 0
    for node in tree.iter():
        key = node.get('up') or node.get('up1') or ''
        for attr in ACTION_KEYS:
            action = node.get(attr)
            if action is None:
                continue
            original = playback_action(action)
            interactive = node.tag in ('Button', 'Checkbox')
            decorative = (node.get('id') or '').startswith('decorative_')
            if not interactive or decorative:
                assert not SIGNAL.search(action), (node.get('id'), 'Effects must not attach to sliders, images or animation masks')
                continue
            assert not SIGNAL.search(original), (node.get('id'), 'Sound signals must be a leading addition only')
            sound = mapping.get(key)
            if key.startswith('shutter_locked'):
                sound = 'shutter'
            if 'main.setLayout(main_start)' in original:
                sound = 'intro'
            events = []
            if sound and original not in ('none', ''):
                events.append(sound)
                if key == 'm_info_no_png' and 'info.show()' in original:
                    events.append('info')
            expected = ''.join(trigger(event) for event in events)+original
            assert action == expected, (node.get('id'), attr, action, expected)
            signals += len(events)
    return signals


def verify_windows(tree, scale):
    for index, (key, _) in enumerate(SOUNDS):
        name = 'nfs_fx_'+key
        windows = tree.findall(f'Window[@id="{name}"]')
        assert len(windows) == 1
        window = windows[0]
        assert (window.get('x'), window.get('y')) == ('-31000', '-31000')
        assert window.get('visible') == 'true', 'Signals must not call OS show during a click'
        assert window.get('dragdrop') == window.get('playondrop') == 'false'
        assert len(window) == 2
        assert {layout.get('id') for layout in window} == {name+'_ready', name+'_trigger'}
        assert window[-1].get('id') == name+('_trigger' if key == 'intro' else '_ready')
        for state, width in [('ready', 41+index), ('trigger', 51+index)]:
            layout = window.find(f'Layout[@id="{name}_{state}"]')
            assert (layout.get('width'), layout.get('height')) == (str(width), '17')
            assert len(layout) == 1 and layout[0].tag == 'Image'
            image = layout[0]
            assert (image.get('x'), image.get('y'), image.get('width'), image.get('height')) == ('0', '0', str(width), '17')
            assert image.get('image') == 'nfs_effect_marker' and image.get('resize') == 'scale'
            assert image.get('action2') == f'{name}.setLayout({name}_ready)', 'Helper must reset the native signal without OS show/hide'
            assert image.get('action', 'none') == image.get('action1', 'none') == 'none'
    windows = tree.findall('Window[@id="nfs_hover_command"]')
    assert len(windows) == 1
    window = windows[0]
    assert (window.get('x'), window.get('y'), window.get('visible')) == ('-31000', '-30900', 'true')
    assert window.get('dragdrop') == window.get('playondrop') == 'false'
    assert len(window) == 1
    layout = window[0]
    assert (layout.get('id'), layout.get('width'), layout.get('height')) == ('nfs_hover_command_layout', '67', '17')
    assert len(layout) == 2 and all(node.tag == 'Image' for node in layout)
    for image, x, target in zip(layout, ('0', '33'), ('video_hover_controls', 'video_hover_closed')):
        assert (image.get('x'), image.get('y'), image.get('width'), image.get('height')) == (x, '0', '33', '17')
        assert image.get('image') == 'nfs_effect_marker' and image.get('resize') == 'scale'
        assert image.get('action2') == f'videoHoverController.setLayout({target})'
        assert image.get('action', 'none') == image.get('action1', 'none') == 'none'
    assert len(tree.findall('.//Video')) == 1, 'Effects must not create a second video output'


def verify_manifest(directory, scale, package):
    manifest_bytes = (directory/'nfs-effects.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    expected = dict(schemaVersion=1, scale=scale,
                    sounds=[dict(id=key, file='sounds/'+filename, width=51+i, readyWidth=41+i, height=17)
                            for i, (key, filename) in enumerate(SOUNDS)],
                    command=dict(width=67, height=17, showX=2, hideX=35, y=2),
                    hover=dict(width=426*scale, height=146*scale, closedWidth=427*scale, closedHeight=scale),
                    video=dict(width=708*scale, height=440*scale))
    assert manifest == expected, 'Helper manifest schema, event IDs or geometry changed'
    assert package.read('nfs-effects.json') == manifest_bytes
    for key, filename in SOUNDS:
        original = (SOURCE/filename).read_bytes()
        assert original[:4] == b'RIFF' and original[8:12] == b'WAVE'
        assert (directory/'sounds'/filename).read_bytes() == original, (key, 'Source WAV changed')
        assert package.read('sounds/'+filename) == original, (key, 'Packaged WAV changed')


def check_action_filter():
    assert playback_action(trigger('button')+'vlc.play()') == 'vlc.play()'
    assert playback_action(trigger('button')+trigger('info')+'info.show()') == 'info.show()'
    for original in ('video.show();'+trigger('button')+'vlc.play()', trigger('unknown')+'vlc.play()',
                     'nfs_fx_button.setLayout(nfs_fx_info_trigger);vlc.play()',
                     'nfs_fx_button.setLayout(nfs_fx_button_ready);vlc.play()',
                     'nfs_fx_button.show();vlc.play()', 'nfs_fx_button.hide();vlc.play()', 'vlc.fullscreen()', 'none'):
        assert playback_action(original) == original, 'Only known leading effects may be removed'


def synthetic_check(scale):
    # Temporary support assets only: never instantiate Builder or touch vlc-Nx.
    with tempfile.TemporaryDirectory(prefix='nfs-effects-fixture-') as temporary:
        parent = Path(temporary)
        original = parent/'original'; original.mkdir()
        for filename in ['nfs.wms']+[name for _, name in SOUNDS]:
            shutil.copyfile(SOURCE/filename, original/filename)
        class Synthetic:
            def bitmap(self, name, image, prescaled=False):
                assert prescaled and image.size == (1, 1)
                assert image.getpixel((0, 0)) == (0, 0, 0, 255)
                E.SubElement(self.theme, 'Bitmap', id=name, file='unused.png')
                return name
        builder = Synthetic(); builder.scale = scale
        builder.out = parent/'fixture'; builder.out.mkdir()
        builder.theme = E.Element('Theme')
        window = E.SubElement(builder.theme, 'Window', id='main')
        layout = E.SubElement(window, 'Layout', id='main_1')
        cases = [('open', 'm_open_no_png', 'dialogs.fileSimple()'),
                 ('logo', 'm_logo_no_png', 'info.show()'),
                 ('replay', 'm_shutter_no_png', 'palette_state.setLayout(palette_1);main.setLayout(main_start);info.hide()'),
                 ('shutter', 'shutter_locked_no_png', 'main.setLayout(main_1_closing)'),
                 ('silent', 'm_close_no_png', 'video.hide()')]
        for identity, up, action in cases:
            E.SubElement(layout, 'Button', id=identity, up=up, action=action)
        E.SubElement(layout, 'Checkbox', id='play', up1='m_play_no_png', action1='vlc.play()', action2='vlc.pause()')
        E.SubElement(layout, 'Checkbox', id='info', up1='m_info_no_png', action1='info.show()', action2='info.hide()')
        E.SubElement(layout, 'Slider', id='volume', value='volume')
        E.SubElement(layout, 'Button', id='decorative_test', up='shutter_open', action='none')
        video = E.SubElement(builder.theme, 'Window', id='video')
        E.SubElement(E.SubElement(video, 'Layout', id='video_1'), 'Video')
        saved = [(node, {attr:node.get(attr) for attr in ACTION_KEYS if node.get(attr) is not None})
                 for node in builder.theme.iter()]
        original_videos = len(builder.theme.findall('.//Video'))
        files = add_support(builder)
        for node, actions in saved:
            for attr, action in actions.items():
                assert playback_action(node.get(attr)) == action, 'Support replaced an original action'
        assert len(builder.theme.findall('.//Video')) == original_videos
        signals = verify_actions(builder.theme)
        verify_windows(builder.theme, scale)
        assert files == {'nfs-effects.json'} | {'sounds/'+name for _, name in SOUNDS}
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            for filename in files:
                archive.writestr(filename, (builder.out/filename).read_bytes())
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            verify_manifest(builder.out, scale, archive)
        changed = deepcopy(builder.theme)
        changed.find('.//Button[@id="open"]').set('action', trigger('logo')+'dialogs.fileSimple()')
        try:
            verify_actions(changed)
        except AssertionError:
            pass
        else:
            raise AssertionError('Wrong source sound mutation escaped')
        changed = deepcopy(builder.theme)
        changed.find('Window[@id="nfs_fx_button"]/Layout/Image').set('action2', 'nfs_fx_button.hide()')
        try:
            verify_windows(changed, scale)
        except AssertionError:
            pass
        else:
            raise AssertionError('Focus-stealing show/hide signal reset escaped')
        return signals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true', help='Use synthetic temporary fixtures only')
    args = parser.parse_args()
    check_action_filter()
    for scale in (1, 2):
        fixture_signals = synthetic_check(scale)
        if args.self_test:
            print(f'PASS {scale}x: synthetic fixture preserves actions, {fixture_signals} source sound signals, manifest/WAV identity and command geometry')
            continue
        assets = ThemeAssets(SKIN/f'vlc-{scale}x')
        signals = verify_actions(assets.tree)
        verify_windows(assets.tree, scale)
        assert assets.image('nfs_effect_marker').size == (1, 1)
        assert assets.image('nfs_effect_marker').getpixel((0, 0)) == (0, 0, 0, 255)
        with zipfile.ZipFile(ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt') as package:
            verify_manifest(assets.directory, scale, package)
            packaged = E.fromstring(package.read('theme.xml'))
            assert E.tostring(packaged, method='c14n') == E.tostring(assets.tree, method='c14n')
            assert verify_actions(packaged) == signals
            verify_windows(packaged, scale)
        print(f'PASS {scale}x: {signals} source-derived sound signals; five original WAVs, exact manifest and resettable offscreen commands; source actions retained')


if __name__ == '__main__':
    main()
