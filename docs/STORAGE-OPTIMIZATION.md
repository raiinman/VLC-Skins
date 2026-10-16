# Lossless startup and memory work

The previous 2x package loaded in 29.55 seconds with about 1805 MiB working memory.
Those native measurements remain bound to its exact hash in info-load-benchmark.json.
The new packages are prepared offline; no VLC process or helper was launched,
no input/focus was controlled, and no installed skin, profile or companion file
was updated. The other chat owns the running pinned 1x session.

VLC's Builder::addSubBitmap allocates and copies a separate RGBA buffer from its
parent FileBitmap. The parent remains resident. The converter previously packed
large animation bands into atlases, duplicating almost all their decoded data.
It now batches only resources with at most 65,536 total pixels into atlases; large
art and animation bands load from their existing exact standalone PNGs instead.
Horizontal animation band geometry, frame counts, 20 fps fades and loops stay intact.

CtrlImage also allocates its own graphics cache even while hidden. Identical
static Info-page backings now share one Image with mutually exclusive route OR
visibility. They remain below active route content. The first existing ID is
retained; assigning IDs before sharing prevents unrelated controls being renamed.
No animated control is shared or removed, so transition restart/timer behavior
does not change. Legacy Info layouts, fonts, geometry, controls and sound payloads
remain available.

The offline comparison reads the actual old and new VLT archives. It compares
every logical bitmap's complete RGBA bytes, dimensions, frame count, fps and loop;
all non-image payloads; all other XML; and active paint/control order for all 54
Info routes plus the no-route state. The Info checker separately verifies source
pixels, 54 states, 590 endpoint control checks and 20 rejected mutations per scale.
The storage checker has six corruption/mutation fixtures of its own.


| Offline allocation reduction | 1x | 2x |
| --- | ---: | ---: |
| Retained bitmap RGBA | 171.08 MiB | 675.50 MiB |
| Initial static Image cache estimate | 11.01 MiB | 44.05 MiB |

These are two distinct allocation categories, not an observed process-memory
measurement. The 2x package is slightly larger on disk (about 176 MiB versus
171 MiB), because separate PNGs compress differently; image quality is unchanged.
Small sprites stay batched to limit decoder-open overhead. Actual startup time
could depend on that overhead and storage/cache state, so no speedup is claimed
before the later native test.

Exact package hashes and allocation savings are in storage-optimization-review.json.
Retained bitmap counts model FileBitmap RGBA plus separately copied SubBitmap
RGBA. Initial CtrlImage cache dimensions are counted separately. These exclude
other graphics, decoder temporaries and general VLC allocations; they are not
measured RSS or a new startup-time result. More PNG files trade decoder-open
overhead against far fewer retained copies and cache constructions. The 30-second
native gate remains; actual timing and process memory need a later authorized
isolated native test. Cold starts and native visual behavior remain unverified.

Both verified packages, matching launchers/helper/scripts and current docs are
staged together in NFS-Current-Offline with a manifest. Future verified fixes
refresh this offline bundle. Launching it later is a manual user action; staging
never changes an already-running player or its selected skin.

Implementation references: [resource creation](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/parser/builder.cpp),
[bitmap buffers and shared graphics](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/src/generic_bitmap.cpp),
[initial Image cache](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/controls/ctrl_image.cpp),
and [animation timers](https://github.com/videolan/vlc/blob/3.0.x/modules/gui/skins2/src/anim_bitmap.cpp).
