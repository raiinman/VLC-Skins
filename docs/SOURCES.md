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

Context7 was not available among the session's callable tools. VLC-specific implementation details were checked against the official authoring reference and upstream source instead.
