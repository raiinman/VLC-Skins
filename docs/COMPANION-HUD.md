# Settings and CC in the video hover strip

This optional addon belongs to the companion-derived skin. Standalone VLTs and
the validated helper stay unchanged. The compact strip remains 360x64 pixels at
both scales. The existing seek line shortens from 336 to 288 pixels, leaving
19x19 Settings and CC buttons at (307,2) and(332,2). Transport, time, volume,
fullscreen and close controls retain their positions and original assets.
All nine new icon states have a truly transparent outer pixel margin, preserving
the complete seek thumb at maximum position. CC on uses a restrained cyan tint.

`tools/companion_hud_assets.py` regenerates the PNGs, manifest and XML templates
in `dist/skin-support/companion-hud`. `companion_hud_apply.py` uses only the Python
standard library. `apply_companion_hud(xml_bytes, addon_folder)` returns derived
XML and only 10 new PNG payloads. The caller rejects archive-name collisions,
keeps original entry bytes/compression methods and owns its private packaging.
The bundle carries the injector next to its support files. The generator needs
Pillow during development, but the shipped injector does not.

The selected companion polls only its owned VLC's unique offscreen signal window
at (-31000,-30600), with height 17 and widths 211 (ready), 212 (Settings) and 213 (CC). It must
observe ready before arming, reset before dispatch, ignore repeated/stale triggers,
and never read unrelated window captions. Native Image.action2 cells accept a
posted double-click at these fixed points:

| Point | Action |
| --- | --- |
| (1,1) | Reset signal to ready |
| (11,1) | Set CC indicator on |
| (21,1) | Set CC indicator off |
| (31,1) | Make managed playback controls available |
| (41,1) | Make controls unavailable |

The hidden CC state defaults off; the hidden availability state defaults
unavailable. The host enables the new buttons only for a ready managed YouTube
entry and updates CC from actual native caption state. The addon does not invent
a VLC subtitle boolean, enqueue media or create additional subtitle tracks.
Settings menus anchor beside the actual selected player's exposed HUD button,
including framed 361x64 and native fullscreen 360x64 controllers. No new pipe,
HTTP command surface or helper capability is introduced.

`python tools/check_companion_hud.py` validates both actual VLT sources, DTD,
resource hashes/paths/IDs, exact routes/defaults, visible gates, feedback, full
thumb clearance and unchanged original payloads/compression. It rejects 10
mutations per scale, including overlap between alpha-1 native hit pixels.
Host dispatch, quality/caption preservation and running-session adoption require
separate companion evidence. Exact hashes are in companion-hud-review.json.
