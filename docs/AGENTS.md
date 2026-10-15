# docs

## Purpose
Evidence, control mapping and user review records.

## Ownership
This subtree.

## Local Contracts
Separate static verification, runtime observation and pending checks. Record unsupported features explicitly.

## Work Guidance
Follow the root visual parity contract.

## Verification
Run python tools/build.py --check, python tools/check_contracts.py, python tools/check_hits.py, python tools/check_animation_bands.py, python tools/check_startup.py, python tools/check_source_art.py, python tools/check_panels.py, python tools/check_transitions.py, python tools/check_placement.py python tools/check_launchers.py and python tools/check_video.py after conversion changes. Run python tools/compare_layers.py for a combined-layer visual audit; residuals are review findings, not an automatic parity certification.

## Child DOX Index
None.


PARITY.md owns acceptance and deviations; SOURCES.md owns provenance; VERIFICATION.md owns check evidence and limits. preview.png is an asset-rendered comparison, not a native screenshot. Keep native RC playback, fullscreen keyboard checks, offline hit modeling and actual skin mouse review distinct.

load-benchmark.json records final package initialization measurements. runtime-summary.json records earlier video playback tests and their exact package hashes; keep the versions distinct. Record saved-layout intro limits and replay access in PARITY.md.

native-gui-review.json records sanitized mouse/visual observations and package scope. Keep failed/intercepted attempts out of passing evidence. Native testing uses an isolated profile and a floating video output as an automation anchor; it does not establish embedded video placement. Record paused-clock seek staleness and interrupted-transition behavior as explicit Skins2 limits. Never include desktop captures, loopback passwords or user media in review artifacts.

offline-review.json identifies the latest background-only candidate and its exact hashes. Native GUI and load-benchmark records retain the earlier package hashes they actually tested. Keep offline candidates separate from installed/user-reviewed builds; the asset-rendered startup contact sheet is not a native capture.

Record default placement, transition gating and isolated launcher-writer checks as offline evidence. Work-area checks allow overlapping windows and do not prove native display or saved-layout migration.

VIDEO-SIZING.md owns the source-backed video sizing analysis. visual-comparison.json and visual-*.png own offline combined-layer comparison evidence; these are reconstructed asset renders, never native screenshots or a percentage acceptance score.
