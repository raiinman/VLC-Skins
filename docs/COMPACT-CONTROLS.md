Current refinement: the HUD now uses a flat smoked-charcoal fill at the user's
request, with the same rounded shape and subtle border. The speaker glyph is
centered inside its23px circle; filename text is two source pixels below the
backing's top edge. See UI-POLISH.md for current exact packages and evidence.

# Compact controls and filename readability

The user approved a slim smoked-charcoal strip in place of the full framed hover
pane. Both skins now use the same360x64 physical artwork (361px framed window,
including an invisible identification column), down from425x146 at1x and
850x292 at2x. It has no outer pane frame or duplicate filename header. Original
29px transport controls retain exact normal/hover/pressed pixels; the seek rail
is thin, time is readable11px white, and fullscreen/hide remain native buttons.

Volume shows a small speaker/percentage by default. The helper expands its
native slider on hover in either bar; clicking the speaker provides a fallback
when loading the VLT without the helper. No input layer covers the video, so
native double-click remains available. The native fullscreen controller keeps
VLC's fade. The helper keeps the framed bar fully opaque (255/255), preventing video
detail from showing through the matching flat fill and button edges.
Theme alpha is unchanged so the main player and other panes remain unaffected.

The main filename uses12px at1x and24px at2x, replacing8/16px palette-colored
text. White scrolling text sits on a dark177x16 source-scale backing. It leaves
the gauge's final row and original logo intact. Fonts and the backing are an
explicit user-approved readability adaptation, independently checked rather
than silently ignored in retained-art comparisons.

Schema2 carries fixed compact geometry and four offscreen commands. The helper
continues accepting exact schema1 large-bar packages. Dedicated launchers read
the packaged manifest and migrate only helper-owned saved window entries,
preserving private main/pane placement. Do not mix schema2 VLTs with an old
schema1-only helper. The complete review bundle supplies matching versions.

The new Lua volume observer polls its owning VLC every 50 ms, baselines the
first sample and requests VLC's own top-right volume text and vertical bar on
later changes, including windowed video. It does not change media volume.
Start-NFS adds `--osd --extraintf=luaintf --lua-intf=nfs_volume_osd_v1` and
sets `VLC_DATA_PATH` on that child only, pointing to bundled skin-support/data.
It changes no global environment or installed VLC files. The bundle ships the
script in data/lua/intf; Python and test-only Lupa are unnecessary at runtime.
The companion must instead copy it into its own portable/lua/intf directory
and combine its existing HTTP interface as `--extraintf=http:luaintf`; that
integration is coordinated separately and has not been deployed here.

VLC 3.0.23 source grounds this approach: skins2/vars/volume.cpp changes volume
without the hotkeys DisplayVolume call; Lua libs/volume.c uses 256 at 100%,
libs/osd.c exposes native message/slider functions, and interface.c discovers
Lua interfaces under the application data directory. Mock tests exercise Lua
5.1 and 5.2 behavior, invalid values, output replacement and failure paths.

This candidate was prepared offline. XML validation, exact-art comparisons,
hit models, contrast/visibility/mutation tests, helper pure tests and asset
renders do not certify native opacity, hover expansion, scroll rendering or
OSD display. Those need a later coordinated live test. Existing running skins,
helpers, installed archives and active profiles were not changed. The earlier
native report remains in effects-hover-review.json with its original hashes.
Framed-bar mouse-wheel routing remains a known Skins2 origin limitation.
