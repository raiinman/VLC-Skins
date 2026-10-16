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

Both exact packages pass all17 conversion checks,23hover mutation cases per
scale and10addon mutations. The layer comparison has714exact cases and42
explained closed-main residuals, with no unexplained cases. Both packages pass
78private native assertions, including8opaque-alpha readbacks and strict window
exposure gates. All four protected processes,24guarded paths and the input
desktop were preserved; owned test children closed. The native fixture calls
shared product-source methods, not the deployed helper executable.

Both user-library packages are installed with verified backups. The running1x
companion adopted the new source and exact latest159-item checkpoint, preserving
manual1080p, captions, paused0:02, volume256, six pane geometries, preferences,
normal settings and original source bytes/compression. No2x profile was created.
The final screenshot was occluded by user windows; no mouse/keyboard/focus action
was taken to expose it. Current physical button/menu appearance is unverified.
See hud-layout-install.json and hud-layout-rollout.json for exact evidence.
