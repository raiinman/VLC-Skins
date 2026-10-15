"""Compare every startup frame with the keyed WMP source before enlargement."""
from PIL import Image, ImageSequence
from assets import ThemeAssets
from build import SKIN, SOURCE


def source_pixels(image):
    image=image.convert('RGBA')
    pixels=image.load()
    for y in range(image.height):
        for x in range(image.width):
            r,g,b,a=pixels[x,y]
            if (r,g,b)==(255,0,255):pixels[x,y]=(r,g,b,0)
    return image


with Image.open(SOURCE/'intro_anim.gif') as gif:
    assert gif.n_frames==59
    frames=[]
    for frame in ImageSequence.Iterator(gif):
        assert frame.info['duration']==100
        frames.append(source_pixels(frame))
static=source_pixels(Image.open(SOURCE/'intro_static.png'))
light=source_pixels(Image.open(SOURCE/'shutter_light.png'))

for scale in (1,2):
    assets=ThemeAssets(SKIN/f'vlc-{scale}x')
    for key,source in (('intro_sequence',static),('intro_light_sequence',light)):
        resource=assets.resources[key]
        assert (resource.get('nbframes'),resource.get('fps'),resource.get('loop'))==('81','10','1')
        for index in range(81):
            expected=source.copy()
            if key=='intro_sequence' and index>=15:
                expected=frames[min(index-15,58)].copy()
            end=8 if key=='intro_sequence' else 7
            alpha=max(0,min(1,(end-index/10)/.5))
            expected.putalpha(expected.getchannel('A').point(lambda a:round(a*alpha)))
            if index==80:expected=Image.new('RGBA',expected.size)
            if scale==2:
                expected=expected.resize((expected.width*2,expected.height*2),Image.Resampling.LANCZOS)
            actual=assets.frame(key,index)
            assert actual.tobytes()==expected.tobytes(),(scale,key,index,'source startup pixels differ')
    print(f'PASS {scale}x: all 162 intro/light frames match keyed source and fade timing')
