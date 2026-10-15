"""Measure real Windows VLC theme initialization, independently of playback."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import time
import wave
from build import ROOT


def measure(vlc,scale,budget):
    folder=ROOT.parent/'work'/f'load-{scale}x-{time.time_ns()}'
    folder.mkdir(parents=True);config=folder/'vlcrc.ini';config.write_text('')
    log=folder/'vlc.log';skin=ROOT/f'dist/Need-for-Speed-Underground-{scale}x.vlt'
    clip=folder/'silence.wav'
    with wave.open(str(clip),'wb') as sound:
        sound.setparams((1,2,8000,0,'NONE','not compressed'))
        sound.writeframes(bytes(8000*2*60))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    args=[str(vlc),'--no-one-instance','--no-media-library',f'--config={config}',
          '--intf=skins2',f'--skins2-last={skin}','--skins2-config=',
          '--no-qt-privacy-ask','--no-metadata-network-access','--extraintf=rc',
          f'--rc-host=127.0.0.1:{port}','--rc-quiet','--verbose=2',
          '--file-logging',f'--logfile={log}',str(clip)]
    start=time.monotonic();process=subprocess.Popen(args)
    try:
        while time.monotonic()-start<budget:
            # CLI autoplay starts after the primary skins2 interface is ready.
            # RC itself starts earlier, and Windows buffers the log file.
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.2) as sock:
                    sock.settimeout(.2);sock.sendall(b'is_playing\n');reply=b''
                    while True:
                        chunk=sock.recv(4096)
                        if not chunk:break
                        reply+=chunk
                        if re.search(rb'(?:^|\n)1\r?\n',reply):break
                    if re.search(rb'(?:^|\n)1\r?\n',reply):break
            except OSError:pass
            assert process.poll() is None,f'{scale}x VLC exited during initialization'
            time.sleep(.1)
        else:raise AssertionError(f'{scale}x exceeded {budget}s initialization budget')
        elapsed=round(time.monotonic()-start,2)
        # Let the complete source-timed startup sequence run before shutdown.
        time.sleep(8.5)
        assert process.poll() is None,f'{scale}x exited during startup animation'
    finally:
        try:
            with socket.create_connection(('127.0.0.1',port),timeout=2) as sock:
                sock.sendall(b'quit\n')
            process.wait(timeout=10)
        except (OSError,subprocess.TimeoutExpired):
            process.terminate();process.wait(timeout=10)
    text=log.read_text(errors='replace')
    assert 'loading theme configuration' in text,'Theme never initialized'
    errors=[line for line in text.splitlines() if re.search(
        r'skins2 error:|unknown (action|variable)|AlphaBlend\(\) failed|pure virtual',line,re.I)]
    assert not errors,errors
    return dict(scale=scale,autoplay_after_interface_ready_seconds=elapsed,
                process_alive_after_animation=True,theme_errors=errors,
                sha256=hashlib.sha256(skin.read_bytes()).hexdigest())


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--vlc',type=Path,default=Path('C:/Program Files/VideoLAN/VLC/vlc.exe'))
    parser.add_argument('--max-seconds',type=float,default=30)
    args=parser.parse_args();results=[]
    for scale in (1,2):
        result=measure(args.vlc,scale,args.max_seconds);results.append(result)
        print(json.dumps(result),flush=True)
    (ROOT/'docs/load-benchmark.json').write_text(json.dumps(results,indent=2)+'\n')
