# Verification evidence — 2026-10-15

## Automated checks

- `python tools/build.py --check`: both scales validate against the official VLC 3.0.x DTD; IDs, resource references and functional button actions pass.
- `python tools/check_contracts.py`: both scales pass exact atlas-versus-unpacked pixels, original main-button coordinates, 56 clock/shutter/palette states plus startup, layout action ownership, single video/playlist/EQ instances, independent 2x needle-frame resampling, animation metadata, endpoint assets, remaining-time dash and static shutter hover/pressed masks.
- `python tools/check_hits.py`: both scales pass 856 functional main-control instances. Coverage is 490,995 pixels at 1x and 1,957,753 at 2x, after excluding only physical overlaps between verified source outer buttons. Invisible hit rectangles remain potential obstructions. This is an offline model of the final XML/pixels, not native mouse QA.
- Mutation checks: a deliberately incorrect elapsed/remaining clock transition failed the contract suite; a painted black obstruction over Next failed the hit suite. XML was restored after each mutation; delivered VLTs were not modified by these tests.
- Python compilation and `git diff --check` passed. The preview was regenerated and inspected; it is an asset rendering.

## Native VLC 3.0.23

Both final scales loaded and played a generated silent 640×360 MPEG-4/AAC clip through VLC's loopback RC interface. The reference is 90 seconds long. Native playback statistics and theme-validation diagnostics are recorded in `runtime-summary.json`; they prove theme load and player operation, not skin button interaction.

An earlier parity test exercised native fullscreen output and Escape through Computer Use. Its capture showed the complete 16:9 reference video. The automation tool does not enumerate VLC's owned skin windows, although the user confirmed the skin is visible. No native skin screenshot or mouse-control certification is claimed. No desktop captures are included in this repository or bundle.

The expanded theme originally exposed a VLC 3.0.x generated-ID truncation defect after the counter exceeded 999. Source and test crash-dump evidence traced the pure-virtual-call crash to colliding control IDs. Explicit unique IDs on every generated control resolved the load crash; repeat native loads succeeded.

Native logs include first-run missing isolated config files and a failed search in the user's optional font directory before the packaged font loads. They contain no unknown action/variable, invalid tooltip font, malformed theme or pure-virtual-call diagnostics in the successful tests.

## Review findings resolved

A separate read-only reviewer found two defects. Shutter hover/pressed states restarted transparent lead-in animations, potentially cancelling clicks; both states now use static original artwork and regression tests. The hit test also discarded arbitrary painted obstructions; exclusions are now restricted to verified source outer-button overlaps and an obstruction mutation is rejected.

## Practical limits

Cold loading is expensive: about twenty seconds observed at 1x and roughly two minutes at 2x on this machine, with substantial memory use from full-quality source-timed animation strips. This has not been performance-certified across machines.

Native clicks, dial dragging, playlist scroll/selection, EQ listening, embedded video placement/resize, visual hover feedback and animation timing still need hands-on review. WMP-only feature removals and other permitted adaptations are listed in PARITY.md. Complete parity remains a user acceptance decision.
