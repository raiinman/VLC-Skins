# Larger Settings/CC and fewer duplicate controls

Both scales remove fullscreen and hide buttons from the framed video hover strip.
The video window header provides those controls. Native borderless fullscreen
keeps both original HUD buttons because its window header is unavailable.

The optional companion addon uses25px Settings/CC faces, up from19px, at
(300,0) and(330,0). The gear has11x11px visible ink; CC has11-13x7px strong
antialiased ink. Both remain inset within beveled faces with transparent outer
margins. Seek length is281px, with the original15x17 thumb unchanged and clear
of the enlarged buttons at both endpoints. Transport, time, volume and speaker
remain unchanged. The fixed360x64 artwork is identical in physical size for1x/2x.

The strip stays flat matching charcoal. The framed helper uses255/255 opacity:
its former85percent alpha applied to the entire window, letting moving video
show through the background and controls. Native fullscreen fading stays VLC-owned.

Exact current hashes and evidence are in hud-layout-review.json. The preceding
UI-POLISH and native-hover records retain their tested versions. Installation
and companion-owned live adoption are recorded separately. No mouse or keyboard
control is needed for source/build work or private non-input-desktop checks.
