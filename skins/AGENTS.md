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
Run python tools/build.py --check, python tools/check_contracts.py, python tools/check_hits.py and python tools/check_animation_bands.py after conversion changes.

## Child DOX Index
None.


Original resources are under need-for-speed-underground/original; provenance.json records all 247 members and their CRCs. vlc-1x and vlc-2x are generated.

Generated themes contain explicit control IDs and lossless atlases. Canonical animation strips remain offline references; animation-bands.json maps them to lossless native bands that bound Windows mask-construction cost. Preserve pixels, frame counts, fps and loops.

Keep the credit-page intro replay action and reset-layout review launchers: VLC may restore another layout on normal launch and bypass the initial intro.
