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
Run python tools/build.py --check and python tools/check_contracts.py after conversion changes.

## Child DOX Index
None.


Build ownership: build.py recovers inputs and packages both scales; check_contracts.py validates control coverage and action ownership; preview.py makes an explicitly asset-rendered comparison.
