# Verification evidence — 2026-10-15

The current loading fix passes native initialization: **1x8.27s /517.8MiB**,
**2x28.27s /1807.2MiB**, both within the existing30-second budget. Exact hashes,
private-desktop setup and preservation results are in fast-load-benchmark.json.
All17 conversion/visual checks passed:714exact cases,42documented closed-main
residuals,zero unexplained. fast-loading-equivalence.json checks actual-package
RGBA/transparency/timing/control equality including the targeted2-to4Info rail
reband. Allocation is reported separately, not used to weaken parity checks.
Both user-library packages were installed with verified backups; ProgramFiles
writes were denied and those copies remain unchanged. Installation/live rollout
are separately scoped in fresh-skin-install.json and FAST-LOADING.md. Loading
proof does not certify all native visual/audio behavior or user acceptance.
The companion fresh1x restart is complete: matching source/helper/OSD,158-item
queue/order/selection,paused2sec,volume and geometry retained;720p nativeAVdecode
passed. Exact scoped proof is in fresh-1x-rollout.json; native pointer hover and
visual OSD appearance remain pending.

## Historical candidates


The storage-optimized exact packages now have loading-only native evidence in `storage-load-benchmark.json` and `LOADING-AND-MEMORY.md`: 1x 16.48 s / 347.1 MiB, 2x 38.38 s / 1130.3 MiB. Memory decreased, but initialization regressed and 2x FAILS the existing 30-second budget. Both requested themes loaded without logged errors/fallback and survived startup. Protected companion/player/helper creation identities, all 16 guarded paths (11 existing) and input desktop were preserved, and owned tests closed. One warm-cache run per scale does not establish cold-start performance, visual controls, animation smoothness or audio. The prior exact-hash benchmarks below remain unchanged.

`storage-optimization-review.json` separately verifies complete RGBA/timing equality for 394/434 packaged resources, all other payloads/XML and active paint/control order for 54 Info routes plus no-route. All 17 conversion/visual checks pass; Info checks include 590 endpoint controls and 20 rejected mutations per scale. Offline allocation estimates remain distinct from measured process working sets. A passing graphics-equivalence check does not override the failed initialization gate.

Pre-optimization Info/playlist package initialization is recorded separately in `info-load-benchmark.json`: 1x 8.27 seconds and 2x 29.55 seconds against the existing 30-second budget. Both survived startup without logged theme errors or fallback. The benchmark used copied portable runtimes, fresh configs, silent dummy audio and private non-input desktops. PID-owned TCP connections queried CLI autoplay readiness; no commands started playback. Both owned test players exited; the running 1x VLC/helper retained their creation identities and stayed alive, the input desktop stayed unchanged, and all 10 guarded paths (5 existing) retained their hashes. No mouse/keyboard/focus control or effects helper was used. This is one warm-cache run per scale with concurrent workload; 2x has little budget margin and used about 1.76 GiB working memory. This establishes initialization only, not native animation smoothness, hover controls, tooltip stacking or audibility. Historical `load-benchmark.json` remains unchanged.

The subsequent Info/tooltip/playlist candidate is scoped in `info-fades-review.json`. Source-pixel/route checks cover54 Info states and590 endpoint button checks per scale, with16 rejected mutations. Helper pure tests cover18 tooltip identity/placement cases without native calls. Playlist customization fixture tests prove only font digits change, with all other XML/assets/actions preserved; hash/scale mismatches fall back safely. Larger playlist/tooltip fonts and native resize geometry are checked separately. Current initialization measurements are recorded above; native transition scheduling, tooltip placement/stacking and customization UI remain pending. Other native evidence below retains its older recorded hashes.

The preceding compact-only candidate has offline checks only; its exact VLT/helper/OSD hashes and limits are recorded in `compact-review.json`. Both scales pass original small-button art, fixed strip geometry, volume-state actions, filename contrast and visibility, packaged XML and mutation checks. Lua 5.1/5.2 mocks pass 20 OSD cases and four rejected mutations. The helper compiles and passes pure tests; private-launcher migration and runtime trust fixtures pass without launching VLC. Native opacity, hover expansion, text scrolling and dial OSD remain unverified. No installed skins, active profiles or running processes were changed. All native evidence below belongs to its recorded older builds.

Subsequent helper `0e1186bac215` adds only scoped trusted portable-executable validation. Compilation, pure identity tests and `tools/check_runtime.ps1` pass, including rejection of altered bytes, wrong process path/start time, noninstalled reference, relative path and missing portable directory. These tests launch no VLC, desktop or audio APIs. Native portable launch, dependency loading and shared-settings isolation are verified separately by the companion; the recorded sound/hover native evidence below remains bound to helper `c579c3fd6b43`.

The latest sound/hover candidate passes offline checks and targeted native tests at both scales. `effects-hover-review.json` records exact hashes, process-scoped audio-meter findings, actual framed/native fullscreen control tests and remaining gaps. Both scales passed pause/resume, seek dragging, volume adjustment, framed maximize/restore and borderless double-click entry/exit. All five effects produced unmuted helper-session output. This establishes stream energy, not physical speaker audibility or exhaustive parity. User-running 1x sessions were preserved; separately owned test players were closed.

`check_effects.py` passes 1,076 source-derived signal bindings per scale, exact original WAV bytes in generated and packaged files, reset layouts and manifest geometry. `check_hover.py` passes original-art comparisons, 28 palette/play states per scale, transport/slider access and 12 rejected mutations. Native testing found and corrected a playback stacking defect; final candidates remained above video. The helper-positioned bar disables frame dragging to avoid stale native coordinates. Mouse-wheel routing over that bar remains open; click/drag controls work. Earlier native reports retain only their original package scope.

## Automated checks

- `python tools/build.py --check`: both scales validate against the official VLC 3.0.x DTD; IDs, resource references and functional button actions pass.
- `python tools/check_contracts.py`: both scales pass exact atlas-versus-unpacked pixels, original main-button coordinates, 56 clock/shutter/palette states plus startup, layout action ownership, single video/playlist/EQ instances, independent 2x needle-frame resampling, animation metadata, endpoint assets, remaining-time dash and static shutter idle/hover/pressed masks.
- `python tools/check_hits.py`: both scales pass 856 functional main-control instances. Coverage is 490,995 pixels at 1x and 1,957,753 at 2x, after excluding only physical overlaps between verified source outer buttons. Invisible hit rectangles remain potential obstructions. This is an offline model of the final XML/pixels, not native mouse QA.
- Mutation checks: a deliberately incorrect elapsed/remaining clock transition failed the contract suite; a painted black obstruction over Next failed the hit suite. XML was restored after each mutation; delivered VLTs were not modified by these tests.
- A displaced animation-band manifest entry failed the exact reconstruction guard; the manifest was restored afterward.
- `python tools/check_animation_bands.py`: native animation masks stay within 4,096 pixels in height. Reassembling their bands reproduces every canonical RGBA frame exactly, with matching fps/loops, source placement and actions. The guard failed before band generation existed.
- Python compilation and `git diff --check` passed. The existing preview is an asset rendering; it is not evidence of the new native behavior.

## Native VLC 3.0.23

Both scales of the prior parity candidate loaded and played a generated silent 640×360 MPEG-4/AAC clip through VLC's loopback RC interface. The reference is 90 seconds long. Native playback statistics and exact candidate hashes are recorded in `runtime-summary.json`; they prove theme load and player operation, not skin button interaction. The previous native-tested banded packages have exact hashes and silent-WAV initialization checks in `load-benchmark.json`; those measurements do not apply to the subsequent offline candidate.

Native Computer Use now reaches skin controls through an isolated floating Direct3D output window. Mouse clicks and drags were checked against independent read-only HTTP values: play/pause, volume endpoints, seeking, playlist selection/scrolling and EQ enable/band/preamp at both scales; next/previous, shuffle/repeat and Open Media at 1x. Native views showed shutter travel/endpoints, selected palettes, clock-mode changes, original Story/Screenshots navigation and credits. The final 2x resize grip increased playlist height from 640 to 665 pixels. The final 1x package loaded and displayed its clock; the tool then failed with `foreground window did not report a process id`, including recovery, before the final resize recheck.

[native-gui-review.json](native-gui-review.json) separates intermediate functional reviews from final-package checks and records sanitized observations. These tests use `--no-skinned-video` as an automation anchor, so they do not establish embedded video placement. Earlier fullscreen/Escape testing showed the complete 16:9 reference. No desktop captures or credentials are included in this repository or bundle.

The expanded theme originally exposed a VLC 3.0.x generated-ID truncation defect after the counter exceeded 999. Source and test crash-dump evidence traced the pure-virtual-call crash to colliding control IDs. Explicit unique IDs on every generated control resolved the load crash; repeat native loads succeeded.

Native logs include first-run missing isolated config files and a failed search in the user's optional font directory before the packaged font loads. They contain no unknown action/variable, invalid tooltip font, malformed theme or pure-virtual-call diagnostics in the successful tests.

## Review findings resolved

A separate read-only reviewer found two defects. Shutter hover/pressed states restarted transparent lead-in animations, potentially cancelling clicks; both states now use static original artwork and regression tests. The hit test also discarded arbitrary painted obstructions; exclusions are now restricted to verified source outer-button overlaps and an obstruction mutation is rejected.

## Practical limits

The user confirmed that 2x eventually appeared after minutes. Upstream Win32Graphics builds masks by repeatedly combining opaque pixel runs. Horizontal bands retain animation pixels/timing while reducing that work. The native benchmark now measures CLI autoplay after interface initialization, using a silent WAV; RC commands never start playback. Windows file-log buffering made the first log-poll timing unreliable. The corrected benchmark checks flushed theme diagnostics after shutdown and requires both scales to initialize within 30 seconds and remain alive through startup. Final timings and package hashes are in `load-benchmark.json`. Cross-machine performance remains unverified.

Exhaustive hover/pressed coverage, exact wall-clock animation timing, final 1x resize, EQ listening and embedded video placement/resize still need hands-on review. WMP-only feature removals and other permitted adaptations are listed in PARITY.md. Complete parity remains a user acceptance decision.

Regular VLC launches can restore a layout without the intro. Review launchers now reset it through their isolated INI (native end-to-end confirmation pending); the conversion credit page provides Replay intro. The automatic WMP on-load timer has no direct skin-only equivalent.

## Native parity fixes in this pass

Reversed volume sprites now agree with native minimum/maximum values. Playlist scrollbar points match VLC's descending scroll variable. The EQ uses its smooth original corner, metadata uses all original palette colors, and the clock is more legible. Closing preserves the interior during travel and covers it only at the endpoint; a clock click preserves the closing destination. That earlier package used alpha-1 black resize masks; a later user screenshot exposed their cached-image painting defect, corrected in CORNER-FIX.md. Pixel and binding contracts guard both scales.

At 2x, 16 bands per short shutter sequence created up to 49 active timers and 980 callbacks/second. Two bands reduce closing to seven timers while retaining every pixel. Dynamic text is visible only in its owning main layout; inactive copies no longer rasterize on each time update. The previous native candidate's initialization timings and hashes are in load-benchmark.json. The animation sequence is preserved; precise wall-clock pacing remains a review item.

Native paused seeking can leave clock text stale until resume. Upstream StreamTime notifies before setting the input position, and an identical subsequent percentage suppresses another notification. Changing clock mode during shutter travel also activates a layout, which can finish opening early or restart closing. These limits are recorded rather than claimed fixed.

## Background source review

The original GIF has opaque magenta pixels but its WMS container declares magenta transparency. The converter previously enlarged GIF frames before the native color key removed those pixels, introducing colored edge pixels at 2x. `color_key` now applies the original key before fades and per-frame resampling, consistent with the static source artwork.

- `check_startup.py`: all 81 intro and 81 lighting frames at each scale match independently decoded, keyed source pixels and source fade timing. The test failed at the first GIF frame on the previous assets and passes after correction.
- `check_source_art.py`: 177 used source images, 920 original hover/pressed bindings, 12 menu-state crops and three EQ power crops per scale pass. In-memory pixel and wrong-hover-binding mutations were rejected.
- `check_panels.py`: 336 palette/size/checkbox combinations and 1,134 panel button-ownership checks and 980 slider-access samples per scale pass. Resize handles remain attached and viewport margins remain constant at base, enlarged and maximum sizes. Obstruction and detached-anchor mutations were rejected. This is an offline geometry model.

The startup contact sheet renders corrected assets over a neutral background. It does not establish native playback, wall-clock timing or visual acceptance. Native load/performance and final desktop checks remain pending for this candidate.

## Offline transition, placement and launcher audit

- `check_transitions.py`: 44 source door/light frames and 56 main states per scale pass. Static shutter feedback sits below a two-frame 2 fps gate whose first frame has an alpha-1 mask and whose final frame is empty. Identical hover/down fallbacks prevent mouse-leave animation resets. The gate releases after 500 ms; it does not replace the original travel animation. An in-memory animated-idle mutation was rejected.
- `check_placement.py`: five fresh windows and 971 critical control instances per scale pass. Defaults fit 1280×720 at 1x and 1920×1040 at 2x, including the video window and information close control. An in-memory offscreen-window mutation was rejected. These checks allow overlap and do not modify saved layouts.
- `check_panels.py`: resized slider access includes the nested playlist scrollbar and native Bezier endpoint scaling at minimum, enlarged and maximum sizes. This supplements button ownership and anchor checks.
- `check_launchers.py`: both isolated INI writers pass exact UTF-8 reset-content checks using Unicode, ampersand and apostrophe paths, and report write failure. Static checks require missing-skin and write-error guards before `start`. Only extracted writers ran against private fixtures; neither CMD launcher nor VLC ran. Upstream ThemeRepository bridges `--skins2-last` into configuration, so historical benchmark skin selection remains valid. The corrected reset concerns `skins2-config`, which Theme reads from configuration.

Independent read-only review found no concrete regressions in the final gate, placement or launcher changes. Installed skins, user profiles and running VLC instances were left untouched. Native end-to-end launch, hover/input timing, embedded video and final visual acceptance remain pending. Closest DOX contracts were updated; existing ownership and child indexes remain valid.

## Offline video sizing and visual comparisons

`python tools/check_video.py` passes at both scales. Explicit `autoresize=false` prevents media-driven layout growth in VLC's source path. Five manual sizes include tall/narrow and wide/short extremes; all retain frame insets and clearance from every feedback state of retained buttons. The packaged theme XML must match the audited generated XML after XML normalization. In-memory omitted/true autoresize mutations are rejected. This is source and geometry evidence; no VLC launch or native aspect-fit/fullscreen test occurred.

`python tools/compare_layers.py` reconstructs retained original WMS layers independently and compares generated XML compositions at both scales. Source, converted and highlighted residual sheets are asset renders. The report lists omitted dynamic text/font adaptations, conversion additions, assumed feedback states and remaining renderer limitations. Residual counts must be interpreted with that scope; they are not a parity percentage or native visual proof.

All pre-existing offline checks pass after rebuilding the video change. Installed skins, user profiles, running VLC and desktop input remain untouched. Nearest DOX contracts were updated; the root contract and child ownership/index remain unchanged because the audit adds no new ownership boundary.

The visual pass found and corrected missing source parent idle-image backings for close/zoom buttons, the video's single-recess header (now the original two-recess asset), and the Web Destinations static link overlay. Menu filtering at 2x now resamples full state artwork before clipping to the nearest-neighbor scaled source map. Microsoft documentation corrected an initial reference assumption: absent showBackground means only mapped regions are drawn, so no full-menu background was added.

The final visual report contains 756 cases: 714 exact reconstructed compositions and 42 closed-main cases with localized shutter/outer-control layer-order differences. A second reference applying only the documented functional layer raise reproduces those 42 exactly; no blanket residual mask is used. Residual self-checks ignore invisible RGB while detecting visible-pixel and shifted-layer mutations. Full-resolution and overview sheets show source, conversion and residuals. These counts exclude dynamic text/clock/font adaptations and added credits, and do not cover complete resized playlist/EQ/video composites or native playback. No overall percentage parity is inferred.

## Lower-right corner correction

The user screenshot shows a black resize-sized rectangle covering the lower-right pane corner. Source tracing found that CtrlImage renders into a separate graphics cache; Win32Graphics copies cached RGB onto the layout using masked BitBlt/SRCCOPY. An alpha-1 black bitmap is therefore not a transparent layout overlay. Previous input-layer checks established resize access but missed this painting behavior.

Both scales now use exact native-scale corner crops for all seven palettes, selected by active main palette and anchored to the lower right. The original visible grip and transparent outside edge are retained. check_corners.py rejects the old mask, verifies 70 palette/pane/size combinations per scale, checks packaged assets, and proves unchanged corner pixels under an explicitly bounded black-cache copy model. It does not launch VLC or prove final Windows appearance. The independent review found no concrete regressions.

The blue resize_hit resource name remains compatible with existing derived pane builders, including the YouTube prototype. Their old embedded copies do not change automatically; regenerate them from a corrected VLT and reload later. A derived builder that uses only the blue alias does not automatically inherit the canonical seven-palette selection. No helper source, installed skin, profile, running process or desktop input was changed in this fix. Root ownership and its child index are unchanged; nearest DOX contracts were updated.

## Shutter isolation retest

The initial native shutter open/close test reproduced rectangular frame cutouts on the video pane. Pane palette expressions depended on main layout activity; TopWindow deactivates the old layout before activating the new one. That transient all-false state hid and repainted every auxiliary frame.

Current pane visibility depends on a separate hidden palette state. Shutter and clock actions leave it untouched; only color cycling and intro replay change it. check_palette.py passes all 56 main states per scale through the inactive gap, plus 57 saved-color migration cases with byte-preservation/backup/idempotence checks. All earlier offline checks and twelve YouTube adapter tests pass. The adapter inherits source pane visibility and synchronizes saved palette state during private configuration generation.

The corrected private companion was launched and its 1x blue shutter clicked closed and open. Mid-animation observations in both directions and the closed endpoint showed intact YouTube/video pane borders, with no reproduced cutouts. This establishes the preceding build's limited live retest, not exhaustive timing, every pane/color, 2x shutter behavior, or video decoding. No desktop captures or browser content are stored. Standalone test windows were not exposed by the desktop tool, so those owned test processes were stopped and the existing companion's discovery support was used.

## Framed fullscreen candidate

Both scales pass the full required offline suite. Fullscreen controls use stateful video-only maximize/restore with original feedback in both states. Video geometry passes 10 sizes at 1x / 9 at 2x, including monitor-size bounds and the 8192x4320 maximum. Panel ownership checks pass with full 8K rasters. Source checks verify 14 opaque header/idle composites per scale; mutations reject bad pixels, alpha, palette, order, feedback and per-pixel mosaic fills. Companion preparation passes 12 adapter tests, its self-test, bridge-click checks, full DTD/CRC and all 58 inherited framed toggle bindings. Final targeted native tests passed at both scales on a 1920x1080 monitor in blue: idle/playing framed maximize/restore, borderless double-click both directions, and stopped-header appearance. Saved settings verify exact restored pane rectangles. Temporary companion profile/positions were restored and only the corrected normal 1x derived copy was redeployed. See fullscreen-review.json and VIDEO-REPAINT.md; older native evidence is version-specific.
