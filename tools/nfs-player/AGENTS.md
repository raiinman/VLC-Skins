# Standalone NFS controller

## Purpose
Publish the minimal original C# source for the independent NFS skin launcher.

## Ownership
This directory contains a release snapshot from the VLC add-ons repository. Coordinate implementation changes with that owner, then refresh these files together after review and tests. Parent tools own compilation and packaging scripts; SkinEffects.cs remains the sound/hover implementation.

## Local Contracts
- Compile only the explicit source list in ../build_nfs_player.ps1. No browser, resolver or Python dependency.
- Own only the explicitly created private VLC process, profile and helper. Preserve installed VLC, source VLTs and unrelated sessions.
- Keep full synchronized startup, original sound/hover support, snapping and confirmed playlist clearing independent of YouTube.
- Preserve exact supported skin hashes and all original assets; derived XML may add only the required startup command cells.
- Launcher priority is explicit --skin, adjacent Need-for-Speed-Underground-1x.vlt, then remembered source/dialog. All choices retain exact hash checks before private data writes.

## Work Guidance
Keep the source snapshot and released controller hashes aligned. Source updates require preparation tests and isolated native verification before distribution.

## Verification
tests/nfs-launcher.test.py --sources tools/nfs-player --skin <release-1x.vlt> --alternate-skin <canonical-1x.vlt> checks actual prepare-only precedence and invalid-source rejection without VLC or dialogs.
../build_nfs_player.ps1 compiles with warnings as errors and runs --self-test without VLC. ../check_nfs_player.py --skin <approved-1x.vlt> checks preparation, original assets, independent palette/config preservation and manifest rejection without VLC. ../package_skin_helper.py --self-test checks packaging integrity and rejection paths without executing programs. ../check_nfs_player_native.py requires explicit --actual-vlc and uses only an unselected private desktop and owned fixture processes, with silent PCM, source/settings/process guards and no physical input. Tests live in tests/ and are excluded from product compilation. Native evidence and limits belong in ../../docs/SOFTWARE-SEPARATION.md.

## Child DOX Index
None.
