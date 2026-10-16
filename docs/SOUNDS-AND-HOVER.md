# Original sounds and video controls

The current offline candidate retains the compact 360 × 64 strip described in COMPACT-CONTROLS.md, with hover-expanded volume and a click fallback, and adds the Info/tooltip/playlist work in INFO-FADES.md. Current exact hashes and offline-only limits are in info-fades-review.json; compact-review.json records the preceding compact-only candidate. Native results later in this document apply to older large-bar versions recorded in effects-hover-review.json.

Both VLTs include the five unchanged WAV files recovered from the original
skin: button.wav, shutter.wav, intro4.wav, imode.wav and eagames.wav. Original
WMS click bindings select their effects; opening information also signals its
original view-load sound. Startup/replay requests intro4.wav after the original
1.5-second static interval. Sliders and decorative animation do not emit clicks.

Skins2 cannot play a WAV directly. `SkinEffects.exe` supplies that capability
without adding the effects to VLC's playlist or changing media volume/mute.
The tray menu can mute skin sounds independently. Windows' application mixer
can also affect helper audio. Process audio-meter activity establishes helper
output, rather than speaker audibility or an acoustic recording.

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
While the framed bar is requested open, the helper reasserts its stacking order
on every poll without activating it. Playback can reorder VLC's native windows
even when the bar's position has not changed. Framed maximize does not suppress
the bar: the borderless blocker must be a visible, unowned `SkinWindowClass`
window covering its monitor in the selected VLC process.

The helper owns framed-bar placement. Its background does not initiate native
dragging, which would use VLC's stale internal offscreen origin and make the
bar jump away. The separate native borderless fullscreen bar remains draggable.
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

Optional `--diagnostic-log` requires an explicit absolute path and creates a new
file. It records changed discovery, geometry, hover and sound-dispatch states,
without window titles, media identifiers or credentials. Normal operation does
not create this diagnostic log.

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

## Targeted native review

The later helper build `0e1186bac215` adds opt-in validation for a companion-managed
byte-identical portable VLC executable. Its pure and filesystem rejection tests
pass; the native review below retains its earlier helper hash. The new options
are `--trusted-vlc-runtime <absolute-exe> --installed-vlc <standard-installed-exe>
--pid-start-ticks <UTC-ticks>`, supplied together. Validation binds the process
path/start time, both executable hashes, `VlcRuntime/<SHA256>/vlc.exe` layout and
adjacent `portable` directory. Default standalone launches remain installed-only.
The companion owns DLL/plugin configuration and actual shared-Qt-settings
isolation verification; this executable check alone does not establish either.

Final 1x VLT `f39765f5a97a`, 2x VLT `56f77cce425a` and helper
`c579c3fd6b43` passed targeted native tests in separate private instances.
Both framed bars revealed above playback and operated pause/resume, seek
dragging and volume. Framed maximize filled 1920x1080 and restored the original
708x440 / 1416x880 rectangles. Double-click entered/exited native borderless
fullscreen at both scales; each native fullscreen bar revealed and paused video.
Final 1x also passed stop, idle-bar display and manual hide. The first stop hit
had no effect; a clear second hit stopped playback. Earlier scratch-build tests
established hover hold/hide and native fullscreen resume/zoom exit separately.

All five original effects produced positive helper-process audio energy at
both scales. Every positive final-session reading was unmuted at volume 1.
The 2x initial intro and both intro replays were measured; initial 1x startup
was sampled too late to assess. Information/logo intervals contain unavailable
meter reads, so these results do not prove uninterrupted waveform playback or
physical speaker audibility. Exact sanitized findings and hashes are recorded
in [effects-hover-review.json](effects-hover-review.json).

User-running VLC processes and active skin-profile files were preserved. Only
the generated clip's shared Qt resume time changed during testing; the exact
pre-test Qt bytes were restored after owned test players closed. The current
running 1x session was not reloaded or redeployed.

Wheel routing over the helper-positioned framed bar remains incorrect because
VLC retains its original internal coordinates. Click and drag controls passed.
Queue progression, every palette/state, multi-monitor behavior and user
listening/visual acceptance remain outside this targeted pass. Complete 100%
visual and interactive parity is not certified.

Official VLC 3.0.23 sources: [FscWindow](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/fsc_window.cpp),
[builder](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/parser/builder.cpp),
[interpreter](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/parser/interpreter.cpp),
[Win32 windows](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/win32/win32_window.cpp).
Context7 returned legacy skin/Lua examples rather than the current Skins2
sound/hover command surface; the pinned source and vendored DTD govern this work.
