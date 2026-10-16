# Docking to exposed panes

Native VLC considers covered but logically visible skin panes as docking targets.
The optional bridge now rejects a target only when higher opaque window regions
fully cover its shaped region. Partially exposed panes remain eligible. The
actual native moving group and the helper's validated hover bar are excluded
from covering windows. Other VLC panes can cover a target too.

This runs only in the explicitly owned copied portable runtime, with an exact
VLC3.0.23 skins2 plugin SHA256 and checked machine-code signatures. The plugin
may be adjacent to the private runtime or at the exact standard installed path
resolved through the Windows64 Program Files known folder, matching the existing
companion launcher's shared-plugin design. Installed VLC processes and
unsupported plugin versions keep native behavior. Neither installed nor copied
plugin files are modified. Only the private process's two
checked function entries are redirected: checkAnchors supplies native moving-set
context, and canHang filters its two exact call sites before native snapping.
Screen magnetism, dependency construction, coordinates and anchor offsets stay
native. Unknown geometry, opacity, cloak or object identity retains native
behavior rather than guessing that a pane is covered.

The official matching debug-symbol archive's GNU debuglink CRC was verified.
Named native addresses and whole-instruction prologues were checked against the
exact plugin. No decompiler result is claimed. Remote bridge code is pinned
before redirects are installed, so removing the helper cannot leave dangling
branches. Removing its validated enable marker restores native decisions through
the retained original code. The process releases this code on exit.

The production DLL passed28 actual private VLC cases across both exact skin
packages, including the original covered attraction baseline, covered rejection
in both native call orientations, exposed/partial snaps, main-carried groups,
child detachment, screen edge and marker-removal fallback. All retained process,
file, input-desktop and cleanup guards passed; copied plugin bytes stayed exact.
Earlier rejected signature and incorrect call-orientation candidates remain
failed evidence. They were never loaded into the user's session.

The first user-session activation exposed a launcher-contract difference: its
private executable shares the standard installed plugin files, rather than
copying that tree. The stricter adjacent-plugin-only gate refused activation
with Status2. The compatibility candidate retains every private-executable,
hash and signature check while permitting only that exact standard plugin path.
Its shared-plugin actual native probe and later Status1 readback are recorded
separately from the earlier adjacent-plugin fixture proof.

exposed-docking-review.json records exact hashes and scope. These tests use
bounded messages only on owned windows on a private non-input desktop. They do
not establish physical drag feel or complete user acceptance. Packaging is held.

The matched1x setup is now loaded, and a read-only check confirms Status1 active,
wheel binding, the enabled clear capability, ready request state, persistent
clock command/elapsed phaseB and video-owned hover bar. The actual empty queue,
stopped state,100percent volume, all six pane geometries and settings were
preserved. No earlier165-row checkpoint was restored. See
exposed-docking-rollout.json. The inactive2x profile and installed files were
not changed; both development packages retain their separate private test proof.
