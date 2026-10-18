# Skin and YouTube software separation

The user requested independent software on 2026-10-17, after publication of the combined 1.0.0 companion. Separate download links alone do not meet this request.

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

Current status: the standalone NFS controller, source snapshot and 136,686-byte helper ZIP pass offline and isolated native checks. The independent YouTube build still requires its stock-VLC video gate before publication. The public README clarifies existing 1.0.0 dependencies and does not yet advertise split downloads.

The NFS checks cover all original non-XML payload bytes, both accepted skin archives, repeat preparation, manifest tampering and unsafe input rejection. A private non-input desktop fixture using the same seven source files verifies the moving full intro, original topmost restoration, tray restoration of a minimized player, snapping initialization, framed hover channel, Clear default No/cancel preserving two fixture rows, Yes clearing only that private queue, and graceful exit saving geometry. The extracted product executable separately passes preparation and rejection checks. Existing player/host/helper identities, source archives and normal settings were guarded. See [exact evidence and limits](software-separation-review.json).

Sound dispatch used private silent PCM fixtures. Speaker audibility and physical pointer-hover feel remain unverified. The user's live setup was not restarted or updated.
