# VLC Skins

Need for Speed Underground, converted from the original Windows Media Player 9 skin to native VLC Skins2. Conversion by **Dead Signal Interactive**; original skin by **The Skins Factory**.

**Status: latest candidate verified offline; native recheck and user acceptance pending.** Both scales pass XML, pixel-preservation, state-transition and input-layer checks. Earlier native mouse tests cover transport, volume/seek, playlist selection/scrolling, equalizer controls and original information navigation. The native pass corrected volume direction, shutter interiors, playlist scrolling and resize hit areas. Offline checks now cover corrected intro transparency, shutter input gating, resized sliders and default panel placement. Both preview launchers reset their isolated layout settings before launch. See [verification](docs/VERIFICATION.md).

![Original artwork and VLC conversion](docs/preview.png)

This comparison is rendered from the assets and XML, not captured from VLC. [Corrected intro frame sheet](docs/startup-frames.png).

## Try it

- [2x skin](dist/Need-for-Speed-Underground-2x.vlt): 600 × 596 main player, for modern screens.
- [1x skin](dist/Need-for-Speed-Underground-1x.vlt): original 300 × 298 main player.

In VLC, choose **Tools → Preferences → Interface → Use custom skin**, select the VLT, save, then restart. [Official installation instructions](https://vlc-user-documentation.readthedocs.io/en/latest/addons/skins.html).

The star/visualization button opens the rectangular video window; the list button opens the original framed playlist; the bars button opens the equalizer. The small color button cycles seven palettes. The information button opens the original game menu, whose footer has a separate conversion credit button. Drag the frame to move a panel and its corner to resize the playlist or video.

## Preserved and adapted

Original player artwork, hover/pressed buttons, seven palettes, information menu, game description, story pages, screenshots, startup animation and shutter frames are retained. The source is a WMZ/WMS package rather than a Winamp skin.

The video panel is rectangular and clear of the NFS logo. The seek and volume gauges keep the original needle sprites and horizontal drag mapping recovered from the source position maps. Click the clock to toggle elapsed and remaining time. The ten-band equalizer and preamp use VLC variables; obsolete WMP SRS/WOW, speaker-size, balance, crossfade, sound-effects and WMP visualization-preset controls are removed. VLC owns native context and settings dialogs; Skins2 cannot restyle their interiors. The skin's own information menu retains its original images.

The video panel now retains the user-selected size when media dimensions change. [Sizing source audit](docs/VIDEO-SIZING.md) records the policy and native review limits. The [layer comparison report](docs/visual-comparison.json) and source/converted/residual sheets compare retained art offline; omitted fonts and conversion additions are listed in the report.

Palette changes preserve the clock mode, shutter state and open panels. The information frame also follows the selected palette. Startup and shutter playback follow the original script timing.

The 2x package uses per-frame Lanczos resampling of the recovered originals. It does not invent higher-resolution detail. Lossless horizontal animation bands reduced Windows initialization to the times recorded for the earlier native-tested package in [load-benchmark.json](docs/load-benchmark.json), followed by the roughly 8-second original intro. Separate `Preview-1x.cmd` and `Preview-2x.cmd` launchers rewrite their adjacent isolated INI files to select the bundled skin and clear saved layouts before starting the intro. Fresh window positions fit a 1280×720 work area at 1x and 1920×1040 at 2x; existing saved positions can override them. Regular VLC launches may restore another saved layout and skip it; Information → conversion credits → Replay intro runs it again in the blue theme. [Control mapping and review limits](docs/PARITY.md).

## Build and verify

Requires Python 3.11+, Pillow and lxml. Original extracted inputs and the font are included, so rebuilding does not need the Downloads file.

```powershell
python -m pip install -r requirements.txt
python tools/build.py
python tools/check_contracts.py
python tools/check_hits.py
python tools/check_animation_bands.py
python tools/check_startup.py
python tools/check_source_art.py
python tools/check_panels.py
python tools/check_transitions.py
python tools/check_placement.py
python tools/check_launchers.py
python tools/check_video.py
python tools/check_corners.py
python tools/compare_layers.py
python tools/preview.py
# Native initialization check (launches VLC; run when desktop testing is available):
python tools/benchmark_load.py
```

To repeat recovery from the supplied package:

```powershell
python tools/build.py --source "C:/path/to/Need_for_Speed_Underground.wmz"
```

Extraction checks every member path and CRC. Only the known four-byte local ZIP signature replacement is made, in memory. The original file is untouched. [Provenance manifest](skins/need-for-speed-underground/provenance.json).

DOX is installed as the root and child AGENTS.md hierarchy, copied and adapted from [raiinman/dox](https://github.com/raiinman/dox). [Attribution and dependency sources](docs/SOURCES.md).

## Credits

Original skin: **The Skins Factory**. Original copyright: **© 2003 Electronic Arts Inc. All Rights Reserved.** Conversion: **Dead Signal Interactive**. Original materials retain their owners' rights. This private review repository does not assign a new license to the recovered artwork, scripts or branding.

The lower-right resize corner now uses matching original artwork at both scales. [Corner fix](docs/CORNER-FIX.md) explains the Windows cache-copy defect and the remaining native appearance check. Already running or derived copies must be regenerated/reloaded to use the new assets.
