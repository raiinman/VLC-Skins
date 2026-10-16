# Filename, hover strip and tooltip corrections

Both scales now place the main filename two source pixels below its backing's
top edge (text y=119; backing y=117). Font size, backing, gauges and logo are
unchanged. The speaker, Settings and CC glyphs are smaller and inset inside crisp dark
beveled faces, with distinct normal, hover and pressed feedback. The compact bar uses a flat matching smoked-charcoal
fill (RGB 13,17,21), retaining its rounded silhouette and subtle border.
Framed opacity is now 255/255, so video detail cannot bleed through the strip.
No textured tile or grain remains. Native fullscreen fading remains VLC-owned.

Framed hover and expanded volume now work while another app is active. The
helper still requires the actual window under the pointer to be the exposed
selected-player video or already-open bar, and rejects hidden/minimized/covered
or remembered old rectangles. No focus change is required.

The missing tooltip root cause was the preceding custom 16px font binding.
VLC 3.0.23 builds Theme before custom Fonts; tooltipfont="tooltip" resolved to
nothing and no native tooltip was created. The correction uses built-in
`defaultfont` (12px). The helper keeps native show/hide and moves only the exact
selected-PID tooltip above the pointer, including inactive-window hover.
The private Lua data directory also includes unchanged FreeSans.ttf, skin.dtd
and skin.catalog so VLC_DATA_PATH retains native Skins2 resource lookup.

All 17 conversion/visual checks pass at both scales. The layer audit has 714 exact
cases and 42 documented closed-main residuals, with zero unexplained cases.
Centered glyph/ring clearance, flat interior, filename border inset, native
controls and mutation rejection are independently checked. Asset-only previews
are available separately; they do not prove native glyph placement or scrolling.

Exact package/helper hashes are in ui-polish-review.json. Private actual-skin
native hover/tooltip evidence is recorded in native-hover-review.json: 78 checks
passed, including real embedded video children, exposed/hidden/minimized/covered
windows, old rectangles, restoration, bar retention and private-desktop identity.
Native tooltip windows were created on both skins. The optional 500ms private
motion probe did not produce a visible tooltip, so timer-driven display and
above-pointer appearance remain unverified by the private fixture. All test
processes closed; four protected processes, 23 unique guard paths and the input
desktop were unchanged. All eight synthetic/actual-bar opacity readbacks were
255 with LWA_ALPHA and layered style. The fixture compiles shared product
source and calls its methods; it does not launch the packaged helper EXE.
The first run failed a2xcover assertion without confirming native coverage.
That failed report remains in native-hover-opacity-first-attempt.json. The
next fixture explicitly established coverage before the unchanged strict
rejection check; both scales passed. The first failure's precise cause is not
proven by the later pass.
Installation and the companion's coordinated running1x update are separate
records. The earlier 8.27/28.27-second measurements remain scoped to the preceding
f628/a1bf packages in fast-load-benchmark.json; this cosmetic revision does not
inherit those exact-hash measurements or a 100% parity certification.

A read-only probe of the updated running 1x player found exactly one native
tooltip with the expected class/style/owner and fixed caption. It was actively
visible at105x21 pixels. The probe did not capture text pixels or measure
above-pointer placement. Companion Settings/CC menu testing is recorded
separately from the private both-scale exposure checks.

The current coordinated1x rollout is confirmed in ui-polish-rollout.json. The
companion observed a solid charcoal strip without video bleed and smaller
inset gear/CC/speaker glyphs in beveled circles. All159 ordered queue rows,
manual1080p, captions on, paused0:02, latest volume256, six pane geometries,
private preferences and normal VLC settings were preserved. Original asset
bytes and compression remain intact. No inactive2x profile was created.
The2x exact-package private tests pass; physical2x appearance is not certified.
