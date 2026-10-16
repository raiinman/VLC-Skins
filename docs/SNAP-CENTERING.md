# 1x SNAP centering and Play-now default

The user screenshot registers exactly against the82x29 native SNAP face at(80,20).
The labels were horizontally centered within half a pixel, but visible SNAP ink
occupied y28..37 and OFF y28..36, above the face center34.5. Move SNAP down2pixels
and ON/OFF down3pixels to center their visible ink and align their baselines.
Keep13/12px native fonts, focus=false, x/width, hit target and feedback artwork.

The actual package comparison permits only those three Text y attributes to
change. Every other XML node and every non-XML payload byte must remain identical.
The2x package stays held and unchanged. No helper, sound or startup behavior is
changed by this alignment fix.

The companion now defaults the playlist/Mix selector to Play now. Existing queue
items remain, and the selected video starts immediately. Add to queue remains an
explicit option; ordinary video click routing is unchanged. The companion owns
the host policy, checks, current-state capture and matched1x activation.

See snap-centering-review.json for exact hashes, checks and activation. Prior
startup/audio proof remains scoped to its measured build, with unchanged assets
and timing preserved by the byte-for-byte delta oracle. Packaging and2x remain
held; no physical input is used.

The matched1x update is loaded. The companion read native ComboBox selection1 without input or media playback; independent inspection confirms the active skin has the corrected native text coordinates and bridgeStatus1. The fresh empty/stopped queue, actual captured volume265 (about104percent), pane geometry and settings were preserved. The2x package remains byte-identical.
