# Snapping preference and playback visibility

Both development skins add a labeled SNAP ON/OFF button beside the playlist folder
and Clear buttons. The cyan ON label means snapping is enabled; the neutral OFF label means disabled.
The button retains separate hover/pressed feedback and stays in the footer when
resizing. Snapping defaults ON. Its preference is shared between scales and
saved independently from VLC geometry, media volume and the native playlist.
The helper tray provides the same control.

OFF disables pane/main-player and screen-edge snapping, plus movement of attached
pane groups. It preserves cached native dependency information so ON can restore
ordinary docking. ON retains the exposed-target filter, the native15px magnet,
main priority2 and auxiliary priority1. The original Anchor declarations and
artwork remain intact.

Native support requires the validated copied64-bit runtime and exact supported
Skins2 plugin. Standard installed-executable and unsupported launches keep native
snapping enabled; their playlist button remains unavailable rather than claiming
an ineffective OFF state. No installed binary is patched. Snapping is not disabled
automatically as a dragging workaround.

The shared preference is LocalAppData/NfsSkinEffects/snapping-enabled.txt. Missing
or invalid values defaultON; literalfalse selectsOFF. Saves replace atomically.
Stale saved requests cannot toggle on startup, delayed acknowledgements cannot
toggle twice, and transient UI layouts reset separately from the saved preference.
Native command cells defer while the selected GUI thread owns capture.

The companion addon also adds a persistent native video.show() command cell.
It lets the host show VLC's own video window through native skin state after an
explicit immediate-play selection. Appending a normal video must retain existing
rows and immediately start that new row. Explicit playlist/Mix Add keeps its queue
semantics. Posting pl_play alone is not proof that media started or its pane was
revealed; the companion owns bounded confirmation and playback diagnostics.

The companion owns startup ordering: hold only the main player above other panes
during startup, release its temporary priority, then restore normal stacking.
This does not grant the sound/hover helper ongoing focus control, force all panes
topmost, reset saved layout/palette, or force an intro replay when the native saved
layout bypasses it.

See snapping-review.json for exact package/source hashes and verification scope.
Private tests use a non-input desktop, owned processes and fresh profiles. They do
not establish physical mouse feel, visual user acceptance or real speaker output.
Packaging, ZIP creation, publication and release remain on hold.

Final private verification passed70 native cases across both scales, including actual labeled-button request/acknowledgement/state transitions, OFF/ON snapping/group behavior, covered-target rejection and repeated native video hide/show. The test-only derived skins include an explicit hide cell absent from the production addon. All source copies, protected installed files and retained user processes passed preservation guards; the input desktop was unchanged. Helper/persistence and capture fixtures separately passed117 and55 cases. Full pointer-driven user acceptance remains separate.

The coordinated current1x update is loaded from the final67e5 source with the matched helper6f369 and DLLac80. Independent read-only inspection confirms native supportStatus1, snapping capability1, ready191 and enabled202, fixed-clock receiver181, clearready161 and the restored non-topmost main. The current native queue remained empty/stopped at100percent volume; no historical restore was used. Six saved pane rows and normal/sound settings passed preservation. The2x development package passed private checks without changing its active profile or the installed skin library. Actual signed-in YouTube clicking, physical appearance and startup animation visibility remain user-review items. Earlier exact-hash evidence files are intentionally retained unchanged.
