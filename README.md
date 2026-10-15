# VLC Skins

Need for Speed Underground, converted from the original Windows Media Player 9 skin to native VLC Skins2. Conversion by **Dead Signal Interactive**; original skin by **The Skins Factory**.

**Status: complete-parity implementation pass, awaiting hands-on acceptance.** Both scales pass XML, pixel-preservation, state-transition and input-layer regression checks. VLC 3.0.23 loads and plays with both scales. Native fullscreen video and Escape were exercised. Owned skin windows are visible to the user but unavailable to the automation tool; skin clicks, dragging and visual animation review remain unverified. See [verification](docs/VERIFICATION.md).

![Original artwork and VLC conversion](docs/preview.png)

This comparison is rendered from the assets and XML, not captured from VLC.

## Try it

- [2x skin](dist/Need-for-Speed-Underground-2x.vlt): 600 × 596 main player, for modern screens.
- [1x skin](dist/Need-for-Speed-Underground-1x.vlt): original 300 × 298 main player.

In VLC, choose **Tools → Preferences → Interface → Use custom skin**, select the VLT, save, then restart. [Official installation instructions](https://vlc-user-documentation.readthedocs.io/en/latest/addons/skins.html).

The star/visualization button opens the rectangular video window; the list button opens the original framed playlist; the bars button opens the equalizer. The small color button cycles seven palettes. The information button opens the original game menu, whose footer has a separate conversion credit button. Drag the frame to move a panel and its corner to resize the playlist or video.

## Preserved and adapted

Original player artwork, hover/pressed buttons, seven palettes, information menu, game description, story pages, screenshots, startup animation and shutter frames are retained. The source is a WMZ/WMS package rather than a Winamp skin.

The video panel is rectangular and clear of the NFS logo. The seek and volume gauges keep the original needle sprites and horizontal drag mapping recovered from the source position maps. Click the clock to toggle elapsed and remaining time. The ten-band equalizer and preamp use VLC variables; obsolete WMP SRS/WOW, speaker-size, balance, crossfade, sound-effects and WMP visualization-preset controls are removed. VLC owns native context and settings dialogs; Skins2 cannot restyle their interiors. The skin's own information menu retains its original images.

Palette changes preserve the clock mode, shutter state and open panels. The information frame also follows the selected palette. Startup and shutter playback follow the original script timing.

The 2x package uses per-frame Lanczos resampling of the recovered originals. It does not invent higher-resolution detail. Lossless horizontal animation bands reduce Windows initialization to approximately 4 seconds at 1x and 14 seconds at 2x on the test machine, followed by the roughly 8-second original intro. Separate `Preview-1x.cmd` and `Preview-2x.cmd` launchers use isolated settings and start the intro. Regular VLC launches may restore another saved layout and skip it; Information → conversion credits → Replay intro runs it again in the blue theme. [Control mapping and review limits](docs/PARITY.md).

## Build and verify

Requires Python 3.11+, Pillow and lxml. Original extracted inputs and the font are included, so rebuilding does not need the Downloads file.

```powershell
python -m pip install -r requirements.txt
python tools/build.py
python tools/check_contracts.py
python tools/check_hits.py
python tools/check_animation_bands.py
python tools/preview.py
# Windows native initialization regression check (requires installed VLC):
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
