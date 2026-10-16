# Video-relative hover stacking

The compact framed bar previously reasserted global topmost status on every
open poll. It could cover YouTube while its own video pane was behind YouTube.
An already-open bar could also maintain its own exposure over a covered video.

The helper now binds the validated bar to its selected video window and places
it immediately above that video without activating or raising the video. It
follows the video's existing topmost preference. Disposal restores the original
native owner when it remains valid. Native fullscreen controls remain separate.

Pointer exposure on the bar requires the first visible shaped window below it
at the pointer to be the selected video. Inactive but exposed video hover stays
supported. Companion Settings popups belong to the selected HUD, with cascades
owned by their parent popup, rather than raising the YouTube owner chain.

Native snapping remains enabled at15px. VLC checks registered skin panes and
screen work-area edges, not arbitrary application windows. A covered but still
visible VLC pane can remain a docking target; this differs from snapping to the
application covering it. No snapping threshold or artwork changed here.

Focused private-desktop fixtures exercise source methods and native window
ownership/stacking. They do not establish physical drag feel or user acceptance.
Exact source, helper and unchanged wheel-DLL hashes belong to
hover-stacking-review.json. Coordinated activation is recorded separately.
Packaging remains on hold; no mouse or keyboard control is used.

The matched helper and companion host are now loaded in the owned1x setup.
The fresh165-row checkpoint matched exactly: selected161, paused25seconds,
volume269(105percent), manual portrait1080p and captions off. All six pane
geometries, elapsed clock mode and preferences were preserved. Read-only checks
observed clock phases151/152, wheel binding and the bar's selected-VLC owner.
See hover-stacking-rollout.json. An extra outside-bar popup fixture assertion
has a corrected setup pending rerun; the original86-case passing proof remains
scoped to its exact fixture hash. Physical drag feel remains for user review.
