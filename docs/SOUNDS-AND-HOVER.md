# Original sounds and video controls

Both VLTs include the five unchanged WAV files recovered from the original
skin: button.wav, shutter.wav, intro4.wav, imode.wav and eagames.wav. Original
WMS click bindings select their effects; opening information also signals its
original view-load sound. Startup/replay requests intro4.wav after the original
1.5-second static interval. Sliders and decorative animation do not emit clicks.

Skins2 cannot play a WAV directly. `SkinEffects.exe` supplies that capability
without adding the effects to VLC's playlist or changing media volume/mute.
The tray menu can mute skin sounds independently. Windows' application mixer
can also affect helper audio. The earlier silent-media incident was resolved
by unmuting VLC in Windows; it was separate from missing skin effects.

`fullscreenController` is VLC's special native auto-revealing controller for
borderless fullscreen. The original-art bar has previous, play/pause, stop,
next, seek, volume, fullscreen and hide controls. A second matching native
bar, `videoHoverController`, serves windowed/framed video. Its extra transparent
pixel distinguishes its native window from the fullscreen bar.

The helper observes the explicitly supplied VLC process and cursor position;
it shows the framed bar on video hover, retains it while hovered, and hides it
after 1.8 seconds without motion or when another application has focus. Native
VLC controls handle playback, seeking and volume. No transparent input layer
covers Video, so native double-click and context-menu input remain available.
The helper does not move the actual pointer, send keyboard input, change focus,
or stop VLC. It validates the installed VLC executable, PID and start time.

Offscreen native windows carry sound and hover layout signals. They stay
shown offscreen and switch layouts rather than calling activating
`Window.show()`/`hide()` for routine events. Each sound has a ready and trigger
size; the framed bar has an original-art open layout and transparent closed
layout. The helper dispatches
only to that VLC process's dedicated command images; ordinary media actions
remain in XML. Sound files are extracted from a five-file whitelist into an
instance-specific temporary directory and removed on exit. This implementation
adds no browser credentials, network interface or HTTP control password.

Use `Start-1x.cmd` or `Start-2x.cmd` from the complete support bundle. Each starts
a separate VLC process and helper, with a persistent private per-scale profile
under `%LOCALAPPDATA%\NfsUnderground\profiles`. The normal VLC profile and
already-running sessions remain intact. Plain VLT loading provides native
borderless hover controls; sound and framed hover require the helper. Existing
preview launchers remain isolated skin-only review tools.

Offline tests validate original WAV bytes, signal/action mappings, archive
contents, both bars' original pixels, control access and helper decisions.
Compilation and archive validation do not establish audible output, native
window discovery, overlay stacking, hover timing or fullscreen suppression.
Initial skin window creation still follows VLC's normal startup window-show
behavior; routine layout switches avoid repeating that activation path.
Those behaviors still require a coordinated live test at both scales. Earlier
fullscreen native reports apply only to the package hashes they recorded.

Official VLC 3.0.23 sources: [FscWindow](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/fsc_window.cpp),
[builder](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/parser/builder.cpp),
[interpreter](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/parser/interpreter.cpp),
[Win32 windows](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/win32/win32_window.cpp).
Context7 returned legacy skin/Lua examples rather than the current Skins2
sound/hover command surface; the pinned source and vendored DTD govern this work.
