"""Native corner docking, added after existing control IDs are assigned.

Four boundary points follow native corner references during resize. This is
corner alignment, not continuously sliding edge docking. Main carries directly
attached panes; equal-priority auxiliaries snap but remain independent.
"""
CANONICAL_WINDOWS = ('main', 'tracks', 'equalizer', 'video', 'info')
ALLOWED_WINDOWS = frozenset((*CANONICAL_WINDOWS, 'youtube'))
CORNERS = (('tl', 'lefttop', False, False),
           ('tr', 'righttop', True, False),
           ('bl', 'leftbottom', False, True),
           ('br', 'rightbottom', True, True))


def add_to_theme(theme, window_ids=CANONICAL_WINDOWS):
    """Add stable native anchors to explicitly selected real pane IDs.

    Compatible with lxml and stdlib ElementTree. Existing exact docking anchors
    are retained, making companion reapplication safe. Never touch controls,
    artwork, Theme magnet, window geometry or saved profiles.
    """
    selected = tuple(window_ids)
    if len(set(selected)) != len(selected) or not set(selected) <= ALLOWED_WINDOWS:
        raise ValueError('Only explicitly selected real docking panes are supported.')
    all_ids = [node.get('id') for node in theme.iter() if node.get('id')]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError('Theme IDs must be unique before docking augmentation.')
    known = set(all_ids)
    additions = []
    count = 0
    for name in selected:
        windows = theme.findall("Window[@id='%s']" % name)
        if len(windows) != 1:
            raise ValueError('Expected one real docking pane: ' + name)
        layouts = windows[0].findall('Layout')
        if not layouts:
            raise ValueError('Docking pane requires layouts: ' + name)
        for layout in layouts:
            identifier = layout.get('id')
            if not identifier:
                raise ValueError('Docking layouts require explicit IDs.')
            width, height = int(layout.get('width', '0')), int(layout.get('height', '0'))
            if width <= 0 or height <= 0:
                raise ValueError('Docking layouts require positive dimensions.')
            expected = []
            for suffix, reference, right, bottom in CORNERS:
                expected.append(dict(id='dock_'+identifier+'_'+suffix,
                    x=str(width if right else 0), y=str(height if bottom else 0),
                    lefttop=reference, points='(0,0)', range='15',
                    priority='2' if name == 'main' else '1'))
            anchors = layout.findall('Anchor')
            if anchors:
                if len(anchors) != 4 or [dict(n.attrib) for n in anchors] != expected:
                    raise ValueError('Unexpected existing docking anchors: ' + identifier)
            else:
                for attrs in expected:
                    if attrs['id'] in known:
                        raise ValueError('Docking ID collision: ' + attrs['id'])
                    known.add(attrs['id'])
                    additions.append((layout, attrs))
            count += 4
    # Validate the entire request before changing any layout.
    for layout, attrs in additions:
        layout.append(layout.makeelement('Anchor', attrs))
    return count


def add_window(theme, window_id):
    """Companion entry point, normally add_window(theme, 'youtube')."""
    return add_to_theme(theme, (window_id,))
