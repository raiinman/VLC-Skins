"""Local 1x promo composition. Never launches VLC or accesses browser profiles.

Capture manifest: JSON list of exactly three {path, caption, provenance} entries.
Images must already be privacy reviewed and redacted. Outputs stay outside Git.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from assets import ThemeAssets, visible

ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / 'skins/need-for-speed-underground'
W, H, FPS, DURATION = 1280, 720, 30, 32
FONT = 'C:/Windows/Fonts/bahnschrift.ttf'


def font(size):
    return ImageFont.truetype(FONT, size)


def skin_frame(assets, layout_id, seconds=99):
    layout = assets.resources[layout_id]
    canvas = Image.new('RGBA', (int(layout.get('width')), int(layout.get('height'))))
    for node in layout:
        if not visible(node.get('visible'), active=layout_id, flags={'clock_elapsed_a.isActive': True}):
            continue
        if node.tag == 'Text' and node.get('text') == '$t':
            spec = assets.resources[node.get('font')]
            face = ImageFont.truetype(str(assets.directory/spec.get('file')), int(spec.get('size')))
            draw = ImageDraw.Draw(canvas)
            text = '00:00'
            x = int(node.get('x')) + (int(node.get('width'))-draw.textlength(text, font=face))/2
            draw.text((x, int(node.get('y'))), text, font=face, fill=node.get('color'))
            continue
        key = None
        if node.tag == 'Image':
            key = node.get('image')
        elif node.tag in ('Button', 'Checkbox'):
            key = node.get('up') or node.get('up1')
        elif node.tag == 'Slider':
            bg = node.find('SliderBackground')
            if bg is not None:
                image = assets.frame(bg.get('image'), int(bg.get('nbvert')) // 2, int(bg.get('nbvert')))
                canvas.alpha_composite(image, (int(node.get('x', 0)), int(node.get('y', 0))))
        if key is None:
            continue
        res = assets.resources[key]
        frames = int(res.get('nbframes', 1))
        animated = any(s in key for s in ('intro_', 'shutter_open', 'shutter_close'))
        index = min(frames - 1, int(seconds * float(res.get('fps', 10)))) if animated else frames - 1
        image = assets.frame(key, index)
        if node.get('width') and node.tag == 'Image':
            image = image.resize((int(node.get('width')), int(node.get('height', image.height))))
        canvas.alpha_composite(image, (int(node.get('x', 0)), int(node.get('y', 0))))
    return canvas


def background():
    yy, xx = np.mgrid[:H, :W]
    falloff = np.exp(-(((xx - 930) / 650) ** 2 + ((yy - 320) / 480) ** 2))
    rgb = np.zeros((H, W, 3), np.uint8)
    for c, (base, gain) in enumerate(((6, 10), (9, 18), (13, 24))):
        rgb[:, :, c] = base + falloff * gain
    im = Image.fromarray(rgb).convert('RGBA')
    d = ImageDraw.Draw(im)
    for x in range(-720, 1600, 48):
        d.line((x, H, x + 720, 0), fill=(25, 33, 40), width=1)
    d.polygon([(730, 720), (1060, 0), (1072, 0), (742, 720)], fill=(12, 75, 101))
    d.line((0, 681, 1280, 681), fill=(38, 76, 94), width=1)
    return im


def label(draw, xy, text, size=20, color='#b4c6cf'):
    draw.text(xy, text, font=font(size), fill=color)


def audio(output):
    """Original 120 BPM electronic backing, with source intro/shutter effects."""
    rate = 48000
    t = np.arange(rate * DURATION) / rate
    track = np.zeros(t.shape, np.float64)
    rng = np.random.default_rng(2007)
    for beat in np.arange(0, DURATION, .5):
        start = int(beat * rate)
        n = min(int(.32 * rate), len(track) - start)
        u = np.arange(n) / rate
        kick = np.sin(2 * np.pi * (43 * u + 5.8 * (1 - np.exp(-u * 25)))) * np.exp(-u * 19)
        track[start:start+n] += .22 * kick
    for beat in np.arange(.25, DURATION, .25):
        start = int(beat * rate)
        n = min(int(.065 * rate), len(track)-start)
        u = np.arange(n) / rate
        noise = rng.normal(0, 1, n)
        noise[1:] -= .9 * noise[:-1].copy()
        track[start:start+n] += .016 * noise * np.exp(-u * 70)
    notes = [41.203, 41.203, 48.999, 36.708, 41.203, 55, 48.999, 36.708]
    for i, beat in enumerate(np.arange(0, DURATION, .5)):
        start = int(beat * rate)
        n = min(int(.40 * rate), len(track)-start)
        u = np.arange(n) / rate
        f = notes[i % len(notes)]
        track[start:start+n] += .055 * (np.sin(2*np.pi*f*u) + .2*np.sin(4*np.pi*f*u)) * np.minimum(u*80, 1) * np.exp(-u*6)
    track *= np.minimum(t / .6, 1) * np.minimum((DURATION-t)/1.2, 1)
    # Duck the backing during the original boot cue.
    track[(t >= 2.0) & (t <= 8.8)] *= .30
    for filename, offset, gain in [('intro4.wav', 2.0, .65), ('shutter.wav', 9.2, .45), ('shutter.wav', 10.4, .45)]:
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(SKIN/'original'/filename), '-f', 'f32le', '-ac', '1', '-ar', str(rate), '-'])
        samples = np.frombuffer(raw, np.float32)
        start = int(offset * rate)
        n = min(len(samples), len(track)-start)
        track[start:start+n] += samples[:n] * gain
    peak = float(np.max(np.abs(track)))
    if peak > .89:
        track *= .89 / peak
    stereo = np.column_stack([track, track])
    with wave.open(str(output), 'wb') as stream:
        stream.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
        stream.writeframes((stereo * 32767).astype('<i2').tobytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--captures', type=Path, required=True)
    args = parser.parse_args()
    shots = json.loads(args.captures.read_text(encoding='utf-8-sig'))
    if len(shots) != 3 or not all(s.get('privacy_reviewed') is True for s in shots):
        raise ValueError('Exactly three privacy-reviewed native capture entries required')
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        raise ValueError('Generated media must stay outside the repository')
    out.mkdir(parents=True, exist_ok=True)
    capture_images = [Image.open(s['path']).convert('RGBA') for s in shots]
    native_frames = sorted(Path(shots[1]['frame_directory']).glob('*.png')) if shots[1].get('frame_directory') else []
    native_main = Image.open(shots[1]['main_path']).convert('RGBA') if shots[1].get('main_path') else None
    a = ThemeAssets(SKIN/'vlc-1x')
    bg = background()
    stills = {p: skin_frame(a, f'main_{p}') for p in range(1, 8)}
    if native_main is not None:
        if native_main.size != stills[1].size:
            raise ValueError('Native 1x main capture must match source geometry')
        native_main.putalpha(stills[1].getchannel('A'))
    cache = {}
    audio(out/'soundtrack.wav')
    process = subprocess.Popen(['ffmpeg', '-y', '-v', 'warning', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', str(out/'soundtrack.wav'), '-vf', 'scale=1920:1080:flags=lanczos', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', str(DURATION), str(out/'NFS-Underground-VLC-1x-Promo.mp4')], stdin=subprocess.PIPE)
    for frame in range(FPS*DURATION):
        t = frame/FPS
        image = bg.copy()
        d = ImageDraw.Draw(image)
        label(d, (64, 36), 'DEAD SIGNAL INTERACTIVE  /  VLC SKINS', 18, '#64d5fb')
        if t < 12:
            label(d, (64, 195), 'YOUR DESKTOP.', 48, '#ffffff')
            label(d, (64, 250), 'BACK IN 2007.', 58, '#ffffff')
            label(d, (66, 338), 'NEED FOR SPEED UNDERGROUND', 21, '#63d4f5')
            label(d, (66, 374), 'Original attitude. A new home in VLC.', 22)
            label(d, (66, 430), 'FULL INTRO  /  SHUTTERS  /  ORIGINAL SOUND', 16, '#89a0ad')
            if t < 8.6:
                key = ('intro', min(80, max(0, int((t-.5)*10))))
                if key not in cache:
                    cache[key] = skin_frame(a, 'main_start', key[1]/10)
                player = cache[key]
            elif t < 9.2:
                player = stills[1]
            elif t < 9.75:
                player = skin_frame(a, 'main_1_closing', t-9.2)
            elif t < 10.4:
                player = skin_frame(a, 'main_1_closed')
            elif t < 10.95:
                player = skin_frame(a, 'main_1_opening', t-10.4)
            else:
                player = stills[min(7, 1+int((t-10.95)*7))]
            player = player.resize((450, 447), Image.Resampling.LANCZOS)
            image.alpha_composite(player, (755, 125))
        elif t < 26:
            stage = 0 if t < 15 else 1 if t < 23 else 2
            label(d, (64, 87), shots[stage].get('heading', ['YOUTUBE. IN THE DRIVER\'S SEAT.', 'PICK A VIDEO. HIT PLAY.', 'QUALITY & CAPTIONS. RIGHT HERE.'][stage]), 35, '#ffffff')
            source = capture_images[stage]
            if stage == 1 and native_frames:
                index = min(len(native_frames)-1, int((t-15)*float(shots[1].get('capture_fps', 15))))
                with Image.open(native_frames[index]) as native:
                    source = native.convert('RGBA')
            source = ImageOps.contain(source, (1152, 480), Image.Resampling.LANCZOS)
            image.alpha_composite(source, ((W-source.width)//2, 145+(480-source.height)//2))
            d = ImageDraw.Draw(image)
            label(d, (64, 637), shots[stage]['caption'], 20, '#a8c5d1')
        else:
            label(d, (64, 175), 'THE SKIN YOU REMEMBER.', 45, '#ffffff')
            label(d, (64, 233), 'THE VIDEO YOU WATCH NOW.', 39, '#63d4f5')
            label(d, (66, 322), 'NFS UNDERGROUND  /  VLC  /  1x PREVIEW', 22)
            label(d, (66, 389), 'FOLLOW THE BUILD', 18, '#89a0ad')
            label(d, (66, 422), 'github.com/raiinman/VLC-Skins', 27, '#ffffff')
            label(d, (66, 505), 'VLC conversion: Dead Signal Interactive', 17)
            label(d, (66, 534), 'Original skin: The Skins Factory', 17)
            image.alpha_composite((native_main or stills[1]).resize((360, 358), Image.Resampling.LANCZOS), (865, 150))
        d = ImageDraw.Draw(image)
        label(d, (64, 695), '1x DEVELOPMENT PREVIEW', 12, '#77909d')
        if any(s.get('blender_credit') for s in shots) and 12 <= t < 26:
            label(d, (420, 695), '(c) 2008 Blender Foundation / www.bigbuckbunny.org  |  CC BY 3.0', 12, '#77909d')
        # Brief blue sweep accents, with clean hard cuts rather than glitch noise.
        if any(0 <= t-c < .16 for c in [12, 15, 23, 26]):
            progress = min((t-c) for c in [12, 15, 23, 26] if 0 <= t-c < .16)/.16
            x = int(progress*1500)-160
            d.polygon([(x,0),(x+130,0),(x-170,H),(x-300,H)], fill='#157b9b')
        if frame in [0, 90, 235, 282, 321, 355, 360, 365, 390, 445, 450, 455, 510, 660, 685, 690, 695, 775, 780, 785, 855, 945]:
            image.convert('RGB').save(out/f'frame-{frame:04d}.jpg', quality=95)
        process.stdin.write(image.convert('RGB').tobytes())
    process.stdin.close()
    if process.wait():
        raise RuntimeError('FFmpeg export failed')
    edl = [
        {'start':0,'end':12,'source':'exact 1x theme artwork and animation frames','purpose':'full original intro, shutter and palette montage','type':'offline asset composition'},
        *[{'start':bounds[0],'end':bounds[1],'source':s.get('frame_directory', s['path']),'purpose':s['caption'],'provenance':s['provenance'],'verified_native_resolution':s.get('verified_native_resolution'),'type':'native frame sequence' if s.get('frame_directory') else 'native capture held in motion-graphics edit'} for bounds,s in zip([(12,15),(15,23),(23,26)],shots)],
        {'start':26,'end':32,'source':'1x original artwork and authored typography','purpose':'project and credits end card','type':'offline composition'},
    ]
    (out/'edit-decisions.json').write_text(json.dumps(edl, indent=2), encoding='utf-8')
    print(out/'NFS-Underground-VLC-1x-Promo.mp4')


if __name__ == '__main__':
    main()
