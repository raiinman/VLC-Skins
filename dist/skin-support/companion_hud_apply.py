"""Apply the optional companion HUD addon to XML; standard library only.

No archive, profile or installed skin is modified. The caller receives new XML
and only the verified new archive payloads, then owns its derived-skin packaging.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
import xml.etree.ElementTree as ET
import zlib


class AddonError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AddonError(message)


def _safe_path(value):
    require(isinstance(value, str) and 0 < len(value) <= 256, 'Invalid addon path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and '\\' not in value and ':' not in value
            and all(p not in ('', '.', '..') for p in value.split('/')), 'Unsafe addon path: '+value)
    return value


def _read(folder, relative):
    relative = _safe_path(relative)
    candidate = folder/relative
    path = candidate.resolve()
    require(path.is_relative_to(folder) and path.is_file() and not candidate.is_symlink(), 'Addon file escapes its folder or is missing')
    require(path.stat().st_size <= 4*1024*1024, 'Oversized addon file')
    return path.read_bytes()


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _png_size(data):
    require(data.startswith(b'\x89PNG\r\n\x1a\n'), 'Addon asset is not PNG')
    offset, size, ended = 8, None, False
    while offset < len(data):
        require(offset+12 <= len(data), 'Truncated PNG chunk')
        length = struct.unpack_from('>I', data, offset)[0]
        end = offset+length+12
        require(end <= len(data), 'Truncated PNG payload')
        kind, body = data[offset+4:offset+8], data[offset+8:end-4]
        require(zlib.crc32(kind+body) == struct.unpack_from('>I', data, end-4)[0], 'PNG CRC mismatch')
        if offset == 8:
            require(kind == b'IHDR' and length == 13, 'Invalid PNG header')
            size = struct.unpack_from('>II', body)
        if kind == b'IEND':
            require(length == 0 and end == len(data), 'PNG trailing payload')
            ended = True
        offset = end
    require(ended and size is not None, 'Incomplete PNG')
    return size


def _xml(data, addon=False):
    require(isinstance(data, bytes) and len(data) <= 16*1024*1024, 'Invalid XML bytes')
    require(b'<!ENTITY' not in data.upper() and (not addon or b'<!DOCTYPE' not in data.upper()), 'XML entity declarations are forbidden')
    try:
        return ET.fromstring(data, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
    except ET.ParseError as error:
        raise AddonError('Invalid XML') from error


def _ids(tree):
    values = [n.get('id') for n in tree.iter() if n.get('id')]
    require(len(values) == len(set(values)), 'Duplicate XML IDs')
    return set(values)


def _load(addon_folder):
    folder = Path(addon_folder).resolve()
    try:
        manifest = json.loads(_read(folder, 'manifest.json'))
        require(manifest['schemaVersion'] == 1 and manifest['assetPrefix'] == 'companion-hud/', 'Unsupported addon manifest')
        template = manifest['template']
        xml = _read(folder, template['file'])
        require(_hash(xml) == template['sha256'], 'Addon template hash mismatch')
        tree = _xml(xml, addon=True)
        require(tree.tag == 'CompanionHudAddon' and tree.get('schemaVersion') == '1', 'Unsupported addon template')
        require([n.tag for n in tree] == ['Resources', 'Controllers', 'Windows'], 'Unexpected addon template sections')
        identifiers = _ids(tree)
        expected = {'yt_hud_settings_'+s for s in ('no', 'hov', 'do')}
        expected |= {'yt_hud_cc_'+state+'_'+s for state in ('off', 'on') for s in ('no', 'hov', 'do')}
        expected.add('yt_hud_command_hit')
        assets, payloads = {}, {}
        for item in manifest['assets']:
            key = item['id']
            require(key in expected and key not in assets, 'Unexpected or duplicate addon asset ID')
            data = _read(folder, item['file'])
            require(_hash(data) == item['sha256'], 'Addon asset hash mismatch: '+key)
            size = _png_size(data)
            require(size == (item['width'], item['height']) == ((3, 3) if key == 'yt_hud_command_hit' else (19, 19)), 'Addon asset geometry mismatch')
            archive_path = _safe_path(manifest['assetPrefix']+item['file'])
            require(archive_path not in payloads, 'Duplicate addon archive path')
            assets[key] = archive_path
            payloads[archive_path] = data
        require(set(assets) == expected, 'Missing addon assets')
        resources = list(tree.find('Resources'))
        require(len(resources) == len(assets), 'Unexpected addon resources')
        for node in resources:
            require(node.tag == 'Bitmap' and len(node) == 0 and node.get('id') in assets
                    and node.get('file') == assets[node.get('id')]
                    and node.get('alphacolor') == '#FF00FF', 'Addon resource declaration differs from manifest')
        require({n.get('id') for n in resources} == set(assets), 'Missing addon resource declaration')
        require(manifest['seek'] == dict(x=12, y=12, length=288, oldLength=336,
                                         sliderPoints='(0,0),(288,0)', railWidth=288), 'Unsupported seek adaptation')
        return tree, identifiers, payloads
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise AddonError('Malformed addon manifest') from error


def apply_companion_hud(xml_bytes, addon_folder):
    """Return (derived_xml_bytes, {archive_relative_path: new_payload_bytes}).

    Reject duplicate application rather than guessing how to overwrite a derived
    theme. Existing seek rails must match the audited compact HUD before editing.
    All other original nodes and resources retain their attributes and order.
    """
    original = _xml(xml_bytes)
    require(original.tag == 'Theme', 'Expected VLC Theme XML')
    addon, identifiers, payloads = _load(addon_folder)
    require(not (_ids(original) & identifiers), 'Addon ID collides with existing theme')
    require(not ({n.get('file') for n in original.iter() if n.get('file')} & set(payloads)), 'Addon archive path collides with original payload')
    controllers = list(addon.find('Controllers'))
    require(len(controllers) == 2 and {n.get('layout') for n in controllers} == {'fullscreen_controls', 'video_hover_controls'}, 'Unexpected addon controllers')
    for controller in controllers:
        layouts = [n for n in original.iter('Layout') if n.get('id') == controller.get('layout')]
        require(len(layouts) == 1, 'Missing compact controller layout')
        layout = layouts[0]
        sliders = [n for n in layout if n.tag == 'Slider' and n.get('value') == 'time']
        require(len(sliders) == 1, 'Expected one compact seek slider')
        slider = sliders[0]
        require((slider.get('x'), slider.get('y'), slider.get('points')) == ('12', '12', '(0,0),(336,0)'), 'Compact seek slider differs from audited geometry')
        index = list(layout).index(slider)
        rail = layout[index-1] if index else None
        require(rail is not None and rail.tag == 'Image' and rail.get('image') == 'compact_rail'
                and all(rail.get(k) == v for k, v in dict(x='12', y='10', width='336', height='3', resize='scale').items()), 'Compact seek rail differs from audited geometry')
        rail.set('width', '288')
        slider.set('points', '(0,0),(288,0)')
        for node in controller:
            require(node.tag in ('Button', 'Checkbox'), 'Unsupported addon control')
            layout.append(deepcopy(node))
    first_window = next((i for i, node in enumerate(original) if node.tag == 'Window'), len(original))
    for index, resource in enumerate(addon.find('Resources')):
        original.insert(first_window+index, deepcopy(resource))
    for window in addon.find('Windows'):
        require(window.tag == 'Window', 'Unsupported addon window')
        original.append(deepcopy(window))
    _ids(original)
    start = xml_bytes.find(b'<Theme')
    require(start >= 0, 'Missing Theme element')
    return xml_bytes[:start]+ET.tostring(original, encoding='utf-8'), payloads


__all__ = ['AddonError', 'apply_companion_hud']
