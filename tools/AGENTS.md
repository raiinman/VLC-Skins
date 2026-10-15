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
Run python tools/build.py --check, python tools/check_contracts.py, python tools/check_hits.py and python tools/check_animation_bands.py after conversion changes.

## Child DOX Index
None.


Build ownership: build.py recovers inputs, packs lossless atlases and packages both scales; assets.py reads standalone/atlas frames; check_contracts.py validates original pixels, state transitions, source timing and explicit control IDs; check_hits.py models input layers offline; preview.py makes an explicitly asset-rendered comparison.

Assign explicit unique IDs to every control: VLC 3.0.x synthetic IDs collide past 999. Hover/down shutter assets stay static because changing a button state restarts its animation. Only the idle shutter mask has a timed transparent lead-in. Exclude only overlaps between verified original outer buttons from hit coverage; arbitrary painted obstructions must fail.

Native animation strips taller than 4096 pixels become 16 horizontal bands. Canonical PNGs and animation-bands.json are offline references; VLC loads only physical bands. check_animation_bands.py checks exact reconstruction, timing, placement and actions. benchmark_load.py measures CLI autoplay after the skins2 interface is ready; both scales must initialize within 30 seconds on the test machine. RC-triggered playback and buffered file-log timing cannot establish initialization time.
