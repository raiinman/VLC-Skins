"""Compare actual VLT pixels/timing/controls and retained RGBA storage offline."""
import argparse
from functools import lru_cache
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import zipfile

from lxml import etree as E
from PIL import Image

from build import ROOT


def digest(data):
    return hashlib.sha256(data).hexdigest()


def control_signatures(tree):
    """Allow only equivalent sharing of static mutually exclusive Info backings."""
    hub=tree.find('Window[@id="info"]/Layout[@id="info_menu"]')
    signatures={}
    if hub is not None:
        states={n.get('id')+'.isActive' for n in tree.findall('Window[@id="info_page_state"]/Layout')}
        for active in [None,*sorted(states)]:
            rendered=[]
            for original in hub:
                node=E.fromstring(E.tostring(original))
                expression=node.get('visible','')
                if 'info_state_' in expression:
                    tokens=re.findall(r'[A-Za-z0-9_.]+',expression)
                    assert set(tokens) <= states|{'or'}, 'Unexpected route expression'
                    if active not in tokens: continue
                    node.attrib.pop('visible')
                    if (node.tag == 'Image' and re.fullmatch(r'(c_back|c_sub_[1-4]_\d+)_jpg',node.get('image',''))):
                        assert set(node.attrib) <= {'id','image','x','y'}, 'Shared backing has extra behavior'
                        node.attrib.pop('id',None)
                rendered.append(E.tostring(node,method='c14n'))
            signatures[active or 'no_route']=digest(b''.join(rendered))
        for child in list(hub):hub.remove(child)
    return digest(E.tostring(tree,method='c14n')),signatures


def inspect(path):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None, 'Invalid archive CRC'
        tree = E.fromstring(archive.read('theme.xml'), E.XMLParser(remove_blank_text=True))
        resources = {}
        decoded = copied = containers = 0
        file_count = len(tree.findall('Bitmap'))

        @lru_cache(maxsize=2)
        def pixels(name):
            with Image.open(io.BytesIO(archive.read(name))) as image:
                return image.convert('RGBA')

        for bitmap in tree.findall('Bitmap'):
            image = pixels(bitmap.get('file'))
            decoded += image.width*image.height*4
            if len(bitmap):
                containers += image.width*image.height*4
                entries = list(bitmap)
            else:
                entries = [bitmap]
            for node in entries:
                actual = image
                if node.tag == 'SubBitmap':
                    x,y,w,h = (int(node.get(k)) for k in ('x','y','width','height'))
                    assert x >= 0 and y >= 0 and x+w <= image.width and y+h <= image.height
                    actual = image.crop((x,y,x+w,y+h))
                    copied += w*h*4
                key = node.get('id')
                assert key not in resources, 'Duplicate bitmap ID'
                resources[key] = dict(size=list(actual.size), rgba_sha256=digest(actual.tobytes()),
                    frames=node.get('nbframes','1'), fps=node.get('fps','0'), loop=node.get('loop','0'))
            tree.remove(bitmap)
        # Every non-bitmap node, including all actions, control order, IDs,
        # visibility, font settings and window geometry must stay identical.
        image_controls=tree.findall('.//Image')
        image_cache=sum(resources[n.get('image')]['size'][0]*resources[n.get('image')]['size'][1]*4
                        for n in image_controls)
        controls, routes = control_signatures(tree)
        payloads = {name:digest(archive.read(name)) for name in archive.namelist()
                    if name != 'theme.xml' and not name.lower().endswith('.png')}
        return dict(sha256=digest(path.read_bytes()), package_bytes=path.stat().st_size,
                    resources=resources, non_bitmap_xml_sha256=controls,
                    info_route_draw_order_sha256=routes, other_payloads=payloads,
                    top_level_png_count=file_count,
                    image_control_count=len(image_controls), initial_image_cache_rgba_bytes=image_cache,
                    decoded_file_rgba_bytes=decoded, subbitmap_copy_rgba_bytes=copied,
                    retained_bitmap_rgba_bytes=decoded+copied, atlas_parent_rgba_bytes=containers)


def compare(before, after):
    assert before['resources'] == after['resources'], 'Bitmap pixels, dimensions or animation timing changed'
    assert before['non_bitmap_xml_sha256'] == after['non_bitmap_xml_sha256'], 'Controls/geometry/font/action XML changed'
    assert before['info_route_draw_order_sha256'] == after['info_route_draw_order_sha256'], 'Info route draw order/controls changed'
    assert before['other_payloads'] == after['other_payloads'], 'Non-image package payload changed'
    saved = before['retained_bitmap_rgba_bytes']-after['retained_bitmap_rgba_bytes']
    assert saved > 0, 'No retained bitmap RGBA reduction'
    def summary(item):
        return {k:v for k,v in item.items() if k not in ('resources','other_payloads','info_route_draw_order_sha256')}
    return dict(before=summary(before),after=summary(after),resource_count=len(after['resources']),
                equivalent_info_route_count=len(after['info_route_draw_order_sha256']),
                initial_image_cache_rgba_saved_bytes=before['initial_image_cache_rgba_bytes']-after['initial_image_cache_rgba_bytes'],
                exact_pixels_timing_and_controls=True,retained_bitmap_rgba_saved_bytes=saved)


def self_test():
    def package(path, packed, changed=None):
        root = E.Element('Theme',version='2.0')
        strip = Image.new('RGBA',(2,4),(23,41,67,255))
        if changed == 'pixel': strip.putpixel((0,0),(24,41,67,255))
        resource = E.SubElement(root,'Bitmap',id='atlas' if packed else 'test',file='assets/test.png')
        if packed:
            resource = E.SubElement(resource,'SubBitmap',id='test',x='0',y='0',width='2',height='4')
        resource.set('nbframes','2'); resource.set('fps','21' if changed == 'fps' else '20'); resource.set('loop','1')
        E.SubElement(root,'Window',id='main',visible='false' if changed == 'control' else 'true')
        encoded=io.BytesIO();strip.save(encoded,format='PNG')
        with zipfile.ZipFile(path,'w') as archive:
            archive.writestr('theme.xml',E.tostring(root))
            archive.writestr('assets/test.png',encoded.getvalue())
    with tempfile.TemporaryDirectory() as folder:
        a,b = (Path(folder)/name for name in ('a.vlt','b.vlt'))
        package(a,True);package(b,False)
        before=inspect(a)
        assert compare(before,inspect(b))['retained_bitmap_rgba_saved_bytes'] == 32
        for mutation in ('pixel','fps','control'):
            package(b,False,mutation)
            try: compare(before,inspect(b))
            except AssertionError: pass
            else: raise AssertionError('Mutation accepted: '+mutation)
    prefix='<Theme><Window id="info_page_state"><Layout id="info_state_a"/><Layout id="info_state_b"/></Window><Window id="info"><Layout id="info_menu">'
    suffix='</Layout></Window></Theme>'
    def backing(state,identifier):
        return f'<Image id="{identifier}" image="c_back_jpg" x="37" y="35" visible="{state}"/>'
    a,b='info_state_a.isActive','info_state_b.isActive'
    button=f'<Button id="nav" up="test" action="none" visible="{a}"/>'
    before=prefix+backing(a,'a')+button+backing(b,'b')+suffix
    after=prefix+backing(a+' or '+b,'a')+button+suffix
    expected=control_signatures(E.fromstring(before))
    assert expected == control_signatures(E.fromstring(after)), 'Equivalent shared backing rejected'
    for mutation in (prefix+button+backing(a+' or '+b,'a')+suffix,
                     after.replace('action="none"','action="vlc.stop()"'),
                     after.replace(a+' or '+b,a)):
        assert expected != control_signatures(E.fromstring(mutation)), 'Route/control mutation accepted'
    print('PASS storage fixtures: exact reorganization/sharing accepted; six pixel/timing/control/route mutations rejected')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        self_test();return
    assert args.baseline and args.output, '--baseline and --output required'
    report=dict(method='Offline actual-package pixels, timing, non-bitmap XML and other payload comparison. '
                'Retained RGBA = FileBitmap buffers + copied SubBitmaps per VLC source; excludes graphics, '
                'decoder temporaries and all other allocations. Initial CtrlImage cache pixels are counted separately '
                'from source dimensions per constructor, not post-resize memory. This is not measured RSS or startup time.',results=[])
    for scale in (1,2):
        name=f'Need-for-Speed-Underground-{scale}x.vlt'
        result=compare(inspect(args.baseline/name),inspect(ROOT/'dist'/name))
        result['scale']=scale;report['results'].append(result)
        print(f'PASS {scale}x: exact {result["resource_count"]} resources, timing, controls and other payloads; '
              f'{result["retained_bitmap_rgba_saved_bytes"]/1024**2:.2f} MiB fewer retained bitmap bytes')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':main()
