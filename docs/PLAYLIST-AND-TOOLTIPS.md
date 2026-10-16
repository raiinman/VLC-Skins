# Playlist clear button and tooltip timer

Both scales add a small beveled trash-can button beside the original playlist
folder, with distinct normal, hover and pressed artwork. The existing folder,
all original control IDs/actions and pane geometry remain unchanged. The button
stays attached to the bottom left while resizing.

The companion arms a dedicated capability and handles its separate ready/request
signal. The button invokes the existing confirmed Clear playlist command, which
also cancels managed playlist/Mix continuation. It does not use playlist.del(),
which deletes selected rows only. Plain VLTs hide this additional button without
a capable host. Protocol acknowledgement and capability changes defer during
native mouse capture; the matching bridge guards the exact dispatch cells too.
Verification never clears the user's actual queue.

Tooltips existed with the correct defaultfont, but forced clock refresh sent
an offscreen double-click every500ms. Each newly active clock layout changes
the hit control, and VLC's findHitControl cancels its global tooltip timer.
That timer also waits500ms, preventing tooltip display throughout the skin.

The new fixed clock command has persistent elapsed/remaining Image receivers.
Each command synchronously selects phase_a then phase_b in the independent clock
state, so it refreshes time while retaining the same receiver identity across
ticks. Repeated refreshes no longer cancel the global tooltip, and paused-seek
refresh continues during hover. First use or switching mode can cancel a tooltip
once. Older packages without this command retain the conservative hover-deferral
fallback. Capture guards, sounds and video-relative stacking remain independent.

The current empty/stopped state also exposed a separate visibility policy:
Settings and CC were hidden without managed YouTube playback. Schema2 companion
art now retains dimmed, non-dispatching controls in the same positions, with
explanatory native tooltips. Available playback retains the existing active
commands and actual caption indicator. No queue restoration is inferred from
an earlier checkpoint when the current native queue is empty.

playlist-tooltip-review.json records exact candidates and focused checks.
Native private fixtures prove root/ownership decisions and preserve the running
session; they do not establish physical tooltip appearance or drag feel.
Packaging remains on hold. Covered-pane docking is a separate native change.

The matched1x source/helper/host and schema2 HUD are now loaded. Read-only
integration confirms the clear capability is enabled, its request is ready,
and the fixed clock receiver and elapsed phaseB are present. The subsequent
DLL-only repair activates covered-target filtering with Status1, preserving
the latest empty/stopped queue,100percent volume and all settings. See
exposed-docking-rollout.json. No actual clear command was executed in testing.

Source: [VLC3.0.23 Skins2 commands](https://github.com/videolan/vlc/blob/3.0.23/modules/gui/skins2/parser/interpreter.cpp).
