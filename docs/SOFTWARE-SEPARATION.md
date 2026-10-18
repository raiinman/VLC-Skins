# Skin and YouTube software separation

The user requested independent software on 2026-10-17, after publication of the combined 1.0.0 companion. Separate download links alone do not meet this request.

The primary NFS download now bundles the skin and its helper together for simpler installation. YouTube remains separate software and a separate download. See [the NFS bundle](SKIN-BUNDLE.md). The 1.1.0 downloads below remain historical verification records.

## Product boundaries

| Product | Owns | Required external software |
| --- | --- | --- |
| NFS Underground `.vlt` | Artwork, palettes, shutters, Info pages, native skin controls | VLC |
| NFS skin helper | Original sound effects and their volume setting, synchronized intro, compact framed-video controls, skin-specific runtime support | VLC and the matching NFS skin |
| YouTube companion | YouTube discovery and playback handoff, queue continuation, quality and captions | VLC and Chrome; no NFS helper requirement |

The NFS helper must work with local media without installing, starting or signing into YouTube or Chrome. Keep native borderless fullscreen controls available with the VLT alone. Helper-backed snapping and confirmed playlist clearing must remain functional without the YouTube application.

Each launcher owns its own explicitly selected private VLC session and profile. The independent apps do not attach to or replace another running player. Optional composition is selected through the YouTube application's NFS adapter and explicit support directory; that controller owns startup and the helper for its VLC process. Keep one helper per PID/start time. Users should select one launcher for the intended session. YouTube Settings and CC remain YouTube-owned, with their supported skin integration or toolbar fallback.

## Delivery and verification

- Keep the released 1.0.0 assets and checksums unchanged as historical downloads.
- Prepare separate ready-to-run packages with plain installation instructions and feature requirements. No end-user compiling.
- Verify NFS-only launch without a browser dependency, full intro/sound dispatch, sound volume, framed controls, snapping and confirmed clear capability.
- Verify YouTube-only launch and playback without the NFS helper, including quality/captions and queue preservation.
- Verify the explicit combined configuration has one intended VLC session and one skin helper, with functional integration and clean shutdown. Distinct independently launched apps retain distinct owned sessions.
- Keep the user's running 1x installation, queue, profile, settings and pane geometry untouched during preparation. Keep 2x held and use no physical input.

The standalone NFS controller and 136,686-byte helper ZIP pass offline and isolated native checks. The independent YouTube ZIP is 11,608,435 bytes and passes package checks plus two fresh native playback runs. Public downloads are separate: [NFS skin and helper 1.1.0](https://github.com/raiinman/VLC-Skins/releases/tag/nfs-underground-1x-v1.1.0) and [independent YouTube 1.1.0](https://github.com/raiinman/VLC-Skins/releases/tag/vlc-youtube-v1.1.0). The VLT is byte-identical to the released 1.0.0 skin; historical combined assets remain unchanged.

The NFS checks cover all original non-XML payload bytes, both accepted skin archives, repeat preparation, manifest tampering and unsafe input rejection. A private non-input desktop fixture using the same seven source files verifies the moving full intro, original topmost restoration, tray restoration of a minimized player, snapping initialization, framed hover channel, Clear default No/cancel preserving two fixture rows, Yes clearing only that private queue, and graceful exit saving geometry. The extracted product executable separately passes preparation and rejection checks. Existing player/host/helper identities, source archives and normal settings were guarded. See [exact evidence and limits](software-separation-review.json).

Sound dispatch used private silent PCM fixtures. Speaker audibility and physical pointer-hover feel remain unverified. Build and verification did not restart or update the user's live setup. The user's separately requested local installation check belongs to the companion chat; its installation and preservation evidence remain separate from these tests.

The independent YouTube handoff waits for the selected occurrence to display its first frame before the one-time show/raise. Two private runs retained the visible stock player above the browser through five and ten seconds after presentation, with advancing video/audio decode and clock, working scoped search input and the real owned Settings popup. Neither main nor browser was permanently topmost. [Native evidence](youtube-independent-review.json) records exact hashes and the dummy-audio/non-input-desktop limits.

Optional NFS composition was verified with the preceding 73c81 host: full intro, helper, then Chrome and READY. The final host changes only stock shared-main presentation readiness; the NFS branch and all seven standalone NFS source files are unchanged. This is not a new exact-74c2 composition claim. Advanced adapter configuration remains owned by the YouTube app; opening both independent launchers creates separate sessions.
