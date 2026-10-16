Current UI refinement packages are documented in [UI-POLISH.md](UI-POLISH.md).
This loading report retains its exact preceding f628/a1bf hashes and measured scope.

# Loading regression fixed; fresh 1x running

Both current packages pass the 30-second initialization gate in the authorized
private-desktop test. [Exact hashes and observations](fast-load-benchmark.json):

| Scale | Initialization | Working set after intro | Private memory after intro |
|---|---:|---:|---:|
| 1x | 8.27 s | 517.8 MiB | 490.4 MiB |
| 2x | 28.27 s | 1807.2 MiB | 1788.1 MiB |

This is one warm-cache run per scale, using copied portable VLC, fresh explicit
configs, silent autoplay and private non-input desktops. It measures autoplay
after interface readiness, not visual timing or control behavior. Three protected
processes stayed alive, the input desktop stayed unchanged, and all 16 guarded
paths, including 11 existing files, were preserved during the test. Cold starts,
timing distributions and full visual/audio parity remain unverified.

The current packages restore atlas batching within 2048x4096 and use standard
Pillow compressed PNGs, with PNG entries stored as ZIP_STORED inside the VLT.
The discarded custom filter0 PNG writer is no longer used. Original RGBA pixels,
alpha, frame counts, fps and loops remain the equivalence requirements.

Only the 14 tall 2x Info rail strips, info_frame_[1-7]_[23], change from two to four
horizontal bands. Their 15 frames still run at 20 fps for the same 700 ms fade.
Smaller regions reduce Win32 CombineRgn construction work; they add band controls
and timers without changing the reconstructed image. All other band policies,
including main startup, shutter and Info page fades, remain unchanged.

File size and memory are reported tradeoffs. The user prioritizes original
presentation and loading; reduced bitmap allocation is not an acceptance gate.
Structural allocation estimates remain separate from measured process memory.
The 2x retained-bitmap estimate increases by 1.75 MiB against the comparison
baseline; this is a reported cost, not a failed memory-reduction requirement.

fast-loading-equivalence.json records exact package hashes and the actual-ZIP
pixel/timing/control comparison. Its oracle reconstructs logical Info strips
from either two or four bands before comparing every RGBA pixel and active
draw/control order across 54 Info routes plus no-route. Reband fixtures include
alpha 0/1/127/254/255 and hidden RGB, and reject seven mutations: missing band,
position, fps, feedback resource, visibility gate, pixel and transparency key.
The exact-package equivalence comparison and all 17 conversion/visual checks
passed. The combined-layer audit has 714 exact cases and 42 explained residual
cases, with zero unexplained cases; it does not certify native visual parity.

Earlier candidates measured 16.48/38.38, 8.28/30.92 and 12.88/33.03 seconds at
1x/2x; all failed the 2x gate. Their records remain historical and do not describe
the current packages.

Both packages are installed in the user's APPDATA VLC skin library, with prior
files backed up and installed hashes verified. The Program Files library update
was denied and its files remain unchanged. [Installation evidence](fresh-skin-install.json)
is separate from the running player.

The coordinated companion restart is complete. The running 1x source hash matches
the tested package, with the matching compact helper and private Lua volume
observer. All158 queue IDs/order, selected ordinal0, paused2-second position,
volume243 and saved pane geometry were preserved. The playlist retains its
position, while VLC clamps its old420x320 size to the approved440x340 minimum;
main/video/YouTube actual geometry remains unchanged.
Native1280x720 audio/video decoding passed; normal settings and other private
preferences were retained. Source asset bytes and storage methods survived the
YouTube derivation. Old owned processes closed; no mouse/keyboard input was used.
Exact source/derived/helper/OSD hashes and process identities are recorded in
[fresh-1x-rollout.json](fresh-1x-rollout.json). Native pointer-driven hover and
visual OSD appearance remain untested; this is not full parity acceptance.

The matching helper also fixes stale-location hover activation: remembered pane
bounds alone cannot open controls. It now requires a visible, nonminimized video
pane and its actual exposed window under the pointer, or the already-open bar.
Compiler/pure exposure and both-scale hover/effects checks pass; native pointer
verification is pending. See hover-visibility-review.json for the exact helper.
