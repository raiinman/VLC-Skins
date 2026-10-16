# Skin-sound volume and dragging maintenance

Right-click the NFS Underground skin effects tray icon and choose Skin sound
volume. Presets are0,10,25,50,75 and100percent; first use defaults to25percent.
Mute remains separate. The selected gain affects only original skin cues,
not VLC media or Windows volume. The saved per-user level is reused on future
launches at either scale. Changing it stops a currently playing cue and prepares
subsequent cues at the new level. Source WAVs and cue timing are unchanged.

The helper now skips redundant alpha writes when the framed strip is already
opaque. Required inactive-hover topmost behavior remains unchanged. Screen-edge
snapping stays at VLC's original15px threshold, as requested. The proposed
magnet0 experiment was discarded before installation. Current skins have no
explicit docking anchors; screen snapping and pane-to-pane docking are distinct.
No pane-docking behavior is claimed by the drag checker.

All20 compiled-helper gain cases match independently calculated samples and
preserve non-sample bytes. All82 private native assertions pass on both exact
current skins, including unchanged alpha-write suppression and exposure gates.
These fixtures do not play audio or establish subjective drag smoothness.
The companion separately removes unchanged embedded-child resize work and owns
click-to-play, Settings-menu placement, live streams and Shorts/Reels routing.
See maintenance-rollout.json for current integration status and remaining limits.
