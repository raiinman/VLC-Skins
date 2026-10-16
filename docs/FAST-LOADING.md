# Loading regression fixed; visible 1x handoff pending

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

The authorized companion handoff covers a fresh visible 1x derivation,
helper changeover and owned restart, preserving the 158-item queue, selected
item, playback position/state, volume and settings. Live confirmation is PENDING;
the existing session remains protected until the coordinated handoff. Record
actual live source/helper hashes and observations in fresh-1x-rollout.json when
available. Installation and successful loading do not establish live adoption.
