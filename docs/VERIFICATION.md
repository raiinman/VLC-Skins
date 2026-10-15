# Verification evidence — 2026-10-15

## Automated checks

- `python tools/build.py --check`: both scales validate against the official VLC 3.0.x DTD; IDs, resource references and functional button actions pass.
- `python tools/check_contracts.py`: both scales pass exact atlas-versus-unpacked pixels, original main-button coordinates, 56 clock/shutter/palette states plus startup, layout action ownership, single video/playlist/EQ instances, independent 2x needle-frame resampling, animation metadata, endpoint assets, remaining-time dash and static shutter hover/pressed masks.
- `python tools/check_hits.py`: both scales pass 856 functional main-control instances. Coverage is 490,995 pixels at 1x and 1,957,753 at 2x, after excluding only physical overlaps between verified source outer buttons. Invisible hit rectangles remain potential obstructions. This is an offline model of the final XML/pixels, not native mouse QA.
- Mutation checks: a deliberately incorrect elapsed/remaining clock transition failed the contract suite; a painted black obstruction over Next failed the hit suite. XML was restored after each mutation; delivered VLTs were not modified by these tests.
- A displaced animation-band manifest entry failed the exact reconstruction guard; the manifest was restored afterward.
- `python tools/check_animation_bands.py`: native animation masks stay within 4,096 pixels in height. Reassembling their bands reproduces every canonical RGBA frame exactly, with matching fps/loops, source placement and actions. The guard failed before band generation existed.
- Python compilation and `git diff --check` passed. The preview was regenerated and inspected; it is an asset rendering.

## Native VLC 3.0.23

Both scales of the prior parity candidate loaded and played a generated silent 640×360 MPEG-4/AAC clip through VLC's loopback RC interface. The reference is 90 seconds long. Native playback statistics and exact candidate hashes are recorded in `runtime-summary.json`; they prove theme load and player operation, not skin button interaction. The current banded packages have separate exact hashes and native silent-WAV initialization checks in `load-benchmark.json`.

An earlier parity test exercised native fullscreen output and Escape through Computer Use. Its capture showed the complete 16:9 reference video. The automation tool does not enumerate VLC's owned skin windows, although the user confirmed the skin is visible. No native skin screenshot or mouse-control certification is claimed. No desktop captures are included in this repository or bundle.

The expanded theme originally exposed a VLC 3.0.x generated-ID truncation defect after the counter exceeded 999. Source and test crash-dump evidence traced the pure-virtual-call crash to colliding control IDs. Explicit unique IDs on every generated control resolved the load crash; repeat native loads succeeded.

Native logs include first-run missing isolated config files and a failed search in the user's optional font directory before the packaged font loads. They contain no unknown action/variable, invalid tooltip font, malformed theme or pure-virtual-call diagnostics in the successful tests.

## Review findings resolved

A separate read-only reviewer found two defects. Shutter hover/pressed states restarted transparent lead-in animations, potentially cancelling clicks; both states now use static original artwork and regression tests. The hit test also discarded arbitrary painted obstructions; exclusions are now restricted to verified source outer-button overlaps and an obstruction mutation is rejected.

## Practical limits

The user confirmed that 2x eventually appeared after minutes. Upstream Win32Graphics builds masks by repeatedly combining opaque pixel runs. Horizontal bands retain animation pixels/timing while reducing that work. The native benchmark now measures CLI autoplay after interface initialization, using a silent WAV; RC commands never start playback. Windows file-log buffering made the first log-poll timing unreliable. The corrected benchmark checks flushed theme diagnostics after shutdown and requires both scales to initialize within 30 seconds and remain alive through startup. Final timings and package hashes are in `load-benchmark.json`. Cross-machine performance remains unverified.

Native clicks, dial dragging, playlist scroll/selection, EQ listening, embedded video placement/resize, visual hover feedback and animation timing still need hands-on review. WMP-only feature removals and other permitted adaptations are listed in PARITY.md. Complete parity remains a user acceptance decision.

Regular VLC launches can restore a layout without the intro. Review launchers reset it; the conversion credit page provides Replay intro. The automatic WMP on-load timer has no direct skin-only equivalent.
