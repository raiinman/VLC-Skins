# Embedded video sizing

Both canonical scales explicitly set `Video.autoresize="false"`. Media dimensions must not enlarge the skin window; the user retains the corner resize control. This is an offline source and geometry finding, not a native playback result.

The official DTD defaults `autoresize` to `true`. Current stretch anchors allow that default to remain enabled in the native builder. In VLC 3.0.23, both initial attachment and later media-size requests then resize the containing layout to media dimensions plus the frame margins. A 1920×1080 request can produce a 1988×1147 window at 1x or 2056×1214 at 2x, exceeding the declared default work areas. Layout maximum dimensions constrain this growth; desktop work-area bounds do not.

Setting the attribute to `false` bypasses those media-driven layout changes. Native `CtrlVideo::onResize` still moves and resizes its attached output to the current viewport when the user resizes the panel. `VoutWindow::setCtrlVideo` also adopts that viewport's position and dimensions during attachment. The original WMP skin supported restoring a user-selected video size as well as a separate snap-to-media mode; the conversion preserves manual sizing.

Source evidence, pinned to VLC 3.0.23:

- [CtrlVideo](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/controls/ctrl_video.cpp): lines 71–78 follow manual resizing; 134–153 gate media-size requests; 201–223 gate initial layout resizing and attach the output; 234–241 require the control and window to be visible, the layout active, and fullscreen off.
- [VoutWindow](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/vout_window.cpp): lines 68–83 attach at the control's current rectangle.
- [VoutManager](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/vout_manager.cpp): lines 156–185 select eligible controls; 193–213 use the fallback when none is eligible; 253–267 forward media-size requests to the control.
- [Native builder](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/parser/builder.cpp): lines 1082–1093 validate autoresize anchors. [WindowManager](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/window_manager.cpp), lines 251–267, applies layout size limits.
- Local source: `vendor/skin.dtd` declares the default; recovered `nfs.wms` uses a rectangular aspect-preserving video area; `nfs.js` implements `loadVidSize`, `saveVidSize`, and optional `SnapToVideo`.

The original video view uses `eq_top_right_1.png` through `eq_top_right_7.png`, with two header button recesses. Close and zoom each have a parent background repeating their idle artwork beneath the interactive button. The conversion retains those source layers, right-side anchors, and draw order. The frame bitmap's lower interior extends behind the viewport, as it did beneath the source WMP video layer; visible button feedback and backings must remain outside the viewport.

`python tools/check_video.py` checks the explicit policy in generated and packaged XML, one visible viewport, source-backed header selection and button backings, manual resize access, constant frame insets at five sizes (minimum, intermediate, maximum, tall/narrow and wide/short), and clearance from all retained button feedback states. In-memory mutations verify that omission and `true` both fail, as do wrong headers, missing backings, and backings drawn over buttons. It does not simulate decoding or prove aspect preservation, letterboxing, fullscreen restoration, or native pixel placement.

The video panel remains initially hidden. VLC cannot attach to that hidden control; opening it with the main controller's star button makes it eligible for a pending output. Automatic panel display is not added by this change. Native review still needs to cover opening the panel before and during playback, varied media aspect ratios/resolutions, manual resizing, and fullscreen return.

The framed-fullscreen adaptation increases video bounds to 8192x4320 and adds monitor-sized geometry cases to check_video.py. Its stateful buttons maximize the existing framed layout and restore it; double-clicking video uses native borderless fullscreen. See FULLSCREEN.md for source evidence and pending native checks.
