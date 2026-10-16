"""Native Info transitions, isolated from main shutter and pane palette state."""
from copy import deepcopy
import json
import re

from lxml import etree as E
from PIL import Image, ImageChops


def share_backings(builder):
    """Share static page paint after IDs are assigned, without restarting fades.

    Each route is an exclusive layout of info_page_state. Native CtrlImage
    eagerly caches its bitmap even while hidden, so repeated static backings
    can share one control. Keep the first ID and every non-visibility attribute;
    animated decorations, navigation and the legacy layouts remain untouched.
    """
    hub = builder.theme.find('Window[@id="info"]/Layout[@id="info_menu"]')
    groups = {}
    route_gate = re.compile(r'info_state_\w+\.isActive')
    for node in hub:
        if (node.tag != 'Image'
                or not re.fullmatch(r'(?:c_back|c_sub_\d+_\d+)_jpg', node.get('image', ''))
                or (node.get('x'), node.get('y')) != (str(37*builder.scale), str(35*builder.scale))
                or any(node.get(a) not in (None, 'none') for a in ('action', 'action2'))):
            continue
        gates = node.get('visible', '').split(' or ')
        if not gates or not all(route_gate.fullmatch(gate) for gate in gates):
            continue
        key = tuple(sorted((k, v) for k, v in node.attrib.items() if k not in ('id', 'visible')))
        groups.setdefault(key, []).append(node)
    if not groups:
        return
    # Route content follows the shared frame prefix (including About, whose
    # carbon backing is deliberately outside this JPEG-only optimization).
    start = min(hub.index(node) for node in hub
                if route_gate.fullmatch(node.get('visible', ''))
                or any(node in nodes for nodes in groups.values()))
    shared = []
    for nodes in groups.values():
        first = nodes[0]
        gates = list(dict.fromkeys(gate for node in nodes for gate in node.get('visible').split(' or ')))
        first.set('visible', ' or '.join(gates))
        for node in nodes:
            hub.remove(node)
        shared.append(first)
    for offset, node in enumerate(shared):
        hub.insert(start+offset, node)


def augment(builder):
    from build import SOURCE, rgba
    b = builder
    window = b.theme.find('Window[@id="info"]')
    templates = {n.get('id').removeprefix('info_'): deepcopy(n) for n in window}
    hub = window.find('Layout[@id="info_menu"]')
    # Keep the old static layout IDs for saved-profile compatibility. Every
    # subsequent navigation enters this one live layout, so page changes do
    # not restart its independent frame-color animation.
    for node in list(hub):
        hub.remove(node)
    for node in list(templates['menu'])[:59]:
        hub.append(deepcopy(node))
    assert len(hub) == 59 and hub[-1].get('image') == 'c_back_png'

    state = E.SubElement(b.theme, 'Window', id='info_page_state', x='0', y='0',
                         visible='false', dragdrop='false', playondrop='false')
    marker = b.bitmap('info_state_marker', Image.new('RGBA', (1, 1)), prescaled=True)
    frame_state = E.SubElement(b.theme, 'Window', id='info_frame_state', x='0', y='0',
                              visible='false', dragdrop='false', playondrop='false')
    for identifier in [f'info_frame_{c}' for c in range(1,8)]+['info_frame_idle']:
        layout = E.SubElement(frame_state,'Layout',id=identifier,width='1',height='1')
        E.SubElement(layout,'Image',image=marker,x='0',y='0')
    # Trigger only real color changes. Initial/restored panes have their static
    # palette immediately, rather than inventing a yellow-to-blue startup fade.
    for layout in b.theme.findall('Window[@id="main"]/Layout'):
        for node in layout:
            if node.get('up') == 'm_color_no_png':
                value=node.get('action')
                match=re.match(r'palette_state.setLayout\(palette_([1-7])\);',value)
                assert match
                node.set('action',value[:match.end()]+f'info_frame_state.setLayout(info_frame_{match.group(1)});'+value[match.end():])
    report = dict(version=1, scale=b.scale, fps=20, page_in_ms=400,
                  page_out_ms=500, frame_ms=700, routes=[], frames=[])

    def native(name):
        im = rgba(name)
        if b.scale != 1:
            im = im.resize((im.width*b.scale, im.height*b.scale), Image.Resampling.LANCZOS)
        return im

    def strip(key, image, alphas):
        seq = Image.new('RGBA', (image.width, image.height*len(alphas)))
        for i, alpha in enumerate(alphas):
            frame = image.copy()
            frame.putalpha(image.getchannel('A').point(lambda a: (a*alpha+127)//255))
            seq.paste(frame, (0, i*image.height))
        return b.bitmap(key, seq, frames=len(alphas), fps=20, loop=1, prescaled=True)

    def animation(parent, key, x, y, visibility, identifier):
        # CtrlImage is static/cached; CtrlButton draws AnimBitmap with alpha.
        # Equal state resources avoid restarting it on hover/press/release.
        return E.SubElement(parent, 'Button', id=identifier, up=key, over=key,
                            down=key, action='none', x=str(x), y=str(y), visible=visibility)

    # Fade only changing frame pixels. Existing original Image controls retain
    # all metal artwork, move handles and the final palette. These sparse
    # overlays disappear completely after 700 ms, restoring native frame hits.
    for color in range(1, 8):
        previous = color-1 if color > 1 else 7
        nodes = [n for n in list(hub) if n.tag == 'Image' and
                 n.get('visible') == f'palette_{color}.isActive']
        for part, node in enumerate(nodes):
            name = node.get('image').removesuffix('_png')
            target = native(name+'.png')
            old = native(name.rsplit('_', 1)[0]+f'_{previous}.png')
            if node.get('width'):
                size = (int(node.get('width')), int(node.get('height')))
                def tile(im):
                    result = Image.new('RGBA', size)
                    for y in range(0, size[1], im.height):
                        for x in range(0, size[0], im.width):
                            result.paste(im, (x,y))
                    return result
                old, target = tile(old), tile(target)
            assert old.getchannel('A').tobytes() == target.getchannel('A').tobytes()
            diff = ImageChops.difference(old.convert('RGB'), target.convert('RGB'))
            r,g,blue = diff.split()
            mask = ImageChops.lighter(ImageChops.lighter(r,g),blue).point(lambda a:255 if a else 0)
            # shortcut: fractional-alpha edge pixels switch immediately; fade
            # only opaque pixels until a native renderer can safely blend the
            # cached Image edges without changing their shape/black backing.
            mask = ImageChops.multiply(mask, target.getchannel('A').point(lambda a:255 if a == 255 else 0))
            box = mask.getbbox()
            if box is None:
                continue
            patch = old.crop(box)
            patch.putalpha(mask.crop(box))
            key = strip(f'info_frame_{color}_{part}', patch, [round(255*(14-i)/14) for i in range(15)])
            # Before fixed content/close feedback; no window-wide opacity.
            overlay = animation(hub, key, int(node.get('x'))+box[0], int(node.get('y'))+box[1],
                                f'palette_{color}.isActive and info_frame_{color}.isActive', f'decorative_info_frame_{color}_{part}')
            hub.remove(overlay)
            hub.insert(hub.index(node)+1, overlay)
            report['frames'].append(dict(color=color, previous=previous, part=part,
                source=name+'.png', resource=key, crop=list(box), x=int(overlay.get('x')), y=int(overlay.get('y'))))

    pages = sorted(p.stem for p in SOURCE.glob('c_sub_*.jpg'))
    incoming = {p:strip('info_page_in_'+p, native(p+'.jpg'),
                      [round(50+205*i/8) for i in range(9)]) for p in pages}
    outgoing = {p:strip('info_page_out_'+p, native(p+'.jpg'),
                      [round(255*(10-i)/10) for i in range(11)]) for p in pages}
    link = strip('info_link_in', native('c_link_no.jpg'), [0]*8+[255])
    menu_hits = []
    for index,node in enumerate(n for n in templates['menu'] if n.tag=='Button' and n.get('up','').startswith('menu_')):
        # A one-level-alpha native Button receives clicks without CtrlImage's
        # cached-black paint. It releases input at the original 500 ms endpoint.
        mapping=Image.open(SOURCE/'c_menu_map.png').convert('RGB')
        color=(0,index*51,255)
        mask=Image.new('L',mapping.size)
        mask.putdata([255 if pixel==color else 0 for pixel in mapping.getdata()])
        box=mask.getbbox(); image=native('c_menu_no.jpg')
        if b.scale!=1:mask=mask.resize(image.size,Image.Resampling.NEAREST)
        image.putalpha(mask);image=image.crop(tuple(v*b.scale for v in box))
        seq=Image.new('RGBA',(image.width,image.height*2))
        image.putalpha(image.getchannel('A').point(lambda a:1 if a else 0))
        seq.paste(image,(0,0))
        menu_hits.append(b.bitmap(f'info_menu_hit_{index}',seq,frames=2,fps=2,loop=1,prescaled=True))

    def state_id(target, previous=None):
        return 'info_state_'+target+(('_from_'+previous) if previous else '')

    def action(target, previous):
        if target == 'menu':
            sid = state_id('menu', previous) if previous in pages else state_id('menu')
        elif target == 'about':
            sid = state_id('about')
        else:
            sid = state_id(target, previous) if previous in pages else state_id(target)
        return f'info_page_state.setLayout({sid})'

    def rewrite(node, previous, legacy=False):
        value = node.get('action')
        if value:
            def replace(match):
                return action(match.group(1), previous)
            value = re.sub(r'info\.setLayout\(info_(\w+)\)', replace, value)
            if legacy and 'info_page_state.setLayout(' in value:
                value = 'info.setLayout(info_menu);'+value
            if 'main.setLayout(main_start)' in value:
                value = 'info_frame_state.setLayout(info_frame_idle);'+value
            node.set('action', value)

    # Compatibility layouts stay usable and keep their saved geometry/page;
    # their first navigation enters the live state machine.
    for layout in window:
        if layout is hub:
            continue
        previous = layout.get('id').removeprefix('info_')
        for node in layout:
            rewrite(node, previous, legacy=True)

    routes = [('about',None)] + [(p,None) for p in pages]
    for previous in pages:
        group, index = previous.rsplit('_',1)
        for target in pages:
            if target.rsplit('_',1)[0] == group and abs(int(target.rsplit('_',1)[1])-int(index)) == 1:
                routes.append((target,previous))
        routes.append(('menu',previous))
    routes.append(('menu',None))  # Default last, matching a fresh static menu.

    for target, previous in routes:
        sid = state_id(target,previous)
        layout = E.SubElement(state,'Layout',id=sid,width='1',height='1')
        E.SubElement(layout,'Image',image=marker,x='0',y='0')
        visibility = sid+'.isActive'
        contents = [deepcopy(n) for n in list(templates[target])[59:]]
        for node in contents:
            # These content states are mutually exclusive; frame is shared.
            node.set('visible',visibility)
            rewrite(node,target)
        if target in pages:
            # Preserve the last completed page under a newly selected JPEG.
            backing = b.image(hub,(previous or 'c_back')+'.jpg',37,35,visible=visibility)
            resource = incoming[target]
            animation(hub,resource,37*b.scale,35*b.scale,visibility,'decorative_'+sid)
            contents = [n for n in contents if n.get('image') != target+'_jpg']
            if target == 'c_sub_4_1':
                contents = [n for n in contents if n.get('image') != 'c_link_no_jpg']
                animation(hub,link,127*b.scale,118*b.scale,visibility,'decorative_info_link')
        elif target == 'menu' and previous:
            backing = contents.pop(0)
            hub.append(backing)
            buttons=contents[:4]
            assert all(n.tag=='Button' and n.get('up','').startswith('menu_') for n in buttons)
            for node in buttons:hub.append(node)
            contents=contents[4:]
            resource = outgoing[previous]
            animation(hub,resource,37*b.scale,35*b.scale,visibility,'decorative_'+sid)
            for index,(node,key) in enumerate(zip(buttons,menu_hits)):
                forwarder=deepcopy(node)
                forwarder.set('id',f'info_menu_hit_{sid}_{index}')
                for attr in ('up','over','down'):forwarder.set(attr,key)
                hub.append(forwarder)
        else:
            resource = None
        for node in contents:
            hub.append(node)
        report['routes'].append(dict(state=sid,target=target,previous=previous,
                                     resource=resource,visible=visibility))

    # Native fades share a single live layout; this compatibility snapshot is
    # deliberately retained for prior saved IDs and source-art comparisons.
    path = b.out/'info-fades.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
