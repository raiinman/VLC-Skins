# Pane docking

Both scales use VLC native corner anchors on main, playlist, equalizer, video
and Info layouts. The companion adds matching anchors to its YouTube pane.
Bring two corners within15 physical pixels to align their edges. Screen-edge
snapping stays enabled at its original15-pixel threshold.

Main has priority2; auxiliary panes have priority1. Moving main carries panes
attached directly to it. Dragging an auxiliary pane detaches it. Equal-priority
auxiliaries align but do not form a moving group. Anchors follow resized outer
corners, with no artwork, animation, button or saved-geometry changes.

Native anchors provide corner alignment, not continuous sliding along any point
of an edge. Coincident same-side corners can overlap, and already-aligned hidden
children may follow main. Hidden panes do not attract new snaps. Helper, state,
hover and fullscreen windows have no docking anchors.

Each package contains308 anchors across77 layouts. The independent offline
oracle checks340 resized corner positions,7,272 layout/contact cases and nine
rejected mutations per scale, plus39 strict-range/visibility cases. Companion
augmentation reaches312 anchors. These are models, not physical drag testing.

Both exact packages pass88 private native drag/resize steps (44per scale).
The first fixture entered the native work-area snap zone; its failure remains
recorded separately. Moving the fixture away from monitor edges preserved the
product and thresholds. Process/file/input-desktop guards and cleanup pass.
Both user-library docking VLTs were installed with verified backups. The later
clock-corrected1x source is now active in the user-authorized companion review
setup (review-1x-rollout.json). Its anchors retain the same configuration; native
88-step evidence remains scoped to the earlier hashes in docking-review.json.
A clock-click attempt with unchanged geometry does not establish the selected
native clock layout. Packaging remains on hold for the user's parity review.

The later private-runtime covered-target filter is recorded in
EXPOSED-DOCKING.md and exposed-docking-review.json. Its exact production DLL and
both new source packages pass28 separate actual native cases, retaining exposed
and partial snaps, screen edges, native groups and marker-removal fallback.
This does not broaden the earlier88-step report to different package hashes.
