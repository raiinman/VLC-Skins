<div align="center">

# NFS Underground for VLC

**Your old media player. Back on your desktop.**

The classic Need for Speed Underground skin, made for VLC on Windows.

**Choose what you need:** the **skin** changes VLC's appearance. The optional **NFS helper** adds original sounds and controls over framed video. **YouTube is a separate app** that also works without the NFS skin.

[![Download skin](https://img.shields.io/badge/Download-1x_skin-159DC1?logo=vlcmediaplayer&logoColor=white)](https://github.com/raiinman/VLC-Skins/releases/download/nfs-underground-1x-v1.1.0/Need-for-Speed-Underground-1x.vlt)
[![NFS helper](https://img.shields.io/badge/Optional-NFS_sounds_%26_controls-444B54?logo=vlcmediaplayer&logoColor=white)](https://github.com/raiinman/VLC-Skins/releases/download/nfs-underground-1x-v1.1.0/NFS-Underground-1x-Helper-Windows-x64.zip)
[![YouTube app](https://img.shields.io/badge/Separate-YouTube_app-B91C1C?logo=youtube&logoColor=white)](https://github.com/raiinman/VLC-Skins/releases/download/vlc-youtube-v1.1.0/VLC-YouTube-Windows-x64.zip)

[Install](#install-the-skin) · [Skin sounds & controls](#skin-sounds--video-controls) · [YouTube app](#youtube-app) · [Controls](#controls) · [Help](#help) · [Credits](#credits)

https://github.com/user-attachments/assets/b5e28626-5d25-49d5-91e5-8daf4a282a67

48 seconds · 1080p60 · [Download the video](https://github.com/raiinman/VLC-Skins/releases/download/nfs-underground-1x-v1.0.0/NFS-Underground-VLC-1x-Release.mp4)

*The film shows skin-helper features and YouTube integration together. These need the separate downloads below; the VLT alone supplies the theme.*

*Original-size 1x release. 2x is on hold.*


## Install the skin

1. [Download the skin](https://github.com/raiinman/VLC-Skins/releases/download/nfs-underground-1x-v1.1.0/Need-for-Speed-Underground-1x.vlt). Keep it as a `.vlt` file. Do not unzip it.
2. In VLC, open **Tools → Preferences → Interface → Use custom skin**. Click **Choose** and select the downloaded file.
3. Click **Save**, then close and reopen VLC.

That is it. **No compiling. No Python. No extra tools.**

Need VLC? [Get VLC for Windows](https://www.videolan.org/vlc/). [Official skin instructions](https://vlc-user-documentation.readthedocs.io/en/latest/addons/skins.html).

## Skin sounds & video controls

[Download the NFS helper](https://github.com/raiinman/VLC-Skins/releases/download/nfs-underground-1x-v1.1.0/NFS-Underground-1x-Helper-Windows-x64.zip) for original skin sounds, their own volume control, the synchronized opening sequence, and compact controls over framed video.

Unzip it, open **Start NFS.exe**, and select your downloaded `.vlt`. It needs **64-bit VLC**, and uses its own private player settings. **No YouTube, Chrome, Python or compiling required.** Adjust skin-sound volume from its tray icon.

The `.vlt` alone still provides the original theme, shutters, colours, playlist, equalizer, and native playback controls. VLC's standard borderless fullscreen controls work without the helper.

## YouTube app

[Download YouTube for VLC](https://github.com/raiinman/VLC-Skins/releases/download/vlc-youtube-v1.1.0/VLC-YouTube-Windows-x64.zip), unzip it, and open **Start YouTube.exe**. Install **64-bit VLC and Google Chrome** first. It includes its own Python runtime, with no compiling or developer tools required.

It provides YouTube browsing, native VLC playback up to 4K when available, highest-first Auto quality with buffering fallback, manual quality and available captions. **It works with VLC's stock skin and does not require the NFS skin or helper.**

<p align="center"><img src="docs/youtube-companion-banner.png" alt="Promotional illustration of optional NFS and YouTube integration, based on the real 1x deck" width="720"></p>

*Optional NFS integration is illustrated above. YouTube uses VLC's stock skin by default.*

Each app owns its own private VLC session. They do not automatically attach to another running player. [Separate software and optional integration](docs/SOFTWARE-SEPARATION.md).

## Controls

- **Folder:** open music or video.
- **List:** open the playlist. **Bars:** open the equalizer.
- **Colour button:** cycle the seven colours. **Clock:** switch elapsed/remaining time.
- **Video + button:** fill the screen with the skin border; click again to restore.
- **Double-click video:** fullscreen without the border.
- **Info:** explore the original game pages and conversion credits.

The playlist and video panes can be resized from their bottom-right corners.

## Help

[Report a problem](https://github.com/raiinman/VLC-Skins/issues/new). Tell us your VLC version and whether you use the skin alone, NFS helper, YouTube app, or both.

To return to regular VLC, choose **Use native style** in Interface preferences, then restart VLC.

This release targets **Windows and VLC 3, 64-bit**. Skins are not supported on macOS. The original 1x player is small by design (300 × 298). Some original WMP-only controls are omitted; fonts and video sizing are adapted for VLC. YouTube's public-video 4K tests passed, but some seeks needed up to 20 seconds to recover. Private videos, age restrictions and account history are not promised.

[Release notes](https://github.com/raiinman/VLC-Skins/releases/tag/nfs-underground-1x-v1.1.0) · [Detailed behaviour and limits](docs/PARITY.md) · [Verification](docs/VERIFICATION.md) · [Developer notes](docs/DEVELOPMENT.md)

## Credits

Original skin: **The Skins Factory**. VLC conversion: **Dead Signal Interactive**. Built with AI assistance.

Original copyright: **© 2003 Electronic Arts Inc. All Rights Reserved.** Original artwork and branding belong to their owners. This fan conversion does not claim their ownership or endorsement. [Sources and notices](docs/SOURCES.md) · [Licensing](LICENSE.md).

</div>
