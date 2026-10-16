# Drag capture correction

The user reported movement catching at other windows. Source inspection confirms
native docking checks registered VLC skin windows and the Windows work area,
not arbitrary application windows. The companion fits only its embedded child
windows, without changing the outer native pane position.

A concrete interfering path was found in the newly added500ms clock refresh:
its offscreen WM_LBUTTONDBLCLK reaches VLC Win32Loop, which calls ReleaseCapture
before dispatching the command. That can release pane/slider mouse capture in
the middle of a drag. This source defect can explain the symptom; no physical
user drag was observed or controlled during this investigation.

The helper now defers offscreen commands while the selected VLC GUI thread
owns capture, or when that thread state cannot be read. The native bridge also
suppresses the exact offscreen clock command during capture on that same thread,
closing the race between posting and dispatch. Commands resume after release.
Normal user double-clicks, wheel behavior, native docking and screen-edge
snapping retain their behavior. No global input hook, pointer movement, focus
change, native VLC patch or media command is introduced.

Plain native covered-but-visible VLC panes may still attract docking. The later
private-runtime filter in EXPOSED-DOCKING.md removes proven covered targets for
the exact supported plugin. Screen magnetism uses VLC's primary work area.
Those are separate from this capture correction's historical evidence.

Packaging remains on hold. Exact compiled candidates, focused private regression
results and any coordinated runtime repair are recorded in drag-capture-review.json.
Historical wheel/clock and activation reports keep their earlier hashes and scope.

Sources: [VLC double-click handler](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/win32/win32_loop.cpp), [VLC snapping](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/window_manager.cpp), [explicit GUI-thread state](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getguithreadinfo).

The matched helper/DLL repair is now loaded in the owned1x review setup. All165
queue entries, selected ordinal161, paused2seconds, volume307(120percent),
Auto/captions settings, all six geometries and elapsed clock mode were preserved.
Normal/profile/source/sound settings stayed unchanged. Idle clock phases151/152
and wheel-hook attachment were observed read-only. Actual user dragging remains
for review. See drag-capture-rollout.json; no release/bundle or2xprofile was made.
