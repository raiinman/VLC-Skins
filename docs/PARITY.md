# Parity and acceptance

The current target is complete parity within the user's permitted VLC adaptations. Acceptance belongs to the user. This build is not certified as 100% visually or interactively identical.

| Source behavior | Conversion | Evidence |
| --- | --- | --- |
| Main artwork and controls | Original coordinates, seven palettes, original hover/pressed images | Pixel/coordinate contracts at both scales |
| Open, transport, minimize, close | Native VLC actions | XML/action checks; skin mouse clicks pending |
| Volume and seek gauges | All 29/33 original frames; source horizontal position mapping; seek frames reversed | Exact per-frame pixel tests; native dragging pending |
| Elapsed/remaining clock | Clickable toggle; retained across palette/shutter changes | State-transition contracts; click pending |
| Palette cycling | All frame palettes, including information; preserves panel widgets and clock/shutter state | Layout/visibility contracts; visual switching pending |
| Shutter | Eleven travel frames at 20 fps, separate timed lighting, open/closed endpoints | Source script and frame contracts; mouse/timing review pending |
| Startup | Source 59-frame GIF, initial hold, lighting and final fade at source timings | 81-frame 10 fps sequence with lossless bands; saved-layout limit below; visual review pending |
| Playlist | One Playtree, scrolling, add, shuffle, loop | DTD/action checks; native selection/scroll pending |
| Equalizer | One ten-band EQ, preamp, enable | Native variable bindings; audible/drag review pending |
| Video | One rectangular resizable viewport inside original framing | Native decoding/playback and fullscreen/Escape; embedded placement/resize pending |
| Information | Original game/menu/story/screenshot artwork, navigation and disabled endpoint assets | Resource/endpoint contracts and asset-rendered preview |
| Credit | Unobtrusive separate conversion page | Preview inspected |

## Permitted adaptations and limits

- Video is rectangular; the NFS logo remains on the audio controller. Original panel frames omit their unused transparent bottom margins.
- Original images remain lossless at 1x. Each animation/needle frame is independently resampled with Lanczos at 2x to avoid bleeding from adjacent frames.
- Equalizer frequencies follow VLC; removed WMP-only controls include preset/reset, SRS/WOW/TruBass, speaker size, balance, crossfade, skin sounds and visualization presets. Their source assets remain archived. The removed right-side EQ rails use the original carbon texture and VLC preamp.
- Clock/metadata use a TTF font over the original backing.
- Palette switching is immediate. The source JavaScript color crossfade has no direct Skins2 layout-action equivalent.
- Regular VLC launches restore the saved layout, which can bypass the intro after switching away from `main_start`. Skins2 has no source-script on-load timer equivalent. Review launchers clear saved layout state; the conversion credit page provides Replay intro in the blue theme, including when `main_start` is already selected.
- VLC owns native context/preferences dialogs. Its skin API cannot style those interiors. The skin's own information menu retains its original artwork.
- Old marketing links remain as source artwork; obsolete outbound actions are omitted.
- Decorative WMP overlays were pass-through. Functional outer buttons are layered above the equivalent Skins2 decorative hit masks to keep the controls reachable.

## Acceptance still needed

Review actual hover/pressed feedback, startup/shutter timing, color cycling, clock toggle, transport, volume/seek endpoints, playlist selection/scroll, EQ response, menu navigation, panel resize and embedded video. The offline hit model and RC playback checks do not substitute for those native mouse and visual checks. See [verification evidence](VERIFICATION.md).
