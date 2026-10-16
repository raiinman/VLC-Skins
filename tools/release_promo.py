"""Product-first 1x release film. Offline edit only; no desktop/runtime access.

Manifest shape: {"clips": {name: {"frame_directory": absolute_path,
"fps": 30, "start": 0, "privacy_reviewed": true, "provenance": "..."}}}.
Required names: details, browse, playback, quality, fullscreen. Optional crop is
[left, top, right, bottom]. Recordings must cover the selected edit interval.
"""
import argparse
from bisect import bisect_right
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

from assets import ThemeAssets
from promo_1x import skin_frame

ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / 'skins/need-for-speed-underground'
W, H, FPS, DURATION = 1920, 1080, 60, 54
FONT = 'C:/Windows/Fonts/bahnschrift.ttf'
BLUE = '#57cff2'
CUTS = [0, 1.25, 2.5, 3, 11.1, 11.65, 12.7, 13.25, 16.05, 20, 28, 36, 40, 46, 50, 54]


@lru_cache(maxsize=64)
def font(size):
    return ImageFont.truetype(FONT, size)


def text(image, xy, message, size=28, color='white'):
    ImageDraw.Draw(image).text(xy, message, font=font(size), fill=color)


def display(image, xy, message, size=48, color='white'):
    """Original racing-ad typography, separate from the unmodified product UI."""
    face = ImageFont.truetype('C:/Windows/Fonts/ariblk.ttf',size)
    box = face.getbbox(message)
    layer = Image.new('RGBA',(box[2]+size,round(size*1.5)))
    ImageDraw.Draw(layer).text((size*.25,-box[1]),message,font=face,fill=color)
    layer = layer.transform(layer.size,Image.Transform.AFFINE,(1,.20,-size*.20,0,1,0),Image.Resampling.BICUBIC)
    image.alpha_composite(layer,xy)


def backdrop():
    yy, xx = np.mgrid[:H, :W]
    glow = np.exp(-(((xx-W*.5)/(W*.55))**2 + ((yy-H*.45)/(H*.62))**2))
    rng = np.random.default_rng(2007)
    noise = rng.normal(0,1,(H,W))
    streak = np.cumsum(noise,axis=1)
    streak[:,24:] -= streak[:,:-24].copy()
    brushed = streak/24*3 + noise*.30
    metal = 13+glow*8+brushed
    rgb = np.stack([metal,metal+2+glow*2,metal+5+glow*4],axis=2).clip(0,255).astype('uint8')
    image = Image.fromarray(rgb).convert('RGBA')
    grille = Image.new('RGBA',(W,H),'#10151a')
    d = ImageDraw.Draw(grille)
    for y in range(-10,H+20,24):
        for x in range(-10+(12 if y//24%2 else 0),W+20,24):
            d.ellipse((x-7,y-7,x+7,y+7),fill='#030507',outline='#34414b',width=1)
    mask = Image.new('L',(W,H))
    md = ImageDraw.Draw(mask)
    md.polygon([(0,0),(1270,0),(0,180)],fill=255)
    md.polygon([(W,H),(W,800),(400,H)],fill=255)
    image.paste(grille,(0,0),mask)
    d = ImageDraw.Draw(image)
    for offset,color,width in [(0,'#06090c',10),(1,'#657582',2),(5,'#142b3a',2)]:
        d.line([(0,180+offset),(1270,offset)],fill=color,width=width)
        d.line([(400,H+offset),(W,800+offset)],fill=color,width=width)
    light = Image.new('RGBA',(W,H))
    ld = ImageDraw.Draw(light)
    rail = [(-100,1030),(980,835),(1990,585)]
    ld.line(rail,fill=(0,151,255,120),width=12)
    image.alpha_composite(light.filter(ImageFilter.GaussianBlur(22)))
    ld = ImageDraw.Draw(image)
    ld.line(rail,fill='#075b85',width=5)
    ld.line(rail,fill='#82dfff',width=1)
    for x,y in [(32,35),(W-34,H-35)]:
        ld.ellipse((x-15,y-15,x+15,y+15),fill='#080b0e',outline='#56616b',width=2)
        ld.ellipse((x-10,y-11,x+9,y+8),fill='#293039')
        ld.line((x-5,y-5,x+5,y+5),fill='#020406',width=3)
    ld.rectangle((0,991,W,H),fill=(7,11,15,245))
    return image


def contain(image, rect):
    x, y, width, height = rect
    image = ImageOps.contain(image, (int(width), int(height)), Image.Resampling.LANCZOS)
    return image, (round(x+(width-image.width)/2), round(y+(height-image.height)/2))


def place(canvas, image, rect, shadow=False):
    image, xy = contain(image, rect)
    if shadow:
        shade = Image.new('RGBA', canvas.size)
        shade.paste((0, 0, 0, 130), (xy[0]+12, xy[1]+20, xy[0]+image.width+12, xy[1]+image.height+20))
        canvas.alpha_composite(shade.filter(ImageFilter.GaussianBlur(22)))
    canvas.alpha_composite(image, xy)


class Clip:
    def __init__(self, spec, seconds, cache):
        if spec.get('privacy_reviewed') is not True or not spec.get('provenance'):
            raise ValueError('Each capture must have explicit privacy review and provenance')
        self.spec = spec
        self.fps = float(spec['fps'])
        self.start = float(spec.get('start', 0))
        if not 1 <= self.fps <= 120 or self.start < 0:
            raise ValueError('Invalid capture cadence/start')
        if spec.get('frame_directory'):
            directory = Path(spec['frame_directory']).resolve()
        else:
            source = Path(spec['path']).resolve()
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            directory = cache/source_hash
            complete = directory/'decode-complete'
            if not complete.exists():
                directory.mkdir(parents=True,exist_ok=True)
                subprocess.run(['ffmpeg','-y','-v','error','-i',str(source),'-fps_mode','passthrough',str(directory/'%06d.png')],check=True)
                complete.write_text(source_hash,encoding='ascii')
        self.files = sorted(directory.glob('*.png'))
        self.timestamps = spec.get('timestamps')
        if self.timestamps is not None:
            if len(self.timestamps)!=len(self.files) or not all(b>a for a,b in zip(self.timestamps,self.timestamps[1:])):
                raise ValueError('Timestamp/frame order mismatch')
            self.duration = float(self.timestamps[-1])+1/self.fps-self.start
        else:
            self.duration = len(self.files)/self.fps-self.start
        if self.duration + .035 < seconds:
            raise ValueError(f'Capture too short: {directory}, {self.duration:.2f}s needs {seconds}s')
        digest = hashlib.sha256()
        for path in self.files:
            digest.update(path.name.encode('utf-8'))
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        self.spec = {**spec, 'frame_count':len(self.files), 'sequence_sha256':digest.hexdigest()}
        self.previous = None
        self.image = None

    def frame(self, elapsed):
        index = max(0,bisect_right(self.timestamps,self.start+elapsed)-1) if self.timestamps is not None else min(len(self.files)-1, int((self.start+elapsed)*self.fps))
        if index != self.previous:
            with Image.open(self.files[index]) as image:
                self.image = image.convert('RGBA')
            if self.spec.get('crop'):
                self.image = self.image.crop(tuple(self.spec['crop']))
            self.previous = index
        return self.image


def make_audio(output, duration=DURATION):
    """Original 138 BPM broken rhythm, no external music or artist imitation."""
    rate = 48000
    n = rate*duration
    t = np.arange(n)/rate
    music = np.zeros((n, 2), dtype=np.float64)
    rng = np.random.default_rng(2007)
    beat = 60/138

    def add(at, data, gain, pan=0):
        first = int(at*rate)
        if first < 0 or first >= n:
            return
        count = min(len(data), n-first)
        music[first:first+count, 0] += data[:count]*gain*math.sqrt((1-pan)/2)
        music[first:first+count, 1] += data[:count]*gain*math.sqrt((1+pan)/2)

    for bar in np.arange(0, duration, beat*4):
        for pos in [0, 1.75, 2.5, 3.5]:
            u = np.arange(int(rate*.25))/rate
            kick = np.sin(2*np.pi*(48*u+4.5*(1-np.exp(-u*33))))*np.exp(-u*23)
            add(bar+beat*pos, kick, .19)
        for pos in [1, 3]:
            u = np.arange(int(rate*.17))/rate
            noise = rng.normal(0, 1, len(u))
            body = np.sin(2*np.pi*177*u)*np.exp(-u*35)
            add(bar+beat*pos, (noise*.33+body*.5)*np.exp(-u*28), .15)
        for i in range(8):
            u = np.arange(int(rate*.045))/rate
            noise = rng.normal(0, 1, len(u))
            noise[1:] -= noise[:-1].copy()*.93
            add(bar+beat*(i*.5+(.045 if i%2 else 0)), noise*np.exp(-u*105), .024 if i%2 else .032, (-.45 if i%2 else .45))
        for i, midi in enumerate([28, 28, 31, 26, 28, 35, 31, 26]):
            u = np.arange(int(rate*.17))/rate
            frequency = 440*2**((midi-69)/12)
            wavelet = np.sin(2*np.pi*frequency*u)+.20*np.sin(4*np.pi*frequency*u)
            add(bar+beat*i*.5, np.tanh(wavelet*1.7)*np.minimum(u*100, 1)*np.exp(-u*10), .085, .08)
    envelope = np.minimum(t/1.0, 1)*np.minimum((duration-t)/1.5, 1)
    envelope[(t >= 2.7) & (t < 11.1)] *= .12
    envelope[(t >= 46) & (t < 50)] *= .55
    music *= envelope[:, None]
    # Full original cue and two shutter operations, source timing preserved.
    for name, at, gain in [('intro4.wav', 4.5, .48), ('shutter.wav', 11.1, .36), ('shutter.wav', 12.7, .36)]:
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(SKIN/'original'/name), '-f', 'f32le', '-ac', '2', '-ar', str(rate), '-'])
        sample = np.frombuffer(raw, '<f4').reshape(-1, 2)
        start = int(at*rate)
        count = min(len(sample), n-start)
        music[start:start+count] += sample[:count]*gain
    # Conservative soft limit, leaving AAC reconstruction headroom.
    music = np.tanh(music*1.1)*.78
    music *= .70/max(float(np.max(np.abs(music))),1e-9)
    with wave.open(str(output), 'wb') as stream:
        stream.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
        stream.writeframes((music*32767).astype('<i2').tobytes())
    return {'sample_rate': rate, 'peak_dbfs': float(20*np.log10(np.max(np.abs(music)))), 'listening_performed': False}


def render(output, manifest, preview=False, omit_fullscreen=False):
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Generated media must be outside Git')
    output.mkdir(parents=True, exist_ok=True)
    captures = json.loads(manifest.read_text(encoding='utf-8-sig'))
    duration = 48 if omit_fullscreen else DURATION
    native_end = 40 if omit_fullscreen else 46
    cuts = [t for t in CUTS if t <= 40]+[44,48] if omit_fullscreen else CUTS
    required = {'details':3.95, 'browse':8, 'playback':8, 'quality':4}
    if not omit_fullscreen:
        required['fullscreen'] = 6
    if not preview:
        for key in required:
            if captures['clips'][key].get('actionsVerified') is not True:
                raise ValueError('Final edit requires observed action verification: '+key)
    clips = {key:Clip(captures['clips'][key], duration, output/'decoded-sources') for key,duration in required.items()}
    assets = ThemeAssets(SKIN/'vlc-1x')
    stills = {p:skin_frame(assets, f'main_{p}') for p in range(1, 8)}
    bg = backdrop()
    audio = make_audio(output/'release-soundtrack.wav',duration)
    encoded = output/'NFS-Underground-VLC-1x-Release.mp4'
    ffmpeg = None if preview else subprocess.Popen(['ffmpeg', '-y', '-v', 'warning', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', str(output/'release-soundtrack.wav'), '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-t', str(duration), str(encoded)], stdin=subprocess.PIPE)
    review = set([0, 36, 90, 150, 180, 210, 270, 390, 540, 660, 665, 698, 731, 770, 850, 950, 970, 1100, 1250, 1500, 1680, 1850, 2140, 2200, 2380, 2450, 2600, 2760, 2940, 3000, 3100, 3230])
    review.update([native_end*FPS+90,(native_end+4)*FPS+60,duration*FPS-10])
    review = {number for number in review if number < FPS*duration}
    frame_numbers = sorted(review) if preview else range(FPS*duration)
    intro_cache = {}
    for frame in frame_numbers:
        t = frame/FPS
        image = bg.copy()
        if t < 3:
            # Actual carbon, bevel and blue-gauge details, photographed by editorial crop.
            if t < 1.25:
                crop = stills[1].crop((56, 42, 238, 155))
                drift = (t/1.25)*22
                place(image, crop, (340-drift, 110, 1240+drift*2, 770))
                display(image, (100, 938), 'YOUR DESKTOP. 2007.', 42)
            elif t < 2.5:
                crop = stills[1].crop((176, 157, 288, 282))
                place(image, crop, (575, 80, 770, 865))
            else:
                place(image, stills[1], (540, 100, 840, 840))
        elif t < 11.1:
            index = min(80, (frame-180)//6)
            if index not in intro_cache:
                intro_cache[index] = skin_frame(assets, 'main_start', index/10)
            place(image, intro_cache[index], (510, 78, 900, 900))
            text(image, (80, 1000), 'ORIGINAL STARTUP.', 22, '#a3b1b9')
        elif t < 13.25:
            if t < 11.65:
                player = skin_frame(assets, 'main_1_closing', (frame-666)/FPS)
            elif t < 12.7:
                player = skin_frame(assets, 'main_1_closed')
            else:
                player = skin_frame(assets, 'main_1_opening', (frame-762)/FPS)
            place(image, player, (510, 78, 900, 900))
        elif t < 16.05:
            p = min(7, (frame-795)//24+1)
            place(image, stills[p], (510, 78, 900, 900))
            text(image, (80, 1000), 'SEVEN ORIGINAL COLOURS.', 22, '#a3b1b9')
        elif t < native_end:
            key, start = ('details', 16.05) if t < 20 else ('browse',20) if t < 28 else ('playback',28) if t < 36 else ('quality',36) if t < 40 else ('fullscreen',40)
            capture = clips[key].frame(t-start)
            if key == 'details' and capture.size == stills[1].size:
                capture = capture.copy()
                capture.putalpha(stills[1].getchannel('A'))
            place(image, capture, (42, 40, 1836, 960))
            label = {'details':'PLAYLIST / EQ / ORIGINAL DETAILS', 'browse':'YOUTUBE. IN YOUR PLAYER.', 'playback':'REAL 4K PLAYBACK.', 'quality':'2160p60. NATIVE VLC VIDEO.', 'fullscreen':'FRAMED. OR FULLSCREEN.'}[key]
            label = clips[key].spec.get('label',label)
            text(image, (62, 1014), label, 23)
            if key != 'details':
                text(image, (1310, 1014), 'OPTIONAL COMPANION', 20, '#a3b1b9')
        elif t < native_end+4:
            place(image, stills[1], (70, 100, 850, 850))
            display(image, (1010, 260), 'NFS UNDERGROUND', 47)
            display(image, (1010, 335), 'FOR VLC.', 82, BLUE)
            text(image, (1015, 465), 'ONE .VLT. NO COMPILING.', 29)
            text(image, (1015, 520), 'YouTube + extras: optional companion.', 24, '#b8c2c8')
            text(image, (1015, 655), 'github.com/raiinman/VLC-Skins', 25)
        else:
            place(image, stills[1], (1250, 250, 500, 500))
            display(image, (140, 270), 'BACK IN THE DRIVER\'S SEAT.', 46)
            text(image, (144, 395), 'Original skin  /  The Skins Factory', 27, '#b8c2c8')
            text(image, (144, 445), 'VLC conversion  /  Dead Signal Interactive', 27, '#b8c2c8')
            text(image, (144, 565), 'Big Buck Bunny  /  CC BY 3.0', 23, '#a1b0b9')
            text(image, (144, 605), '(c) 2008 Blender Foundation / www.bigbuckbunny.org', 23, '#a1b0b9')
            text(image, (144, 670), 'Built with AI assistance.', 22, '#a1b0b9')
            text(image, (144, 730), '1x RELEASE', 26, BLUE)
        if 20 <= t < native_end:
            text(image, (60, 8), 'Demo film: (c) 2008 Blender Foundation / www.bigbuckbunny.org · CC BY 3.0', 15, '#8296a2')
        if 3 <= t < 13.25:
            text(image, (1390, 1000), 'SOUND: OPTIONAL COMPANION', 18, '#a3b1b9')
        if frame in review:
            image.convert('RGB').save(output/f'review-{frame:04d}.jpg', quality=96)
        if ffmpeg:
            ffmpeg.stdin.write(image.convert('RGB').tobytes())
        if frame % 300 == 0:
            print(f'Render frame {frame}/{FPS*duration}', flush=True)
    if ffmpeg:
        ffmpeg.stdin.close()
        if ffmpeg.wait():
            raise RuntimeError('FFmpeg export failed')
    edl = {'duration':duration, 'fps':FPS, 'dimensions':[W,H], 'cuts':cuts, 'intro':{'start':3,'end':11.1,'frames':81,'source_fps':10,'output_holds':6,'sound_start':4.5,'type':'source-exact asset composition, not native screen capture'}, 'ordered_shots':[{'start':0,'end':3,'source':'original artwork macro crops','type':'asset editorial enlargement'}, {'start':3,'end':11.1,'source':'all81main_start sourceframes','type':'asset animation'}, {'start':11.1,'end':13.25,'source':'original shutter closing/closed/opening layouts','sound_cues':[11.1,12.7],'type':'asset animation'}, {'start':13.25,'end':16.05,'source':'seven original palettes, 0.4s each','type':'asset montage'}, *[{'start':start,'end':end,'source':key,'type':'actual native capture'} for key,start,end in [('details',16.05,20),('browse',20,28),('playback',28,36),('quality',36,40),('fullscreen',40,46)] if key in clips], {'start':native_end,'end':duration,'source':'original main artwork and authored release/credit typography','type':'editorial end card'}], 'clips':{k:c.spec for k,c in clips.items()}, 'audio':audio, 'output':str(encoded), 'preview_only':preview}
    (output/'edit-decisions.json').write_text(json.dumps(edl,indent=2),encoding='utf-8')
    (output/'credits.txt').write_text('Original skin: The Skins Factory\nVLC conversion: Dead Signal Interactive\nBuilt with AI assistance.\nBig Buck Bunny: (c) 2008 Blender Foundation / www.bigbuckbunny.org, CC BY 3.0\nFilm source: https://peach.blender.org/about/\nFilm license: https://creativecommons.org/licenses/by/3.0/\nChanges: short excerpts displayed in native VLC, editorial framing/scaling; original film audio omitted.\nMusic: original synthesized production for this release film.\nYouTube, skin sounds and framed hover require the optional companion.\n',encoding='utf-8')
    return encoded


def audit(movie):
    """Decode the whole movie and measure every encoded frame, not spot samples."""
    probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(movie)]))
    video = next(s for s in probe['streams'] if s['codec_type']=='video')
    sound = next(s for s in probe['streams'] if s['codec_type']=='audio')
    duration = round(float(probe['format']['duration']))
    if duration not in (48,54):
        raise ValueError('Unexpected film duration')
    if (video['width'],video['height'],video['codec_name'],video['r_frame_rate']) != (W,H,'h264','60/1'):
        raise ValueError('Unexpected video encoding')
    if sound['codec_name']!='aac' or int(sound['sample_rate'])!=48000:
        raise ValueError('Unexpected sound encoding')
    process = subprocess.Popen(['ffmpeg','-v','error','-i',str(movie),'-vf','scale=96:54:flags=area,format=gray','-f','rawvideo','-pix_fmt','gray','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    previous = None
    frame_count = 0
    black = []
    differences = []
    frozen_runs = []
    freeze_start = 0
    while True:
        raw = process.stdout.read(96*54)
        if not raw:
            break
        if len(raw)!=96*54:
            raise ValueError('Truncated decoded frame')
        pixels = np.frombuffer(raw,np.uint8).astype(np.int16)
        if float(np.mean(pixels)) < 10 and float(np.mean(pixels<12)) > .995:
            black.append(frame_count)
        difference = float(np.mean(np.abs(pixels-previous))) if previous is not None else 999
        differences.append(difference)
        if difference >= .12:
            if frame_count-freeze_start > FPS:
                frozen_runs.append([freeze_start/FPS,frame_count/FPS])
            freeze_start = frame_count
        previous = pixels
        frame_count += 1
    if frame_count-freeze_start > FPS:
        frozen_runs.append([freeze_start/FPS,frame_count/FPS])
    errors = process.stderr.read().decode('utf-8','replace')
    if process.wait() or errors.strip():
        raise ValueError('Decode errors: '+errors[:500])
    if frame_count != FPS*duration or black:
        raise ValueError(f'Frame audit failed: {frame_count} frames, black indices {black[:20]}')
    # Continuous video is required here; source intro/palette and editorial holds
    # are deliberately excluded from this motion gate.
    failed_motion = [r for r in frozen_runs if max(r[0],28)<min(r[1],36) and min(r[1],36)-max(r[0],28)>1.5]
    if failed_motion:
        raise ValueError('Unexpected frozen native playback: '+str(failed_motion))
    loudness = subprocess.run(['ffmpeg','-hide_banner','-i',str(movie),'-af','volumedetect','-vn','-sn','-f','null','-'],capture_output=True,text=True,check=True).stderr
    report = {'passed':True,'decoded_frames':frame_count,'dimensions':[W,H],'fps':FPS,'duration':float(probe['format']['duration']),'black_frames':black,'low_motion_intervals':frozen_runs,'low_motion_note':'Boot frames repeat six times exactly; fixed macro artwork, menu and release cards deliberately hold. Only native playback is required to move continuously.','motion_mean':float(np.mean(differences[28*FPS:36*FPS])),'full_decode_errors':False,'audio_measurements':[line.strip() for line in loudness.splitlines() if 'mean_volume:' in line or 'max_volume:' in line],'audio_listening_performed':False,'sha256':hashlib.sha256(movie.read_bytes()).hexdigest()}
    edl = json.loads((movie.parent/'edit-decisions.json').read_text(encoding='utf-8'))
    cut_frames = sorted({max(0,min(frame_count-1,round(t*FPS)+offset)) for t in edl['cuts'] for offset in [-1,0,1]})
    expression = '+'.join(f'eq(n\\,{number})' for number in cut_frames)
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(movie),'-vf',f'select={expression}','-fps_mode','vfr','-q:v','2',str(movie.parent/'encoded-cut-%03d.jpg')],check=True)
    report['encoded_cut_frame_map'] = cut_frames
    (movie.parent/'encoded-frame-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    paths = sorted(movie.parent.glob('review-*.jpg'))
    sheet = Image.new('RGB',(1280,math.ceil(len(paths)/4)*205),'#080c10')
    for i,path in enumerate(paths):
        with Image.open(path) as image:
            image.thumbnail((320,180))
            sheet.paste(image,((i%4)*320,(i//4)*205))
        ImageDraw.Draw(sheet).text(((i%4)*320+8,(i//4)*205+182),path.stem,font=font(14),fill='white')
    sheet.save(movie.parent/'release-contact-sheet.jpg',quality=93)
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    parser.add_argument('--captures',type=Path)
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--audit',type=Path)
    parser.add_argument('--omit-fullscreen',action='store_true',help='Explicit 48s edit, omitting an unverified fullscreen demonstration')
    args = parser.parse_args()
    if args.audit:
        audit(args.audit)
    else:
        if args.output is None or args.captures is None:
            parser.error('--output and --captures are required for editing')
        print(render(args.output,args.captures,args.preview,args.omit_fullscreen))
