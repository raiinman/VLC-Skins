# Developer notes

You do not need these tools to use the release. Download the `.vlt` or ready-to-run companion from the main README.

## Build the 1x skin

Development requires Python3.11+, Pillow and lxml. Original extracted inputs and font are included.

```powershell
python -m pip install -r requirements.txt
python -c "import sys; sys.path.insert(0, 'tools'); from build import Builder; b=Builder(1); b.main(); b.panels(); b.information(); print(b.save())"
```

This builds only1x. Do not run the default both-scale generator while2x is held. The archive is written to `dist/Need-for-Speed-Underground-1x.vlt`. PNGs are stored without ZIP compression to favour loading; pixels, animation frames and timings remain unchanged. Rebuilt ZIP metadata may differ from the published artifact, so release hashes identify the actual download.

## Check the result

```powershell
python -c "import sys; from pathlib import Path; sys.path.insert(0, 'tools'); from build import validate; validate(Path('skins/need-for-speed-underground/vlc-1x'))"
```

The existing `tools/check_*.py` commands cover artwork, frames, coordinates, controls, panes, signals and helper contracts. Some are historical both-scale fixtures; they do not certify2x as a released edition. Read `tools/AGENTS.md` before maintaining them. Native verification is separately recorded in [VERIFICATION.md](VERIFICATION.md). Do not launch test players against a user's active configuration.

## Source and notices

[Source inventory](../skins/need-for-speed-underground/provenance.json) records member hashes/CRCs. The converter never executes the source WMS/JavaScript. Original art retains its owners’ rights. [Sources](SOURCES.md) and the vendored font/DOX notices remain authoritative.

The Windows sound/hover helper is prebuilt in the independent NFS helper package. Its source and developer compiler scripts live in `tools/`. YouTube app packaging is maintained in the separate VLC add-ons repository and distributed as its own verified release asset here.

## Independent NFS helper

The standalone controller source snapshot is in `tools/nfs-player/`. Build it with `powershell -ExecutionPolicy Bypass -File tools/build_nfs_player.ps1 -Destination <fresh-output-directory>`. This requires the installed .NET Framework compiler and runs only its pure self-test. Users receive the compiled executable and do not compile it themselves.

`python tools/check_nfs_player.py --skin <audited-1x.vlt>` checks source preparation, original payload preservation and manifest rejection without launching VLC. Native checks require an explicit `--actual-vlc` invocation of `tools/check_nfs_player_native.py`, an extracted standalone helper ZIP passed as `--support`, the audited skin passed as `--source`, and the existing private-desktop preservation rules. They never switch desktops or move physical input.

`tools/package_skin_helper.py --controller <compiled.exe> --expected-controller-sha256 <verified-hash> --output <fresh.zip> --skin <notice-bearing-release-1x.vlt> --version 1.1.1` packages the standalone controller, pinned sound/hover helper, native bridge, volume observer, notices and unchanged released 1x VLT. YouTube, Chrome, Python and user data are excluded. Omit --skin only for helper-only builds. Run --self-test --skin <notice-bearing-release-1x.vlt> to check both layouts and skin-hash rejection. [Product boundaries](SOFTWARE-SEPARATION.md) and [bundle verification](SKIN-BUNDLE.md) remain authoritative.

## Package the release copy

`tools/package_1x_release.py --source <canonical.vlt> --output <separate-release.vlt> --expected-source-sha256 <audited-hash>` adds redistribution notices without changing any runtime member. It checks CRCs, unique safe paths, all runtime bytes/compression and the untouched canonical hash. This is a developer release step, not an end-user requirement.
