# Clock, shutter and framed wheel corrections

Both scales have development candidates. The user-authorized1x review update is
now running with the matching helper and wheel DLL;2x remains offline. Packaging,
ZIPs and release remain on hold. review-1x-rollout.json records exact deployed
hashes, preserved fresh queue/settings/geometry and read-only integration checks.
Clock phase commands and wheel-hook attachment were observed without input;
actual wheel behavior, clock raster timing and visual parity remain for review.

Clock clicks select an independent elapsed/remaining state. They never select a
main layout, so they do not interrupt/restart shutter travel or change palettes.
The existing artwork, animation frame/timing data and control identities remain.
Four small offscreen clock states preserve mode and alternate paint phases.
The matching helper requests a phase change at most every500ms. Native Text
visibility refresh reads the current completed-seek time; it never issues a seek,
play/pause pulse or reload. Main and both compact HUD clocks use the same phase.
Without the matching helper, normal clock updates and mode switching still work,
but periodic paused-seek refresh is unavailable. VLC still formats an exact zero
position as unavailable; this correction does not change that native rule.

The framed hover strip is positioned by the helper while VLC retains its original
internal offscreen origin. NfsWheelBridge64.dll corrects only existing queued
WM_MOUSEWHEEL coordinates for that marked361x64 strip, on one validated VLC UI
thread. It preserves the message, wheel delta and modifiers. It never generates
input, hooks global mouse/keyboard input, moves the pointer, changes focus or
patches installed VLC. Native fullscreen and unrelated windows pass unchanged.
The helper validates matching PE architecture and initial canonical origin,
sets the enable marker last and removes it first, and retains the DLL until
unhook succeeds. Missing DLLs, unsupported architectures and custom initial
origins leave legacy behavior usable without guessing. The present DLL build is
x64;32-bit VLC correction remains unsupported.

Focused source/package checks pass at both scales, including DTD, unchanged
animation/pixel contracts,43 clock layouts,11 rejected clock mutations,16 HUD
phase/playback/volume hit states,23 original HUD mutations and closed-launch
migration. The companion independently checked migration against both actual
new XMLs. Compiled helper pure checks pass. Private cross-process wheel tests
pass13 routing/passthrough cases with process/file/desktop preservation and cleanup.
That fixture uses a synthetic child window, not actual VLC playback controls.
Native paused-seek raster timing, shutter continuity under real clicks and final
VLC wheel behavior remain unobserved for these exact candidates. No complete
parity or live deployment is claimed.

Sources: VideoLAN3.0.23 skins2/controls/ctrl_text.cpp visibility refresh,
vars/time.cpp and utils/var_text.cpp observer ordering, win32/win32_loop.cpp wheel
translation; Microsoft GetMsgProc and SetWindowsHookExW thread/DLL contracts.

Primary references: [VLC wheel translation](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/win32/win32_loop.cpp), [Text refresh](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/controls/ctrl_text.cpp), [GetMsgProc](https://learn.microsoft.com/en-us/windows/win32/winmsg/getmsgproc), [thread hook contract](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowshookexw).

The subsequent clock-command capture correction is documented in DRAG-CAPTURE.md
and drag-capture-review.json. It preserves dragging while deferring clock refresh
until release; earlier verification/activation hashes remain historical.

The later persistent clock_refresh_command receiver is documented in
PLAYLIST-AND-TOOLTIPS.md. Its phase_a;phase_b macro keeps text refresh during
hover without repeatedly canceling native tooltips. Both scales passed the
186-case actual private native mechanism test, including legacy cancellation
and repeated fixed-receiver survival. Exact candidate hashes and the combined
41-case capture/wheel proof are in playlist-tooltip-review.json. Physical tooltip
appearance and exact paused-seek raster latency remain distinct review limits.
