# Info transitions and readable tooltips

Both scales now have native, lossless Info page animations at 20 fps. A selected
JPEG starts at alpha 50 and reaches 255 at 400 ms; returning to the menu reaches
zero at 500 ms. Next/previous transitions retain the previous completed page
underneath. Web Destinations reveals its static link artwork at 400 ms. These
transitions do not alter imode.wav or synchronize to its 18-second duration.

The live Info pane keeps one layout and changes a hidden page state. Its frame
therefore does not restart on page navigation. Explicit color cycling selects a
separate hidden frame state and fades changing frame pixels for 700 ms. Fresh
palettes remain static; intro replay resets the frame trigger.
Shutter/clock actions cannot touch either state. Other panes retain their prior
palette behavior. Legacy Info layout IDs remain usable for saved settings; their
first navigation enters the shared layout without changing pane geometry.
The private launcher resets an existing saved frame trigger to idle while
preserving the Info page/geometry. Ordinary VLC profile restoration can restore
a hidden page/frame transition state and replay its fade on initialization;
XML defaults alone cannot prevent that. No active profile was migrated here.

VLC's CtrlImage does not animate and caches translucent RGB. Animations instead
use CtrlButton/AnimBitmap with identical up/over/down resources, so pointer state
changes do not restart their timers. Oversized strips use two lossless bands.
Frame overlays fade only changing fully opaque pixels; fractional-alpha filtered
edge pixels switch immediately, preserving the existing frame shape and avoiding
bright fringes. The final overlay is transparent and releases frame input.

On return, original menu artwork remains beneath the outgoing page. Timed
one-level-alpha native hit buttons above it forward clicks to the same menu
actions and become fully transparent at 500 ms. This avoids both opaque menu
rows punching through the page and blocked navigation. Their direct bitmap
blend can change a transient channel by one level; hover/pressed feedback falls
back to the original buttons when they release. Exact WMP passThrough/hover
feedback during those 500 ms is not reproduced. Rapid interrupted navigation
uses the previous selected page rather than WMP's arbitrary current-alpha/
last-completed callback state. There is no automatic slideshow. The separate
conversion-credit page has no invented source transition.

Tooltips use a fixed 16 px FreeSans font on both scales, retaining VLC's native
black-on-pale-yellow appearance. VLC hardcodes their position below the pointer;
the optional helper moves only its selected VLC process's native tooltip above
the pointer, with an 8 px gap. It clamps to the pointer monitor's work area and
uses below-pointer placement when the top edge leaves no room. It preserves
VLC's text, show/hide timing and disabled input behavior. It reasserts topmost
without activation, while the selected VLC process has foreground focus.

Tooltip identity requires selected PID, SkinWindowClass, popup/disabled and tool
styles, a same-process owner, then the exact fixed caption `tooltip`. No user
media titles are read or logged. There are no input hooks, pointer movement,
keyboard injection or focus changes. A plain VLT gets the larger font; above-
pointer placement requires the matching helper.

The playlist default increases from 420 × 320 to 440 × 340 source pixels, with
dedicated 12 px text at 1x / 24 px at 2x (previously 10/20) and brighter gray.
Its original frame, red selection, scrollbar, header controls and
lower-right manual resize remain. Saved window sizes may override the new
fresh defaults. Dragging the corner changes pane size independently of text.
The bundle's Playlist-Text-Size.cmd opens a small settings dialog for 1x/2x and
8–48 physical-pixel text. Saving writes only a separate custom VLT/font setting
and hash sidecar. The next dedicated launcher uses it only when source/custom
hashes and scale match; stale or mismatched copies fall back to the bundled
skin. It never reloads VLC, edits active profiles or changes shared artwork.

Offline checks verify all animation pixels, source timings, 54 page states,
navigation ownership, idle suppression, state isolation and rejected mutations.
Helper tests cover tooltip identity and monitor geometry without native calls.
Native animation smoothness and tooltip stacking/DPI behavior remain unverified.
The separately authorized loading-only test in `info-load-benchmark.json` measured
8.27 seconds at 1x and 29.55 seconds at 2x, with no logged theme errors or fallback.
Both survived the intro; the 2x result is close to the 30-second budget. Page strips alone add about 85 MiB decoded RGBA at 1x /
339 MiB at 2x before native graphics copies; lossless PNG compression does not
remove that runtime cost. Total working sets after startup measured about 518 MiB
and 1805 MiB respectively. One warm-cache run per scale under concurrent workload
does not establish cold-start performance or visual fidelity. The tests launched
only owned copies on private non-input desktops. The running 1x player/helper,
installed skins, active profiles and guarded companion files were preserved.

Source references: original nfs.js showInfo/infoNavNext/infoNavPrev/navCheck/
endAlphaBlend and htcpInfo; original nfs.wms infoSub passThrough; VideoLAN
3.0.x modules/gui/skins2/src/tooltip.cpp and win32/win32_tooltip.cpp (historical
checkout paths use modules/skins2), plus cached CtrlButton/AnimBitmap sources.
Context7 returned legacy Skins1 examples; the current Skins2 DTD and native
implementation determine the supported animation and tooltip behavior.
