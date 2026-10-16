"""Measure exact VLT loading on a private desktop/runtime, without user input."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time
import wave
from build import ROOT
from windows_load_host import DesktopProcess, ProcessGuard, input_desktop, owns_tcp


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def connection(process,port):
    if process.poll() is not None or not owns_tcp(process.pid,port):return None
    sock=socket.create_connection(('127.0.0.1',port),timeout=.2)
    sock.settimeout(.2)
    if not owns_tcp(process.pid,port,sock.getsockname()[1]):
        sock.close()
        return None
    return sock


def playing(process,port):
    try:
        sock=connection(process,port)
        if sock is None:return False
        with sock:
            sock.sendall(b'is_playing\n')
            reply=b''
            while len(reply)<65536:
                chunk=sock.recv(4096)
                if not chunk:break
                reply+=chunk
                if re.search(rb'(?:^|\n)1\r?\n',reply):return True
    except OSError:
        pass
    return False


def measure(vlc,scale,budget,session,observe_seconds):
    folder=session/f'{scale}x'
    folder.mkdir()
    config=folder/'vlcrc.ini'
    config.write_text('')
    log=folder/'vlc.log'
    source=ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt'
    skin=folder/source.name
    shutil.copyfile(source,skin)
    assert sha(skin)==sha(source)
    clip=folder/'silence.wav'
    with wave.open(str(clip),'wb') as sound:
        sound.setparams((1,2,8000,0,'NONE','not compressed'))
        sound.writeframes(bytes(8000*2*60))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    args=[str(vlc),'--no-one-instance','--no-one-instance-when-started-from-file',
          '--no-media-library',f'--config={config}','--intf=skins2',
          f'--skins2-last={skin}','--skins2-config=',
          '--no-qt-privacy-ask','--no-metadata-network-access','--aout=dummy',
          '--extraintf=rc',f'--rc-host=127.0.0.1:{port}','--rc-quiet',
          '--verbose=2','--file-logging',f'--logfile={log}',str(clip)]
    env=dict(os.environ)
    env['APPDATA']=str(folder/'AppData')
    env['LOCALAPPDATA']=str(folder/'LocalAppData')
    temporary=folder/'Temp'
    temporary.mkdir()
    env['TEMP']=env['TMP']=str(temporary)
    for key in ('VLC_PLUGIN_PATH','VLC_DATA_PATH','VLC_LIB_PATH'):
        env.pop(key,None)
    result=dict(scale=scale,sha256=sha(skin),budget_seconds=budget,
                autoplay_after_interface_ready_seconds=None,within_budget=False,
                process_alive_after_animation=False,theme_errors=[],error=None)
    process=None
    start=time.monotonic()
    try:
        process=DesktopProcess(args,env)
        result['test_pid']=process.pid
        while time.monotonic()-start<observe_seconds:
            # CLI autoplay begins only after skins2 Run() initializes the theme.
            # Never use RC play/add or buffered log arrival as the timing signal.
            if playing(process,port):
                elapsed=time.monotonic()-start
                result.update(autoplay_after_interface_ready_seconds=round(elapsed,2),
                              within_budget=elapsed<=budget,memory_at_ready_mib=process.memory())
                break
            if process.poll() is not None:
                raise RuntimeError('Owned VLC exited during initialization')
            time.sleep(.1)
        else:
            raise TimeoutError(f'Initialization not observed within {observe_seconds}s')
        time.sleep(8.5)
        result['process_alive_after_animation']=process.poll() is None
        result['memory_after_intro_mib']=process.memory() if process.poll() is None else None
        if not result['process_alive_after_animation']:
            raise RuntimeError('Owned VLC exited during startup animation')
    except Exception as error:
        result['error']=str(error)
    finally:
        if process:
            try:
                if process.poll() is None:
                    sock=connection(process,port)
                    if sock is not None:
                        with sock:sock.sendall(b'quit\n')
                    process.wait(10)
            except (OSError,subprocess.TimeoutExpired):
                pass
            finally:
                try:process.close()
                except OSError as error:result['cleanup_error']=str(error)
    text=log.read_text(errors='replace') if log.exists() else ''
    result['theme_configuration_logged']='loading theme configuration' in text
    result['requested_exact_skin_logged']=f'requested skins {skin} is  accessible' in text
    result['skin_copy_unchanged']=sha(skin)==result['sha256']
    result['fallback_logged']=bool(re.search(r'trying (?:the )?default skin|using default skin|failed to load the skin|no skins found',text,re.I))
    patterns={'skins2_error':r'skins2 error:', 'unknown_action_or_variable':r'unknown (action|variable)',
              'alpha_blend':r'AlphaBlend\(\) failed', 'pure_virtual':r'pure virtual'}
    result['theme_errors']=[name for name,pattern in patterns.items() if re.search(pattern,text,re.I)]
    result['passed']=bool(result['within_budget'] and result['process_alive_after_animation']
                          and result['theme_configuration_logged'] and result['requested_exact_skin_logged']
                          and result['skin_copy_unchanged'] and not result['fallback_logged']
                          and not result['theme_errors'] and not result['error'] and not result.get('cleanup_error'))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vlc',type=Path,default=Path('C:/Program Files/VideoLAN/VLC/vlc.exe'))
    parser.add_argument('--max-seconds',type=float,default=30)
    parser.add_argument('--observe-seconds',type=float,default=120)
    parser.add_argument('--protect-pid',type=int,action='append',default=[])
    parser.add_argument('--guard-file',type=Path,action='append',default=[])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert 0<args.max_seconds<=args.observe_seconds<=300
    session=ROOT.parent/'work'/f'load-isolated-{time.time_ns()}'
    session.mkdir(parents=True)
    normal=Path(os.environ['APPDATA'])/'vlc'
    paths=list(dict.fromkeys([normal/'vlcrc',normal/'vlc-qt-interface.ini',*args.guard_file]))
    before={str(path.resolve()):sha(path) for path in paths}
    desktop=input_desktop()
    guards=[]
    report=dict(scope='Exact skins, fresh explicit configs, copied portable VLC and private non-input desktop; no mouse/keyboard/focus APIs or helper launched.',
                runtime_sha256=sha(args.vlc),runtime_copy_seconds=None,input_desktop_unchanged=None,
                protected_processes=[],guarded_files_unchanged=None,results=[],
                limits='One run per scale; existing OS file caches, not a cold-machine test. Measures CLI autoplay after interface readiness, not visual timing or controls.')
    try:
        for pid in args.protect_pid:guards.append(ProcessGuard(pid))
        runtime=session/'runtime'
        start=time.monotonic()
        shutil.copytree(args.vlc.parent,runtime)
        (runtime/'portable').mkdir(exist_ok=True)
        copied=runtime/args.vlc.name
        assert sha(copied)==report['runtime_sha256']
        report['runtime_copy_seconds']=round(time.monotonic()-start,2)
        for scale in (1,2):
            assert all(guard.alive() for guard in guards),'Protected process exited before test'
            result=measure(copied,scale,args.max_seconds,session,args.observe_seconds)
            report['results'].append(result)
            print(json.dumps(result),flush=True)
            assert input_desktop()==desktop,'Input desktop changed externally'
            assert all(guard.alive() for guard in guards),'Protected process exited during test'
    finally:
        try:report['input_desktop_unchanged']=input_desktop()==desktop
        except OSError as error:report['input_desktop_unchanged']=False;report['input_desktop_error']=type(error).__name__
        try:
            report['protected_processes']=[dict(pid=guard.pid,creation_filetime=guard.started,still_alive=guard.alive()) for guard in guards]
        finally:
            for guard in guards:guard.close()
        try:
            after={str(path.resolve()):sha(path) for path in paths}
            report['guarded_files_unchanged']=before==after
        except OSError as error:
            after={};report['guarded_files_unchanged']=False;report['guard_error']=type(error).__name__
        report['guarded_file_count']=len(paths)
        report['guarded_existing_file_count']=sum(value is not None for value in before.values())
        (session/'preservation.json').write_text(json.dumps(dict(before=before,after=after),indent=2)+'\n')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+'\n')
    if len(report['results'])!=2 or not all(item['passed'] for item in report['results']):
        raise SystemExit('Loading benchmark failed; see exact scoped report')
    if not report['input_desktop_unchanged'] or not report['guarded_files_unchanged'] or not all(p['still_alive'] for p in report['protected_processes']):
        raise SystemExit('Preservation guard changed; no automatic restoration attempted')


if __name__=='__main__':main()
