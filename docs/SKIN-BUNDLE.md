# NFS Underground 1x, single download

Version 1.1.1 bundles the skin and its sounds/video-controls helper in one Windows ZIP. YouTube stays separate software and its 1.1.0 download is unchanged.

## Install

1. Install 64-bit VLC 3 for Windows.
2. Extract `NFS-Underground-1x-Windows-x64.zip` completely.
3. Open `Start NFS.exe`.

The included skin is selected automatically. Keep all extracted files together. No compiling, Python, Chrome or account is needed. The launcher uses private VLC settings and does not attach to an existing player. Its tray icon includes the separate skin-sound volume control. The executables are unsigned.

The VLT alone remains available for users who want only the theme. It cannot supply helper sounds or framed-video hover controls by itself. Native borderless controls remain VLC-owned. Install the separate YouTube app only for YouTube features. Independent launchers own separate sessions; optional composition is described in [software separation](SOFTWARE-SEPARATION.md).

## Package and verification

- Download size: 52,855,435 bytes. [Exact hashes and checks](skin-bundle-review.json).
- The VLT is byte-identical to the notice-bearing 1.0.0/1.1.0 release, SHA256 `91ed2e80498b3b6fc3a746a22c54e02b79df8f0f491837eaee674fdd73c87497`. It is stored without recompression. No artwork, animation frames, timing or sounds changed.
- The sound/hover executable, native wheel bridge and volume observer are unchanged from the verified 1.1.0 helper.
- The only launcher behavior change selects its adjacent `Need-for-Speed-Underground-1x.vlt` before a remembered file. Explicit `--skin` still wins. Exact source validation remains mandatory.
- Source compilation with warnings as errors, pure self-test, preparation/preservation/manifest tests and six launcher-selection cases pass.
- The extracted shipping executable passes preparation without `--skin`, repeat preparation, manifest hash checks and tampered-skin rejection before data creation. ZIP CRCs and every manifest payload pass.
- These are offline preparation checks. No VLC/browser launch, physical input or installed-profile write was used. Existing isolated native runtime evidence remains scoped to [1.1.0](software-separation-review.json); this packaging change does not establish new speaker or physical-hover observations.

The bundle retains original skin/font notices inside the VLT and original-code MIT notices beside the executable. Upstream skin materials are excluded from our MIT grant. [Licensing](../LICENSE.md).

Historical release assets, the independent YouTube package, the user's installed/running setup, and all 2x files remain unchanged.
