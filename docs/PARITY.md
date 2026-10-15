# Parity and review contract

## Acceptance

The user decides whether the initial review reaches 80%. Preserve working buttons/sliders, available animations and original asset quality. Preserve the information menu's aesthetic. Allowed changes are a flat video rectangle, careful upscale, font changes, obsolete-control removal, limited relocation, and an unobtrusive Dead Signal Interactive credit.

## Control mapping

| Original control | VLC implementation | Verification |
| --- | --- | --- |
| Open | dialogs.fileSimple() | Action exists in VLC source; click pending |
| Next / previous | playlist.next() / previous() | Action exists; click pending |
| Play / pause | Stateful checkbox using vlc.isPlaying | Action and variable checked; click pending |
| Stop / minimize / close | vlc.stop(), minimize(), quit() | Actions exist; click pending |
| Volume gauge | Curved Slider + all 29 original sprite frames | Resource and binding checked; dragging pending |
| Seek gauge | Curved Slider + 33 frames reversed to run 0 → 100% | Resource and binding checked; dragging pending |
| Playlist toggle | tracks.show() / hide() | Targets and state checked; click pending |
| Shuffle / loop | playlist.isRandom / isLoop checkboxes | Variables and actions checked; click pending |
| Playlist entries | Playtree with scroll slider, add media | XML and variable checked; selection/scroll pending |
| Equalizer | Ten equalizer.band(n) sliders, preamp and enable | XML and variables checked; audible response pending |
| Visualizations | Opens rectangular video panel | Intentional adaptation; screen geometry pending |
| Full mode / zoom | vlc.fullscreen() | Action exists; fullscreen pending |
| Color | Seven coordinated player, playlist, EQ and video layouts | Target ownership checked; switching pending |
| Shutter | 12 original frames, forward/reverse animated buttons | Frame count and restart behavior supported by VLC source; timing pending |
| Startup | Original 59-frame GIF converted to a one-shot vertical sprite strip, transparent final frame | Frame metadata checked; timing pending |
| NFS logo / information | Opens original game menu | Original images, hover/pressed states and navigation retained |
| About conversion | Separate carbon-backed credit page inside information window | Asset preview inspected |
| Old marketing links | Historic destinations shown as source page artwork | Obsolete outbound actions omitted |

## Intentional changes

- The original WMP frames have 72 transparent pixels below their visible bottoms; panel geometry removes that extra space.
- Video is a separate rectangular, resizable area inside the original border. The logo stays on the circular audio controller.
- Equalizer bands follow VLC's ten frequencies rather than WMP's labels; tooltips identify VLC band numbers.
- Equalizer preset stepping/reset, SRS/WOW/TruBass, speaker size, balance, crossfade and skin sounds have no direct Skins2 action bindings and are removed. Their source assets remain archived.
- Main time and metadata use a TTF font. The original engraved digit backing remains.
- Color changes select the corresponding layouts immediately; the original JavaScript alpha crossfade is not reproduced by Skins2 layout actions.
- Native VLC popups/preferences are controlled by VLC, outside the skin's bitmap styling API. The original internal game menu is preserved.

## Observed checks, 2026-10-15

- Both 1x and 2x builds pass the official VLC 3.0.x DTD, unique-ID, resource-existence, layout-owner, slider-coverage and animation-frame checks.
- VLC 3.0.23 loaded both a 1x test build and the final 2x package without unknown action, unknown variable, invalid tooltip-font or resize-policy warnings after repairs. An earlier build exposed DTD catalog and resize-anchor errors which were corrected.
- A generated MPEG-4/AAC test clip opened successfully. VLC's loopback RC interface reported play state 3, time 15 seconds for 1x and 8 seconds for the final 2x package, duration 60 seconds. This verifies the player engine with the skin loaded; it does not prove clicks or on-screen video placement.
- The Computer Use plugin listed VLC as running but exposed no owned skin windows. No GUI clicks, captured runtime screenshot, EQ listening test, fullscreen/resize interaction or visual animation timing was verified.
- Asset-rendered comparison inspected after removing a transient grayscale startup overlay and correcting a composite EQ button group into its individual switch.

## Review next

Try play/pause, seek at both endpoints, volume, playlist selection/scroll, shuffle/loop, all EQ bands, color cycling, shutter reopening, menu navigation and rectangular/fullscreen video. Compare hover/pressed states and animations to the original. Record the user's rating and requested corrections here before marking the 80% milestone accepted.
