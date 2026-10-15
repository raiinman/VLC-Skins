# skins

## Purpose
Skin source and generated VLC themes.

## Ownership
This subtree.

## Local Contracts
Preserve original asset pixels and author attribution; record intentional changes. Generated files come from tools/build.py.

## Work Guidance
Follow the root visual parity contract.

## Verification
Run python tools/build.py --check, python tools/check_contracts.py, python tools/check_hits.py, python tools/check_animation_bands.py, python tools/check_startup.py, python tools/check_source_art.py, python tools/check_panels.py, python tools/check_transitions.py, python tools/check_placement.py, python tools/check_launchers.py, python tools/check_video.py python tools/check_corners.py and python tools/check_palette.py after conversion changes. Run python tools/compare_layers.py for a combined-layer visual audit; residuals are review findings, not an automatic parity certification.

## Child DOX Index
None.


Original resources are under need-for-speed-underground/original; provenance.json records all 247 members and their CRCs. vlc-1x and vlc-2x are generated.

Generated themes contain explicit control IDs and lossless atlases. Canonical animation strips remain offline references; animation-bands.json maps them to lossless native bands that bound Windows mask-construction cost. Preserve pixels, frame counts, fps and loops.

Keep the credit-page intro replay action and reset-layout review launchers: VLC may restore another layout on normal launch and bypass the initial intro.

Preserve source metadata palette colors and the smooth EQ bottom corner. Closing endpoint patches are composed at the output scale, contain no translucent replacement pixels, and leave the source shutter edges intact. The 14-pixel source-scale clock font is an allowed readability adaptation.

Keep default desktop positions inside the declared work areas without scaling them blindly with artwork. Existing saved VLC positions are not migrated. Shutter travel uses a separate 500 ms input gate over static original button feedback.

The video viewport uses autoresize=false: media dimensions cannot enlarge the parent layout. Retain rightbottom stretch anchors and the manual resize corner. Do not infer native aspect fit or automatic window display from this policy.

Panel close buttons and video zoom retain their original parent idle-image backings. Video uses the original eq_top_right two-button header. Web Destinations keeps c_link_no.jpg at (127,118) source coordinates, without obsolete outbound actions. Menu-region masks stay crisp at output scale; full artwork is filtered before cropping.

Controller fullscreen and video zoom are stateful Checkboxes bound to video.isMaximized. Keep original normal/hover/pressed artwork in both states; use video.maximize()/unmaximize() only for the video pane. Native maximize fills the current monitor with the existing skin frame; allow up to 8192x4320. Leave video mouse input unobstructed for native borderless fullscreen on double-click.

Resizable panes use seven conditional corner patches at (width-36,height-24), with rightbottom anchors. Crop (128,33)-(151,57) from each complete f_bot_right bitmap after output scaling. Preserve the source alpha shape and visible grip; fully transparent pixels remain outside the hit region.

All auxiliary frame/corner visibility uses palette_N.isActive, independent of main shutter/clock layouts. The palette_state window is always hidden and defaults to blue. It adds no visible pane or native playback widget. Legacy saved colored layouts require matching hidden state migration before loading; new state is saved by VLC afterward.
