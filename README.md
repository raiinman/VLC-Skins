# VLC Skins

Need for Speed Underground, converted from the original Windows Media Player 9 skin to native VLC Skins2 by **Dead Signal Interactive**.

**Status: first review build. User acceptance of the 80% milestone is pending.** XML, resources, action targets and control coverage pass automated checks. VLC loaded both scales and played a generated 60-second video, including with the final 2x package. Native window capture did not expose VLC's owned skin windows, so mouse interaction, animation timing and video placement still require a real visual review. This is not a claim of complete parity.

![Original artwork and VLC conversion](docs/preview.png)

This comparison is rendered from the assets and XML, not captured from VLC.

## Try it

- [2x skin](dist/Need-for-Speed-Underground-2x.vlt): 600 × 596 main player, for modern screens.
- [1x skin](dist/Need-for-Speed-Underground-1x.vlt): original 300 × 298 main player.

In VLC, choose **Tools → Preferences → Interface → Use custom skin**, select the VLT, save, then restart. [Official installation instructions](https://vlc-user-documentation.readthedocs.io/en/latest/addons/skins.html).

The star/visualization button opens the rectangular video window; the list button opens the original framed playlist; the bars button opens the equalizer. The small color button cycles seven palettes. The information button opens the original game menu, whose footer has a separate conversion credit button. Drag the frame to move a panel and its corner to resize the playlist or video.

## Preserved and adapted

Original player artwork, hover/pressed buttons, seven palettes, information menu, game description, story pages, screenshots, startup animation and shutter frames are retained. The source is a WMZ/WMS package rather than a Winamp skin.

The video panel is rectangular and clear of the NFS logo. VLC uses curved seek and volume sliders with the original needle sprites. The ten-band equalizer and preamp use VLC variables; obsolete WMP SRS/WOW, speaker-size, balance, crossfade, sound-effects and WMP visualization-preset controls are removed. VLC owns native context and settings dialogs; Skins2 cannot restyle their interiors. The skin's own information menu retains its original images.

The 2x package uses per-frame Lanczos resampling of the recovered originals. It does not invent higher-resolution detail. [Control mapping and review limits](docs/PARITY.md).

## Build and verify

Requires Python 3.11+, Pillow and lxml. Original extracted inputs and the font are included, so rebuilding does not need the Downloads file.

```powershell
python -m pip install -r requirements.txt
python tools/build.py
python tools/check_contracts.py
python tools/preview.py
```

To repeat recovery from the supplied package:

```powershell
python tools/build.py --source "C:/path/to/Need_for_Speed_Underground.wmz"
```

Extraction checks every member path and CRC. Only the known four-byte local ZIP signature replacement is made, in memory. The original file is untouched. [Provenance manifest](skins/need-for-speed-underground/provenance.json).

DOX is installed as the root and child AGENTS.md hierarchy, copied and adapted from [raiinman/dox](https://github.com/raiinman/dox). [Attribution and dependency sources](docs/SOURCES.md).

## Credits

Original skin: **The Skins Factory**. Original copyright: **© 2003 Electronic Arts Inc. All Rights Reserved.** Conversion: **Dead Signal Interactive**. Original materials retain their owners' rights. This private review repository does not assign a new license to the recovered artwork, scripts or branding.
