# tools

## Purpose
Reproducible WMZ extraction, conversion and packaging.

## Ownership
This subtree.

## Local Contracts
Accept only safe archive paths. Validate CRC after the documented four-byte header repair. Validate generated XML against the official VLC DTD.

## Work Guidance
Follow the root visual parity contract.

## Verification
Run python tools/build.py --check, python tools/check_contracts.py, python tools/check_hits.py, python tools/check_animation_bands.py, python tools/check_startup.py, python tools/check_source_art.py, python tools/check_panels.py, python tools/check_transitions.py, python tools/check_placement.py, python tools/check_launchers.py, python tools/check_video.py python tools/check_corners.py and python tools/check_palette.py after conversion changes. Run python tools/compare_layers.py for a combined-layer visual audit; residuals are review findings, not an automatic parity certification.

## Child DOX Index
None.

Sound/hover support: skin_support.py adds exact source WAVs and source-derived click signals, preserving media actions. Signals switch already-visible offscreen windows between unique ready/trigger layouts; never use Window.show()/hide() for routine sound events, because Win32 SW_SHOW can activate them. Framed hover similarly switches between an original-art open layout and a fully transparent closed layout. Native fullscreenController remains VLC-owned. check_effects.py and check_hover.py independently validate assets, signals, action preservation, geometry, hit access and rejected mutations. Run both with the conversion suite.

SkinEffects.cs is an optional .NET Framework product runtime, scoped to an explicit installed VLC PID plus start time. It owns no global input hooks, media playlist changes, focus changes or VLC termination. Commands target only dedicated native command images, never pointer/keyboard injection. Build with build_effects.ps1; --self-test checks pure decisions and --check-skin validates/extracts a VLT without audio or desktop APIs. Native audibility/hover/stacking claims require separate observed tests. Start-NFS.ps1 uses per-scale private APPDATA/config and refuses a second launch of its still-running profile; -SelfTest touches no user profile or process.


Build ownership: build.py recovers inputs, packs lossless atlases and packages both scales; assets.py reads standalone/atlas frames; check_contracts.py validates original pixels, state transitions, source timing and explicit control IDs; check_hits.py models input layers offline; preview.py makes an explicitly asset-rendered comparison.

Assign explicit unique IDs to every control: VLC 3.0.x synthetic IDs collide past 999. All shutter button feedback stays static because changing a button state restarts its animation. A separate top-layer two-frame gate uses identical state fallbacks and releases its alpha-1 hit mask after 500 ms. Exclude only overlaps between verified original outer buttons from hit coverage; arbitrary painted obstructions must fail.

Native animation strips taller than 4096 pixels become horizontal bands. Canonical PNGs and animation-bands.json are offline references; VLC loads only physical bands. check_animation_bands.py checks exact reconstruction, timing, placement and actions. benchmark_load.py measures CLI autoplay after the skins2 interface is ready; both scales must initialize within 30 seconds on the test machine. RC-triggered playback and buffered file-log timing cannot establish initialization time.

Short 11-frame sequences use two bands when splitting is required; the 81-frame intro uses 16. Each band adds a native timer and repaint, so do not increase the count without runtime evidence. Main dynamic Text visibility follows its owning layout.isActive, including startup after cloning. Both volume and seek sprite order runs minimum to maximum. Resize handles repeat exact output-scale palette corner pixels; never use faint black hit masks, because Windows CtrlImage copies cached RGB onto the layout. Closing layouts retain the interior during travel, then cover it with exact native-scale closed pixels; clock toggles must retain the closing destination.

Apply the WMS exact magenta transparency key before resampling or fading GIF frames. check_startup.py independently compares every startup/light frame to source pixels and timings; check_source_art.py checks original artwork and hover/pressed bindings; check_panels.py checks panel button ownership, resize attachment and viewport margins offline. Native benchmarking launches VLC and is excluded from background-only work.

check_transitions.py compares source shutter/light frames and non-restarting transition gates. check_placement.py checks fresh defaults against 1280x720 at 1x and 1920x1040 at 2x; desktop placement is independent of artwork scale. check_panels.py includes resized slider access. check_launchers.py executes only the extracted isolated INI writer against private fixtures; never run review launchers during offline work.

check_video.py requires explicit Video.autoresize=false, compares packaged XML with audited geometry, and checks manual resize extremes. compare_layers.py composes retained WMS and VLC layers independently, writes source/converted/residual sheets and visual-comparison.json; disclose omitted dynamic text, conversion additions and renderer limitations.

check_video.py also guards reversible framed maximize actions, original feedback in both Checkbox states, and monitor-sized geometry. Maximize only video: VLC 3.0.23 shares one restore rectangle across skin windows. Never replace stateful toggles with unconditional maximize or cover Video with a double-click overlay.

Uniform screen_black fills must use resize=scale. A 1px mosaic causes one native GDI copy per output pixel and can stall idle/header repaint. Keep textured frame rails tiled; pixel-equivalence tests alone do not detect this performance defect.

Information-menu sprites resample full source artwork before clipping with a nearest-neighbor output-scale mapping mask. WMP BUTTONGROUP.showBackground defaults false: retain only mapped regions. Preserve original parent close/zoom image backings and the static Web Destinations overlay; its obsolete outbound actions remain omitted. Video backings use opaque palette-matched header/idle composites to avoid partial-alpha cached RGB fringes. Scale full source header and idle images before cropping/compositing; independently verify exact pixels, opacity, palette selection and draw order.

check_corners.py compares real-art resize patches with independently decoded native-scale source crops and models Windows cached RGB copy. Alpha-based hit checks do not establish paint transparency. Keep the resize_hit resource as a blue-corner compatibility alias for existing derived panes; other palettes use their matching conditional images.

Palette visibility uses an independent hidden palette_state window with seven 1x1 transparent layouts. Only color cycling and intro replay may switch it; shutter/clock actions must never reselect even the same palette layout. check_palette.py models the all-main-inactive gap. migrate_palette.py migrates only an explicitly selected closed profile, derives palette from saved main layout, makes a backup and preserves other bytes. Never migrate a live profile.
