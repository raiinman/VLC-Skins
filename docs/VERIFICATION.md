# Verification evidence — 2026-10-15

Latest candidate: offline verified only. No VLC launches, desktop input, installed-skin changes or profile edits were performed in this background pass. Exact candidate hashes are in `offline-review.json`; prior native records keep their original package hashes.

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

Reversed volume sprites now agree with native minimum/maximum values. Playlist scrollbar points match VLC's descending scroll variable. The EQ uses its smooth original corner, metadata uses all original palette colors, and the clock is more legible. Closing preserves the interior during travel and covers it only at the endpoint; a clock click preserves the closing destination. Transparent source resize rectangles now receive input through alpha 1 hit masks. Pixel and binding contracts guard both scales.

At 2x, 16 bands per short shutter sequence created up to 49 active timers and 980 callbacks/second. Two bands reduce closing to seven timers while retaining every pixel. Dynamic text is visible only in its owning main layout; inactive copies no longer rasterize on each time update. The previous native candidate's initialization timings and hashes are in load-benchmark.json. The animation sequence is preserved; precise wall-clock pacing remains a review item.

Native paused seeking can leave clock text stale until resume. Upstream StreamTime notifies before setting the input position, and an identical subsequent percentage suppresses another notification. Changing clock mode during shutter travel also activates a layout, which can finish opening early or restart closing. These limits are recorded rather than claimed fixed.

## Background source review

The original GIF has opaque magenta pixels but its WMS container declares magenta transparency. The converter previously enlarged GIF frames before the native color key removed those pixels, introducing colored edge pixels at 2x. `color_key` now applies the original key before fades and per-frame resampling, consistent with the static source artwork.

- `check_startup.py`: all 81 intro and 81 lighting frames at each scale match independently decoded, keyed source pixels and source fade timing. The test failed at the first GIF frame on the previous assets and passes after correction.
- `check_source_art.py`: 176 used source images, 920 original hover/pressed bindings, 12 menu-state crops and three EQ power crops per scale pass. In-memory pixel and wrong-hover-binding mutations were rejected.
- `check_panels.py`: 336 palette/size/checkbox combinations and 1,134 panel button-ownership checks and 980 slider-access samples per scale pass. Resize handles remain attached and viewport margins remain constant at base, enlarged and maximum sizes. Obstruction and detached-anchor mutations were rejected. This is an offline geometry model.

The startup contact sheet renders corrected assets over a neutral background. It does not establish native playback, wall-clock timing or visual acceptance. Native load/performance and final desktop checks remain pending for this candidate.

## Offline transition, placement and launcher audit

- `check_transitions.py`: 44 source door/light frames and 56 main states per scale pass. Static shutter feedback sits below a two-frame 2 fps gate whose first frame has an alpha-1 mask and whose final frame is empty. Identical hover/down fallbacks prevent mouse-leave animation resets. The gate releases after 500 ms; it does not replace the original travel animation. An in-memory animated-idle mutation was rejected.
- `check_placement.py`: five fresh windows and 971 critical control instances per scale pass. Defaults fit 1280×720 at 1x and 1920×1040 at 2x, including the video window and information close control. An in-memory offscreen-window mutation was rejected. These checks allow overlap and do not modify saved layouts.
- `check_panels.py`: resized slider access includes the nested playlist scrollbar and native Bezier endpoint scaling at minimum, enlarged and maximum sizes. This supplements button ownership and anchor checks.
- `check_launchers.py`: both isolated INI writers pass exact UTF-8 reset-content checks using Unicode, ampersand and apostrophe paths, and report write failure. Static checks require missing-skin and write-error guards before `start`. Only extracted writers ran against private fixtures; neither CMD launcher nor VLC ran. Upstream ThemeRepository bridges `--skins2-last` into configuration, so historical benchmark skin selection remains valid. The corrected reset concerns `skins2-config`, which Theme reads from configuration.

Independent read-only review found no concrete regressions in the final gate, placement or launcher changes. Installed skins, user profiles and running VLC instances were left untouched. Native end-to-end launch, hover/input timing, embedded video and final visual acceptance remain pending. Closest DOX contracts were updated; existing ownership and child indexes remain valid.
