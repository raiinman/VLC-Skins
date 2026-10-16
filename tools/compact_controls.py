"""Small native Skins2 controls, kept at physical 1x size in both themes."""
from pathlib import Path
from lxml import etree as E
from PIL import Image, ImageChops, ImageDraw

SOURCE = Path(__file__).resolve().parents[1] / 'skins/need-for-speed-underground/original'


def original(name):
    image = Image.open(SOURCE/name).convert('RGBA')
    channels = ImageChops.difference(image.convert('RGB'), Image.new('RGB', image.size, '#FF00FF')).split()
    mask = ImageChops.lighter(ImageChops.lighter(*channels[:2]), channels[2]).point(lambda n: 255 if n else 0)
    image.putalpha(ImageChops.multiply(image.getchannel('A'), mask))
    return image


def carbon():
    """Flat smoked charcoal; retain the resource name for bundle compatibility."""
    image = Image.new('RGBA', (360,64), (13,17,21,255))
    mask = Image.new('L', image.size)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,359,63), radius=10, fill=255)
    image.putalpha(mask)
    ImageDraw.Draw(image).rounded_rectangle((0,0,359,63), radius=10, outline=(59,72,80,255))
    return image


def volume_icon(state):
    from hud_button_art import button_icon
    return button_icon('speaker',state,23)


def add_controllers(builder):
    # Dedicated aliases prevent a 2x main resource from inflating this HUD.
    def bitmap(name, image):
        return builder.bitmap(name,image,prescaled=True)
    def source(name):
        return bitmap('compact_'+name, original(name))
    background = bitmap('compact_carbon',carbon())
    rail = Image.new('RGBA',(1,3)); rail.putdata([(35,114,142,255),(9,22,29,255),(52,76,86,255)])
    rail = bitmap('compact_rail',rail)
    E.SubElement(builder.theme,'Font',id='compactfont',file='assets/FreeSans.ttf',size='11')
    for window_id, layout_id in [('fullscreenController','fullscreen_controls'),('videoHoverController','video_hover_controls')]:
        companion = window_id == 'videoHoverController'
        window = E.SubElement(builder.theme,'Window',id=window_id,x='-31000' if companion else '0',
                              y='-30800' if companion else '0',visible='true' if companion else 'false',dragdrop='false',playondrop='false')
        layout = E.SubElement(window,'Layout',id=layout_id,width='361' if companion else '360',height='64',
                              minwidth='361' if companion else '360',maxwidth='361' if companion else '360',minheight='64',maxheight='64')
        E.SubElement(layout,'Image',image=background,x='0',y='0',action='none' if companion else 'move')
        gate = layout_id+'.isActive' if companion else window_id+'.isVisible'
        expanded = gate+' and hover_volume_expanded.isActive'
        collapsed = gate+' and not hover_volume_expanded.isActive'
        def button(prefix,x,y,action,tip):
            return E.SubElement(layout,'Button',x=str(x),y=str(y),
                up=source(prefix+'_no.png'),over=source(prefix+'_hov.png'),down=source(prefix+'_do.png'),action=action,tooltiptext=tip)
        def label(text,x,y,width,visible=gate):
            return E.SubElement(layout,'Text',text=text,x=str(x),y=str(y),width=str(width),font='compactfont',
                                color='#FFFFFF',alignment='center',scrolling='none',focus='false',visible=visible)
        def slider(value,x,y,length,visible):
            E.SubElement(layout,'Image',image=rail,x=str(x),y=str(y-2),width=str(length),height='3',resize='scale',visible=visible)
            E.SubElement(layout,'Slider',id=layout_id+'_'+value,x=str(x),y=str(y),
                         up=source('eq_thumb2.png'),down=source('eq_thumb2_do.png'),
                         points=f'(0,0),({length},0)',thickness='8',value=value,visible=visible,
                         tooltiptext='Seek: $T / $D' if value=='time' else 'Volume: $V%')
        slider('time',12,12,336,'true')
        button('m_prev',8,27,'playlist.previous()','Previous track')
        play = dict(x='42',y='27',state='vlc.isPlaying',action1='vlc.play()',action2='vlc.pause()',tooltiptext1='Play',tooltiptext2='Pause')
        for state,prefix in [('1','m_play'),('2','m_pause')]:
            for attr,suffix in [('up','no'),('over','hov'),('down','do')]:play[attr+state]=source(prefix+'_'+suffix+'.png')
        E.SubElement(layout,'Checkbox',**play)
        button('m_stop',76,27,'vlc.stop()','Stop')
        button('m_next',110,27,'playlist.next()','Next track')
        label('$t / $d',148,33,80)
        volume = dict(x='232',y='31',state='hover_volume_expanded.isActive',
                      action1='hover_volume_state.setLayout(hover_volume_expanded)',
                      action2='hover_volume_state.setLayout(hover_volume_collapsed)',
                      tooltiptext1='Volume: hover or click to expand',tooltiptext2='Volume: click to collapse')
        for state in ('1','2'):
            for attr,suffix in [('up','no'),('over','hov'),('down','do')]:
                volume[attr+state] = bitmap('compact_volume_'+suffix+'.png',volume_icon(suffix))
        E.SubElement(layout,'Checkbox',**volume)
        label('$V%',259,34,46,collapsed)
        slider('volume',264,43,40,expanded)
        button('vid_zoom',312,33,'vlc.fullscreen()','Enter / leave borderless fullscreen')
        button('m_close',334,33,'videoHoverController.setLayout(video_hover_closed)' if companion else window_id+'.hide()','Hide playback controls')
        if companion:
            closed = E.SubElement(window,'Layout',id='video_hover_closed',width='362',height='1')
            marker = bitmap('hover_closed_marker',Image.new('RGBA',(1,1)))
            E.SubElement(closed,'Image',image=marker,x='0',y='0',width='1',height='1')
    state = E.SubElement(builder.theme,'Window',id='hover_volume_state',x='-31000',y='-30700',
                         visible='true',dragdrop='false',playondrop='false')
    marker = bitmap('hover_closed_marker',Image.new('RGBA',(1,1)))
    for suffix,width in [('expanded',72),('collapsed',71)]:
        layout = E.SubElement(state,'Layout',id='hover_volume_'+suffix,width=str(width),height='19')
        E.SubElement(layout,'Image',image=marker,x='0',y='0',width='1',height='1')
