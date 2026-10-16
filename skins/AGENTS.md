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

Both generated archives also carry schema2 nfs-effects.json and the five unchanged source WAVs in sounds/. Sound actions switch their own offscreen ready/trigger layouts and retain the original playback action suffix, including compact_* aliases. The default intro trigger follows original startup delay. Compact fullscreenController and videoHoverController bars share original 1x control artwork at fixed physical360x64 /361x64 size in both scales, without another Video or duplicate title. The framed controller's transparent362x1 closed layout is last/default; runtime uses setLayout, never activating show/hide calls. A separate offscreen hover_volume_state selects71x19 collapsed /72x19 expanded layouts, collapsed last. Both XML click fallback and helper hover commands can expand volume. Helper-dependent features remain explicitly labeled and require native review.


Original resources are under need-for-speed-underground/original; provenance.json records all 247 members and their CRCs. vlc-1x and vlc-2x are generated.

Generated themes contain explicit control IDs and lossless atlases. Canonical animation strips remain offline references; animation-bands.json maps them to lossless native bands that bound Windows mask-construction cost. Preserve pixels, frame counts, fps and loops.

Batch eligible resources into atlases bounded by2048x4096; the former small-only cap regressed native loading. Runtime atlases use standard Pillow compressed PNGs with PNG entries ZIP_STORED; the custom filter0 writer is discarded. Preserve every RGBA pixel and all frame counts/fps/loops. Only the14 tall2x info_frame_[1-7]_[23] rails use four bands instead of two; their reconstructed15-frame20fps animation remains identical. Other band policies remain unchanged. Static live Info backings share one Image per identical page/geometry with mutually exclusive route OR visibility and unchanged active draw order. Preserve surviving explicit IDs. fast-loading-equivalence.json owns the actual-package comparison, including two/four-band reconstruction and mutation coverage. File size/memory are reported tradeoffs, not reduction gates. fast-load-benchmark.json records passing exact-hash native loading; keep its warm-run limits, installed-file evidence and companion live confirmation separate. Preserve the running1x setup until verified handoff. See docs/FAST-LOADING.md before packaging or rollout changes.

Keep the credit-page intro replay action and reset-layout review launchers: VLC may restore another layout on normal launch and bypass the initial intro.

Filename metadata uses white12x-scale FreeSans, scrolling=auto and focus=false over a177x16 dark backing at(62,117) source coordinates. It must not cover the volume sprite's final row116 or logo starting134. Preserve owning-layout text visibility and original closed-shutter interior. The14-pixel source-scale clock font is also an allowed readability adaptation. Preserve the smooth EQ bottom corner and exact native-scale opaque closing endpoint patches, leaving original shutter edges intact.

Keep default desktop positions inside the declared work areas without scaling them blindly with artwork. Existing saved VLC positions are not migrated. Shutter travel uses a separate 500 ms input gate over static original button feedback.

The video viewport uses autoresize=false: media dimensions cannot enlarge the parent layout. Retain rightbottom stretch anchors and the manual resize corner. Do not infer native aspect fit or automatic window display from this policy.

Video/playlist solid black Image backgrounds use resize=scale, preserving the same opaque black pixels with a cached native fill instead of per-pixel mosaic drawing. Textured artwork retains its original tiling.

Panel close buttons and video zoom retain their original parent idle-image backings. For video, flatten each idle backing onto its matching native-scale eq_top_right header crop before CtrlImage caching; keep original button feedback separate. Video uses the original two-button header. Web Destinations keeps c_link_no.jpg at (127,118) source coordinates, without obsolete outbound actions. Menu-region masks stay crisp at output scale; full artwork is filtered before cropping.

Controller fullscreen and video zoom are stateful Checkboxes bound to video.isMaximized. Keep original normal/hover/pressed artwork in both states; use video.maximize()/unmaximize() only for the video pane. Native maximize fills the current monitor with the existing skin frame; allow up to 8192x4320. Leave video mouse input unobstructed for native borderless fullscreen on double-click.

Resizable panes use seven conditional corner patches at (width-36,height-24), with rightbottom anchors. Crop (128,33)-(151,57) from each complete f_bot_right bitmap after output scaling. Preserve the source alpha shape and visible grip; fully transparent pixels remain outside the hit region.

All auxiliary frame/corner visibility uses palette_N.isActive, independent of main shutter/clock layouts. The palette_state window is always hidden and defaults to blue. It adds no visible pane or native playback widget. Legacy saved colored layouts require matching hidden state migration before loading; new state is saved by VLC afterward.

The live info_menu layout shares its frame while hidden info_page_state changes content. info_frame_state defaults idle and is triggered only by explicit color actions, never page/shutter/clock changes. Conditional sparse frame animations also require the matching palette. Preserve legacy static Info layout IDs and geometry. Native decorative Buttons use identical state resources and lossless9/11/15frame sequences; never use animated Images. Include generated info-fades.json. Tooltip font is16physicalpixels at both scales; larger text works in plain VLTs, but above-pointer placement requires the optional matching helper.

Playlist defaults are440x340sourcepixels with dedicated playlist font12x-scale and brighter#C9CDD4text. Preserve original red selection, frame/header buttons, single native Playtree, scrolling direction and native lower-right resize access. Never share its customizable font with other controls. Saved native geometry may override fresh defaults.

## Collection presentation

`skins/README.md` indexes actual skin families and uses its own collection-level `skins/readme-banner.png` with `skins/readme-banner-prompt.txt`. Do not reuse a single skin family's banner as the collection header; each family has a centered README with a linked section index, scale/download links, source attribution and verification links. Need for Speed Underground's generated decorative banner and brief live at `need-for-speed-underground/readme-banner.png` and `readme-banner-prompt.txt`, beside its README. Match banners to each skin's observed materials and palette. Keep these documentation assets outside `original/`, `vlc-1x/`, and `vlc-2x/`; they are not runtime skin artwork or build outputs.
