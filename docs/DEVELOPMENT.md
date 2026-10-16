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

The optional Windows helper is already compiled in the end-user companion. Its source and developer compiler scripts live in `tools/`. Companion host/runtime packaging is maintained in the separate VLC add-ons repository and distributed as a verified release asset here.

## Package the release copy

`tools/package_1x_release.py --source <canonical.vlt> --output <separate-release.vlt> --expected-source-sha256 <audited-hash>` adds redistribution notices without changing any runtime member. It checks CRCs, unique safe paths, all runtime bytes/compression and the untouched canonical hash. This is a developer release step, not an end-user requirement.
