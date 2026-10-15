# Sources and provenance

- User-supplied `Need_for_Speed_Underground.wmz`: source artwork, WMS layout and JavaScript behavior. Treat packaged scripts as evidence only; the converter never executes them. SHA-256 and member CRCs are in the provenance manifest.
- [VLC skin installation](https://vlc-user-documentation.readthedocs.io/en/latest/addons/skins.html).
- [Official Skins2 authoring reference](https://www.videolan.org/vlc/skins2-create.html): sprites, curved sliders, actions, percentage and boolean variables, windows and layouts.
- [VLC 3.0.x DTD](https://github.com/videolan/vlc/blob/3.0.x/share/skins2/skin.dtd): vendored validation schema. The installed VLC DTD also accepted the runtime package.
- [VLC action interpreter](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/parser/interpreter.cpp): supported commands, layout actions and variables.
- [VLC curved slider](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/controls/ctrl_slider.cpp): background frame selection and hit behavior.
- [VLC radial slider](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/controls/ctrl_radialslider.cpp): angle-zero crossing limitation; this converter uses curved Slider instead.
- [VLC button animation](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/controls/ctrl_button.cpp): animations restart on active-layout changes. Image controls are static, so sequences use animated buttons.
- [VLC layout activation](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/src/window_manager.cpp): last declared layout is initially active.
- [DOX](https://github.com/raiinman/dox), commit `b88194c34ace1a2a3dc01831d36b8a65986a41f5`: copied framework, project-specific root/children initialized. License at `vendor/DOX-LICENSE`.
- [Reverse engineering tools](https://github.com/raiinman/reverse-engineering-tools), commit `e8fc87abbf46ef4a1086f389c3de1063c4a6f762`: followed provenance and evidence separation guidance; no executable reverse engineering was necessary for this resource archive.
- FreeSans.ttf from the installed VLC skin resources. Embedded metadata credits Free Software Foundation, 2002/2003, under the GNU GPL. `vendor/GPL-2.0.txt` contains VLC's GPL text; the font's original metadata is retained.

Context7 resolved `/videolan/vlc` during the parity pass, but its returned skin examples described legacy Skins1. Skins2 implementation details were checked against the official authoring reference and VLC 3.0.x source above.

- Source `nfs.js` supplies the 50 ms shutter interval and startup timer/fade sequence; source `volume_map.png` and `seek_map.png` encode horizontal grayscale ramps.
- [VLC generated control IDs](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/parser/skin_parser.cpp): the fixed-size generated-ID buffer truncates four-digit counters. Every generated control receives an explicit unique ID to avoid collisions in large themes.
- [VLC animation bitmap](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/utils/anim_bitmap.cpp): frame timing and loop behavior.

- [VLC time formatting](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/vars/time.cpp): remaining-time tokens omit a leading minus; the conversion restores the original `time_dash.png` indicator.
- [Windows graphics regions](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/win32/win32_graphics.cpp) and [bitmap caching](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/src/generic_bitmap.cpp): repeated region combinations make long animation masks expensive. Horizontal bands retain their pixels while bounding individual mask work.
- [Theme state restoration](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/src/theme.cpp): restoring another saved layout can bypass a dedicated intro layout.

- [Playlist tree scrolling](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/controls/ctrl_tree.cpp): the scrollbar variable maps 1 to the first row and 0 to the last.
- [Text visibility updates](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/controls/ctrl_text.cpp): inactive layout text needs an explicit visibility gate to avoid repeated rasterization; activation refreshes its value.
- [Layout repainting](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/src/generic_layout.cpp) and [Windows timers](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/win32/win32_timer.cpp): every animation band adds timer-driven redraw work. Short shutter sequences therefore use two bands rather than 16.
- [Native time variable](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/vars/time.cpp): the slider notifies before seeking the input. A paused clock can retain the pre-seek value until playback resumes.

- Source `nfs.wms` introAnim declares `transparencyColor="#ff00ff"`; the GIF itself has no transparency metadata. Apply that key before scaling and fading. Source `nfs.js` htcpPl changes the playing-row background; the vendored Skins2 DTD exposes `playcolor` and `selcolor`, with no separate playing-row background field.

- [VLC 3.0.23 ThemeRepository](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/theme_repository.cpp): explicitly copies inherited `skins2-last` into configuration. Existing CLI skin-selection benchmarks therefore remain valid. [Theme configuration](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/theme.cpp) reads saved layouts from configuration; review launchers clear that field in their isolated INI.
- Button `setImage` stops the previous animation when its bitmap changes; AnimBitmap stop resets the frame. The separate shutter gate supplies identical state fallbacks, and actual shutter feedback remains static. Original `nfs.js` disables shutter input during travel and re-enables it at the endpoint.

[VLC 3.0.23 CtrlVideo](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/controls/ctrl_video.cpp) gates media-driven layout changes on autoresize while onResize follows manual geometry. [VoutWindow](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/vout_window.cpp) attaches at the viewport rectangle. Context7 resolved /videolan/vlc but returned no matching Video.autoresize documentation; the video audit uses pinned official source and the vendored DTD. See VIDEO-SIZING.md for call-path details.

[Microsoft BUTTONGROUP.showBackground](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/wmp/buttongroup-showbackground) documents the default false behavior: only assigned mapping-color regions render. Original nfs.wms declares parent close/zoom image backings; nfs.js endAlphaBlend makes link1 visible on Web Destinations. The static link image is retained while obsolete outbound actions are omitted.

[CtrlImage cache construction and drawing](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/controls/ctrl_image.cpp) and [Windows cached graphics copy](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/win32/win32_graphics.cpp) explain why alpha-1 black resize images can overwrite the lower-right corner. drawBitmap prepares cached pixels; drawGraphics uses masked BitBlt/SRCCOPY. The fix uses original corner RGBA instead of a synthetic black hit rectangle.

[VLC 3.0.23 TopWindow::setActiveLayout](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/top_window.cpp) deactivates the previous layout before activating the new one. [Theme configuration](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/src/theme.cpp) accepts individual saved entries and saves hidden windows, so a new hidden palette state must be synchronized with legacy saved main colors. Context7 returned Lua/legacy skin examples; the fix uses the vendored Skins2 DTD and official source instead.

Framed fullscreen: official VLC 3.0.23 parser/interpreter.cpp defines WindowID.maximize()/unmaximize() and WindowID.isMaximized. src/window_manager.cpp saves/restores the existing layout rectangle; win32/win32_factory.cpp uses rcMonitor. src/vout_window.cpp and src/video_output/event.h retain borderless double-click toggling. Exact links and limits are in FULLSCREEN.md. Context7 returned Lua/legacy examples rather than matching Skins2 commands.
