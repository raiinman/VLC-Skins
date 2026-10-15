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
Run python tools/build.py --check, python tools/check_contracts.py and python tools/check_hits.py after conversion changes.

## Child DOX Index
None.


Original resources are under need-for-speed-underground/original; provenance.json records all 247 members and their CRCs. vlc-1x and vlc-2x are generated.

Generated themes contain explicit control IDs and lossless atlases. Full-quality source-timed animations increase cold-load cost, particularly at 2x; preserve original assets rather than silently lowering fidelity.
