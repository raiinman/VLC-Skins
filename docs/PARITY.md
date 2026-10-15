# Parity and acceptance

The latest candidate includes offline intro-transparency, shutter-gate, default-placement and isolated preview-reset fixes; native evidence below belongs to the earlier review candidate. See `offline-review.json` for exact scope.

The current target is complete parity within the user's permitted VLC adaptations. Acceptance belongs to the user. This build is not certified as 100% visually or interactively identical.

| Source behavior | Conversion | Evidence |
| --- | --- | --- |
| Main artwork and controls | Original coordinates, seven palettes, original hover/pressed images | Pixel/coordinate contracts at both scales |
| Open, transport, minimize, close | Native VLC actions | Native 1x play/pause/next/previous/Open/Close; minimize and skin fullscreen click pending |
| Volume and seek gauges | All 29/33 original frames; source horizontal position mapping; both strips reversed | Exact per-frame pixels; both-scale native volume endpoints and seeking |
| Elapsed/remaining clock | Clickable toggle; retained across palette/shutter changes | Both-scale native toggles; paused-seek and interrupted-travel limits below |
| Palette cycling | All frame palettes, including information; preserves panel widgets and clock/shutter state | Layout/visibility contracts; blue/green and closed-state native switching |
| Shutter | Eleven travel frames at 20 fps, separate timed lighting, open/closed endpoints | Native travel and endpoints at both scales; exact wall-clock timing review pending |
| Startup | Source 59-frame GIF, initial hold, lighting and final fade at source timings | 81-frame 10 fps sequence with lossless bands; native startup/replay observed, precise timing review pending |
| Playlist | One Playtree, scrolling, add, shuffle, loop | Both-scale native selection/scroll; shuffle/repeat at 1x; resize at 2x |
| Equalizer | One ten-band EQ, preamp, enable | Native enable, band and preamp changes at both scales; listening pending |
| Video | One rectangular resizable viewport inside original framing | Native decoding/playback and fullscreen/Escape; embedded placement/resize pending |
| Information | Original game/menu/story/screenshot artwork, navigation and disabled endpoint assets | Native 1x Story and 2x Screenshots navigation; exact resource/endpoint checks |
| Credit | Unobtrusive separate conversion page | Native 1x credits observed; preview inspected |

## Permitted adaptations and limits

- Video is rectangular; the NFS logo remains on the audio controller. Original panel frames omit their unused transparent bottom margins.
- Media dimensions no longer resize the video panel automatically. The frame follows the user's manual size; native playback and aspect-fit behavior still require review. See [video sizing audit](VIDEO-SIZING.md).
- Original images remain lossless at 1x. Each animation/needle frame is independently resampled with Lanczos at 2x to avoid bleeding from adjacent frames.
- Equalizer frequencies follow VLC; removed WMP-only controls include preset/reset, SRS/WOW/TruBass, speaker size, balance, crossfade, skin sounds and visualization presets. Their source assets remain archived. The removed right-side EQ rails use the original carbon texture and VLC preamp.
- Clock/metadata use a TTF font over the original backing. The clock uses 14 source-scale pixels for legibility. Metadata retains the source palette colors.
- The original playlist changes the playing-row background with its palette. VLC Playtree exposes a fixed selection background and playing-text color, without a separate playing-row background binding. The single retained Playtree therefore cannot reproduce that palette-dependent row treatment.
- Palette switching is immediate. The source JavaScript color crossfade has no direct Skins2 layout-action equivalent.
- Regular VLC launches restore the saved layout, which can bypass the intro after switching away from `main_start`. Skins2 has no source-script on-load timer equivalent. Review launchers clear saved layout state; the conversion credit page provides Replay intro in the blue theme, including when `main_start` is already selected.
- VLC owns native context/preferences dialogs. Its skin API cannot style those interiors. The skin's own information menu retains its original artwork.
- Old marketing links remain as source artwork; obsolete outbound actions are omitted.
- Decorative WMP overlays were pass-through. Functional outer buttons are layered above the equivalent Skins2 decorative hit masks to keep the controls reachable.

- Paused seeking works, but VLC's native time variable can notify text before the seek completes; the clock may retain its previous value until playback resumes. This was reproduced at 2x and traced to upstream source.
- Changing the clock token activates another layout. During shutter opening this can finish travel early; during closing it restarts travel while preserving the closing destination.
- Resize controls use exact palette corner artwork. The previous alpha-1 black masks allowed resizing but painted black rectangles through Windows cached-image copies. Native 2x resize was verified on the earlier package; the corrected corner appearance and final 1x resize need native recheck. See CORNER-FIX.md.

## Acceptance still needed

Review exhaustive hover/pressed feedback, exact startup/shutter wall-clock timing, all seven palettes, audible EQ response, 1x resize and embedded video placement/resize. Native mouse QA now covers substantial controls at both scales; it does not certify complete parity. Exact package scope and passing observations are in [native-gui-review.json](native-gui-review.json). See [verification evidence](VERIFICATION.md).

## Offline audit changes

Shutter idle, hover and pressed feedback now retain static original pixels. A separate two-frame hit mask releases after 500 ms, so leaving hover cannot restart the input delay. Every door/light frame still matches the source. Native timing and input recheck remain pending.

Fresh defaults fit 1280×720 at 1x and 1920×1040 at 2x. The 1x video window moves upward; 2x desktop positions are independent of artwork scale. Window overlap is allowed and existing saved positions are untouched. Smaller work areas remain outside this placement contract.

Review launchers rewrite only their adjacent isolated INI: bundled skin path plus empty saved layout. The writer passes UTF-8 path and failure checks offline; native end-to-end launcher validation remains pending.

## Combined-layer findings

The offline comparison restores the original parent button backings, the video's two-button header and the Web Destinations static link artwork. Obsolete outbound actions remain omitted. At 2x, menu artwork is resampled before clipping to the original mapping regions, removing filtering seams without drawing outside those regions. Microsoft's original API specifies that BUTTONGROUP.showBackground defaults to false.

Of 756 reconstructed main/information compositions, 714 match exactly. The remaining 42 closed-main cases differ along shutter/outer-control overlaps; they match exactly when the source reference applies the documented outer-control layer raise needed for VLC input access. This is a localized rendering deviation, not 100% pixel identity. Dynamic text/font changes and conversion-credit additions are excluded explicitly. Playlist/EQ/video full composites, live state changes and native display remain outside this comparison's scope.
