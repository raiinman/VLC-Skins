"""Prepare or explicitly run real docking gestures on a private non-input desktop.

Uses copied portable VLC, exact VLTs, private saved positions, retained process
identities and job cleanup. Never positions panes with SetWindowPos or touches
the physical pointer. Without --actual-vlc, only prepares/compiles the fixture.
"""
import argparse
from copy import deepcopy
import json
import os
import shutil
from pathlib import Path
import subprocess
import zipfile
from lxml import etree as E

from assets import ThemeAssets
from check_panels import layers, ownership
from check_hover_native import ROOT, OwnedJob, actual_requests, silent_video, sha
from windows_load_host import DesktopProcess, ProcessGuard, input_desktop


def shared_plugin_requests(output, installed):
    """Copy only the exact exe; load standard installed DLLs/plugins read-only."""
    runtime=output/'VlcRuntime'/sha(installed)
    runtime.mkdir(parents=True)
    shutil.copyfile(installed,runtime/'vlc.exe')
    (runtime/'portable').mkdir()
    assert sorted(p.name for p in runtime.iterdir())==['portable','vlc.exe']
    data=output/'skin-support-data'
    shutil.copytree(ROOT/'dist/skin-support/data',data)
    requests,hashes=[],{}
    for scale in (1,2):
        folder=output/f'{scale}x'; folder.mkdir()
        skin=folder/f'Need-for-Speed-Underground-{scale}x.vlt'
        source=ROOT/'dist'/skin.name
        shutil.copyfile(source,skin); hashes[str(scale)]=sha(source)
        assert sha(skin)==hashes[str(scale)]
        config=folder/'vlcrc.ini'; log=folder/'vlc.log'; clip=folder/'silent-fixture.png'
        silent_video(clip)
        temporary=folder/'Temp';temporary.mkdir()
        environment={'APPDATA':str(folder/'AppData'),'LOCALAPPDATA':str(folder/'LocalAppData'),
            'TEMP':str(temporary),'TMP':str(temporary),'VLC_DATA_PATH':str(data),
            'VLC_PLUGIN_PATH':str(installed.parent/'plugins'),
            'PATH':str(installed.parent)+os.pathsep+os.environ.get('PATH','')}
        arguments=['--no-one-instance','--no-one-instance-when-started-from-file','--no-media-library',
            '--config='+str(config),'--intf=skins2','--skins2-last='+str(skin),'--no-qt-privacy-ask',
            '--no-metadata-network-access','--aout=dummy','--vout=wingdi','--demux=image',
            '--image-duration=600','--image-fps=10/1','--verbose=2','--file-logging','--logfile='+str(log),str(clip)]
        requests.append(dict(scale=scale,executable=str(runtime/'vlc.exe'),installed=str(installed),
            workingDirectory=str(installed.parent),sharedInstalledPlugins=True,
            arguments=subprocess.list2cmdline(arguments),skin=str(skin),log=str(log),environment=environment))
    path=output/'requests.json';path.write_text(json.dumps(requests),encoding='utf-8')
    return path,hashes


def addon_video_request(request, addon_folder):
    """Private derived package. The only fixture-only cell is explicit video.hide()."""
    from companion_hud_apply import apply_companion_hud
    base=Path(request['skin']); derived=base.with_name(base.stem+'-addon-video-test.vlt')
    with zipfile.ZipFile(base) as archive:
        xml,payloads=apply_companion_hud(archive.read('theme.xml'),addon_folder)
        tree=E.fromstring(xml)
        command=tree.find('./Window[@id="yt_playback_actions"]')
        assert command is not None
        for layout in command:
            existing=layout.find('./Image[@x="100"]')
            assert existing is not None and existing.get('action2')=='video.show()'
            E.SubElement(layout,'Image',id=layout.get('id')+'_fixture_hide',image='yt_hud_command_hit',
                x='110',y='0',width='3',height='3',resize='scale',action2='video.hide()')
        xml=xml[:xml.index(b'<Theme')]+E.tostring(tree,encoding='UTF-8')
        with zipfile.ZipFile(derived,'w') as target:
            for entry in archive.infolist():
                target.writestr(entry,xml if entry.filename=='theme.xml' else archive.read(entry.filename))
            for name,content in payloads.items():target.writestr(name,content)
    config=base.parent/'vlcrc.ini';text=config.read_text(encoding='utf-8').replace(str(base),str(derived))
    extra=[]
    for window in tree.findall('Window'):
        if window.get('id') in ('yt_playback_actions','yt_cc_indicator','yt_hud_availability'):
            layout=window.findall('Layout')[-1]
            extra.append(f'["{window.get("id")}" "{layout.get("id")}" {window.get("x")} {window.get("y")} {layout.get("width")} {layout.get("height")} {int(window.get("visible")=="true")}]')
    text=text.rstrip('\n')+''.join(extra)+'\n';config.write_text(text,encoding='utf-8')
    request.update(skin=str(derived),arguments=request['arguments'].replace(str(base),str(derived)),addonVideoShow=True,
        derivedSkinSha256=sha(derived),baseSkinSha256=sha(base),addonManifestSha256=sha(addon_folder/'manifest.json'),testOnlyHideCell=[110,0])
    return request


def grip(assets, layout, scale, action, size=None):
    size = size or (int(layout.get('width')), int(layout.get('height')))
    items = layers(assets, layout, 1, size, False)
    owners = ownership(items, size)
    candidates = []
    for y in range(3, min(size[1]-3, 34*scale)) if action == 'move' else range(size[1]-24*scale+3, size[1]-3):
        for x in range(3, size[0]-3):
            index = owners.getpixel((x, y))
            if not index or items[index-1][0].get('action') != action:
                continue
            if all(owners.getpixel((x+dx,y+dy)) == index for dx in (-2,0,2) for dy in (-2,0,2)):
                candidates.append((x,y))
    assert candidates, (layout.get('id'), action, 'No safe native gesture grip')
    return min(candidates, key=lambda p: abs(p[0]-size[0]//2)+abs(p[1]-16*scale))


def prepare_cases(request, occlusion=False, snapping_toggle=False):
    scale = request['scale']
    with zipfile.ZipFile(request['skin']) as archive:
        tree = E.fromstring(archive.read('theme.xml'))
    assets = ThemeAssets(ROOT/f'skins/need-for-speed-underground/vlc-{scale}x')
    assert E.tostring(tree,method='c14n') == E.tostring(assets.tree,method='c14n'), 'Generated XML differs from tested package'
    selected = {'main':'main_1', 'tracks':'tracks_1', 'equalizer':'equalizer_1', 'video':'video_1', 'info':'info_menu'}
    panes, layouts, state = [], {}, {}
    for index, (name, layout_id) in enumerate(selected.items()):
        layout = assets.tree.find(f'.//Window[@id="{name}"]/Layout[@id="{layout_id}"]')
        assert layout is not None and len(layout.findall('Anchor')) == 4, (name,'Docking candidate required')
        layouts[name]=layout
        # Isolate pane-to-pane anchoring from the separately tested work-area
        # magnet. Native screen snapping runs before Anchor::canHang.
        position = ((100,100) if occlusion else (3000,3000)) if name=='main' else (5000+index*3000,6000)
        entry=dict(x=position[0],y=position[1],width=int(layout.get('width')),height=int(layout.get('height')))
        state[name]=entry
        gx,gy=grip(assets,layout,scale,'move')
        panes.append(dict(id=name,gripX=gx,gripY=gy,**entry))
    saved=[]
    for window in tree.findall('Window'):
        name=window.get('id'); layout=window.findall('Layout')[-1]
        if name in selected:
            layout=window.find(f'Layout[@id="{selected[name]}"]'); r=state[name]
            saved.append(f'["{name}" "{layout.get("id")}" {r["x"]} {r["y"]} {r["width"]} {r["height"]} 1]')
        else:
            saved.append(f'["{name}" "{layout.get("id")}" {window.get("x","0")} {window.get("y","0")} {layout.get("width")} {layout.get("height")} {int(window.get("visible","true")=="true")}]')
    config=Path(request['skin']).parent/'vlcrc.ini'
    config.write_text('[skins2]\nskins2-last='+request['skin']+'\nskins2-config='+''.join(saved)+'\n',encoding='utf-8')
    if occlusion:
        return prepare_occlusion_cases(request, panes, state, assets, snapping_toggle)
    steps=[]
    grips={pane['id']:(pane['gripX'],pane['gripY']) for pane in panes}
    def move(name,x,y,label,expected=None,followers=()):
        old=state[name]; dx,dy=x-old['x'],y-old['y']
        gx,gy=grips[name]
        state[name]=dict(old,x=expected[0] if expected else x,y=expected[1] if expected else y)
        for follower in followers:
            state[follower]['x']+=state[name]['x']-old['x']; state[follower]['y']+=state[name]['y']-old['y']
        steps.append(dict(name=label,pane=name,kind='move',gripX=gx,gripY=gy,dx=dx,dy=dy,expected=deepcopy(state)))
    for name in ('tracks','equalizer','video','info'):
        main=state['main']; edge=main['x']+main['width']; top=main['y']
        move(name,edge+16,top,name+'-outside16-no-snap')
        move(name,edge+15,top,name+'-boundary15-no-snap')
        move(name,edge+14,top,name+'-within14-snaps',(edge,top))
        main=state['main']; move('main',main['x']+57,main['y']+43,name+'-main-carries-child',followers=(name,))
        if name=='tracks':
            # Attempt elapsed/remaining with the current independent clock state.
            # Geometry alone does not establish a successful mode change.
            clock=layouts['main'].find('Checkbox[@id="clock_1_open_0"]')
            assert clock is not None and clock.get('action1') == 'clock_state.setLayout(clock_remaining_a)'
            assert clock.get('action2') == 'clock_state.setLayout(clock_elapsed_a)'
            steps.append(dict(name='main-clock-click-attempt-preserves-geometry',pane='main',kind='click',gripX=int(clock.get('x'))+20*scale,gripY=int(clock.get('y'))+7*scale,dx=0,dy=0,expected=deepcopy(state)))
            main=state['main']; move('main',main['x']+41,main['y']+37,'main-after-clock-click-attempt-carries-child',followers=(name,))
        child=state[name]; move(name,child['x']+100,child['y']+90,name+'-child-detaches-alone')
        main=state['main']; move('main',main['x']+31,main['y']+29,name+'-detached-child-stays')
        if name in ('tracks','video'):
            for grow in (True,False):
                r=state[name]; gx,gy=grip(assets,layouts[name],scale,'resizeSE',(r['width'],r['height']))
                dx,dy=(70,50) if grow else (-1000,-1000)
                state[name]=dict(r,width=r['width']+70 if grow else int(layouts[name].get('minwidth')),height=r['height']+50 if grow else int(layouts[name].get('minheight')))
                steps.append(dict(name=name+('-grow' if grow else '-minimum-clamp'),pane=name,kind='resize',gripX=gx,gripY=gy,dx=dx,dy=dy,expected=deepcopy(state)))
                main=state['main']; r=state[name]
                # Exercise the resizable RIGHTTOP anchor against main LEFTTOP.
                move(name,main['x']-r['width']-14,main['y'],name+('-grown-right-anchor' if grow else '-minimum-right-anchor'),(main['x']-r['width'],main['y']))
                move(name,5000+len(steps)*20,6000,name+'-resize-detach')
        move(name,10000+len(steps)*30,6000,name+'-park')
    # Equal-priority panes snap, but moving either must leave its peer behind.
    video=state['video']; tracks=state['tracks']
    move('tracks',video['x']-tracks['width']-14,video['y'],'aux-to-aux-snaps',(video['x']-tracks['width'],video['y']))
    video=state['video']; move('video',video['x']+37,video['y']+41,'equal-priority-does-not-carry')
    request.update(panes=panes,steps=steps)
    return request


def prepare_occlusion_cases(request, panes, state, assets=None, snapping_toggle=False):
    steps=[]
    grips={pane['id']:(pane['gripX'],pane['gripY']) for pane in panes}
    def move(name,x,y,label,cover='none',expected=None,followers=()):
        old=state[name]
        dx,dy=x-old['x'],y-old['y']
        state[name]=dict(old,x=expected[0] if expected else x,y=expected[1] if expected else y)
        for follower in followers:
            state[follower]['x']+=state[name]['x']-old['x']; state[follower]['y']+=state[name]['y']-old['y']
        gx,gy=grips[name]
        steps.append(dict(name=label,pane=name,kind='move',cover=cover,gripX=gx,gripY=gy,dx=dx,dy=dy,expected=deepcopy(state)))
    main=state['main']; edge=main['x']+main['width']; top=main['y']
    move('tracks',edge+14,top,'unfiltered-covered-baseline-attracts','full',(edge,top))
    move('tracks',5000,3000,'baseline-detach','full')
    steps.append(dict(name='attach-exact-candidate-filter',pane='main',kind='bridge',cover='full',expected=deepcopy(state)))
    move('tracks',edge+14,top,'filtered-covered-target-does-not-attract','full')
    move('tracks',5000,3000,'covered-detach','full')
    move('tracks',edge+14,top,'filtered-partial-exposed-target-snaps','partial',(edge,top))
    move('main',main['x']+57,main['y']+43,'filtered-main-carries-attached-child',followers=('tracks',))
    child=state['tracks']; move('tracks',child['x']+100,child['y']+90,'filtered-child-detaches-alone')
    main=state['main'];edge=main['x']+main['width'];top=main['y']
    move('tracks',edge+14,top,'filtered-exposed-target-snaps',expected=(edge,top))
    move('tracks',5000,3000,'exposed-detach')
    move('tracks',14,1000,'filtered-screen-left-edge-retained',expected=(0,1000))
    move('tracks',5000,3000,'screen-edge-detach')
    if snapping_toggle:
        # Retain all original ON cases, then prove OFF/ON restoration without
        # changing the exact skin package or its native priority hierarchy.
        main=state['main'];edge=main['x']+main['width'];top=main['y']
        move('tracks',edge+14,top,'toggle-on-establish-attached-child',expected=(edge,top))
        steps.append(dict(name='set-snapping-off',pane='main',kind='toggle-off',cover='none',expected=deepcopy(state)))
        move('main',main['x']+57,main['y']+43,'snapping-off-main-does-not-carry-attached-child')
        main=state['main'];edge=main['x']+main['width'];top=main['y']
        move('tracks',edge+14,top,'snapping-off-pane-remains-fourteen-pixels-away')
        move('tracks',14,1000,'snapping-off-screen-remains-fourteen-pixels-away')
        move('tracks',edge,top,'snapping-off-exact-align-for-resize')
        r=state['tracks'];layout=assets.tree.find('.//Layout[@id="tracks_1"]')
        gx,gy=grip(assets,layout,request['scale'],'resizeSE',(r['width'],r['height']))
        state['tracks']=dict(r,width=r['width']+70,height=r['height']+50)
        steps.append(dict(name='snapping-off-resize-attached-pane-leaves-neighbors-fixed',pane='tracks',kind='resize',
            cover='none',gripX=gx,gripY=gy,dx=70,dy=50,expected=deepcopy(state)))
        steps.append(dict(name='restore-snapping-on',pane='main',kind='toggle-on',cover='none',expected=deepcopy(state)))
        main=state['main'];move('main',main['x']+41,main['y']+37,'restored-on-main-carries-aligned-child',followers=('tracks',))
        move('tracks',5000,3000,'restored-on-child-detaches')
        main=state['main'];edge=main['x']+main['width'];top=main['y']
        move('tracks',edge+14,top,'restored-on-pane-snaps',expected=(edge,top))
        move('tracks',14,1000,'restored-on-screen-snaps',expected=(0,1000))
        move('tracks',5000,3000,'restored-on-screen-detach')
        move('tracks',edge+14,top,'restored-on-covered-target-does-not-attract','full')
        move('tracks',5000,3000,'restored-on-covered-detach','full')
    steps.append(dict(name='remove-enable-marker-native-fallback',pane='main',kind='disable',cover='full',expected=deepcopy(state)))
    move('tracks',edge+14,top,'disabled-filter-covered-target-native-fallback','full',(edge,top))
    request.update(panes=panes,steps=steps,occlusion=True,snappingToggle=snapping_toggle)
    return request


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--actual-vlc',action='store_true')
    parser.add_argument('--addon-video-show',type=Path,help='Separate private addon-derived packages with a disclosed test-only hide cell')
    parser.add_argument('--snapping-toggle',action='store_true',help='Require native toggle support and test OFF/ON pane/screen/group restoration')
    parser.add_argument('--shared-installed-plugins',action='store_true',help='Copied EXE only, standard installed core/plugin modules with independent path/hash checks')
    parser.add_argument('--occlusion-dll',type=Path,help='Exact candidate DLL, enables owned foreign-cover docking cases')
    parser.add_argument('--protect-pid',type=int,action='append',default=[])
    parser.add_argument('--guard-file',type=Path,action='append',default=[])
    args=parser.parse_args(); output=args.output.resolve(); scratch=(ROOT.parent/'work').resolve()
    if not output.is_relative_to(scratch) or output==scratch: parser.error('Output must be a new work/ subdirectory')
    if args.snapping_toggle and not (args.shared_installed_plugins and args.occlusion_dll): parser.error('Toggle cases require shared plugin mode and --occlusion-dll')
    if args.shared_installed_plugins and not args.occlusion_dll: parser.error('Shared plugin mode requires --occlusion-dll')
    output.mkdir(parents=True,exist_ok=False)
    installed=Path('C:/Program Files/VideoLAN/VLC/vlc.exe')
    factory=shared_plugin_requests if args.shared_installed_plugins else actual_requests
    request_path,hashes=factory(output,installed)
    requests=[prepare_cases(item, bool(args.occlusion_dll), args.snapping_toggle) for item in json.loads(request_path.read_text())]
    if args.addon_video_show:
        requests=[addon_video_request(r,args.addon_video_show) for r in requests]
    if args.occlusion_dll:
        if not args.occlusion_dll.is_file(): parser.error('Candidate DLL is missing')
        shutil.copyfile(args.occlusion_dll, output/'NfsWheelBridge64.dll')
    request_path.write_text(json.dumps(requests),encoding='utf-8')
    compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    if not compiler.is_file(): compiler=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework/v4.0.30319/csc.exe'
    sources=[]
    for name in ('SkinEffects.cs','check_hover_native.cs','check_docking_native.cs'):
        copy=output/name; copy.write_bytes((ROOT/'tools'/name).read_bytes()); sources.append(copy)
    executable=output/'DockingNativeFixture.exe'
    command=[str(compiler),'/nologo','/target:winexe','/optimize+','/main:NfsSkinSupport.DockingNativeFixture','/out:'+str(executable)]
    command+=['/reference:'+name+'.dll' for name in ('System.Windows.Forms','System.Drawing','System.Web.Extensions','System.IO.Compression','System.IO.Compression.FileSystem')]
    compiled=subprocess.run(command+list(map(str,sources)),capture_output=True,text=True)
    if compiled.returncode: raise RuntimeError(compiled.stdout+compiled.stderr)
    provenance=dict(derived_packages=[{k:r[k] for k in ('scale','derivedSkinSha256','baseSkinSha256','addonManifestSha256','testOnlyHideCell')} for r in requests if r.get('addonVideoShow')],snapping_toggle=args.snapping_toggle,shared_installed_plugins=args.shared_installed_plugins,candidate_dll_sha256=sha(output/'NfsWheelBridge64.dll'),packages=hashes,sources={p.name:sha(p) for p in sources},fixture_sha256=sha(executable))
    if not args.actual_vlc:
        (output/'prepared.json').write_text(json.dumps(dict(provenance,launched=False,cases=sum(len(r['steps']) for r in requests)),indent=2))
        print('Prepared only; no native process launched.'); return 0
    installed_skins=Path('C:/Program Files/VideoLAN/VLC/skins')
    user_skins=Path(os.environ['APPDATA'])/'vlc/skins'
    paths=[Path(os.environ['APPDATA'])/'vlc/vlcrc',Path(os.environ['APPDATA'])/'vlc/vlc-qt-interface.ini',
           *installed_skins.glob('*.vlt'),*user_skins.glob('*.vlt'),*args.guard_file]
    if args.shared_installed_plugins:
        paths += [installed,installed.parent/'libvlc.dll',installed.parent/'libvlccore.dll',
                  installed.parent/'plugins/gui/libskins2_plugin.dll',installed.parent/'plugins/plugins.dat']
    paths=list(dict.fromkeys(p.resolve() for p in paths))
    before={str(p):sha(p) for p in paths}; desktop=input_desktop(); guards=[]; process=None; job=None
    report={'passed':False}; result=output/'fixture.json'; cleanup=[]
    try:
        for pid in args.protect_pid: guards.append(ProcessGuard(pid))
        env=dict(os.environ); env['TEMP']=env['TMP']=str(output)
        process=DesktopProcess([str(executable),str(result),str(request_path)],env)
        job=OwnedJob(process); Path(str(request_path)+'.ready').write_text('Owned job armed\n')
        status=process.wait(360)
        if result.exists(): report=json.loads(result.read_text(encoding='utf-8-sig'))
        report['fixture_exit_code']=status
    finally:
        for item in (job,process):
            if item is not None:
                try:item.close()
                except Exception as error:cleanup.append(str(error))
        after={str(p):sha(p) for p in paths}
        report.update(provenance,cleanup_errors=cleanup,input_desktop_unchanged=input_desktop()==desktop,guarded_files_unchanged=before==after,
                      protected_processes=[dict(pid=g.pid,alive=g.alive()) for g in guards],owned_fixture_closed=process is not None and process.handle is None,
                      skin_copies_unchanged=all(sha(output/f'{scale}x'/f'Need-for-Speed-Underground-{scale}x.vlt')==value for scale,value in hashes.items()),
                      derived_skin_copies_unchanged=all(sha(Path(r['skin']))==r['derivedSkinSha256'] for r in requests if r.get('addonVideoShow')))
        for g in guards:g.close()
        report['passed']=bool(report.get('passed') and report.get('fixture_exit_code')==0 and not cleanup and report['input_desktop_unchanged'] and report['guarded_files_unchanged'] and report['owned_fixture_closed'] and report['skin_copies_unchanged'] and report['derived_skin_copies_unchanged'] and all(g['alive'] for g in report['protected_processes']))
        (output/'preservation.json').write_text(json.dumps(dict(before=before,after=after),indent=2))
        (output/'result.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(passed=report['passed'],cases=len(report.get('cases',[])),report=str(output/'result.json'))))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
