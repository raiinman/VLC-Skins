# Filename, hover strip and tooltip corrections

Both scales now place the main filename two source pixels below its backing's
top edge (text y119; backing y117). Font size, backing, gauges and logo are
unchanged. The speaker glyph is centered inside its existing23px circle in all
three feedback states. The compact bar uses a flat matching smoked-charcoal
fill (RGB13,17,21), retaining its rounded silhouette, subtle border and85%
framed opacity. No textured tile or new decorative artwork remains in the bar.

Framed hover and expanded volume now work while another app is active. The
helper still requires the actual window under the pointer to be the exposed
selected-player video or already-open bar, and rejects hidden/minimized/covered
or remembered old rectangles. No focus change is required.

The missing tooltip root cause was the preceding custom16px font binding.
VLC3.0.23 builds Theme before custom Fonts; tooltipfont="tooltip" resolved to
nothing and no native tooltip was created. The correction uses built-in
`defaultfont` (12px). The helper keeps native show/hide and moves only the exact
selected-PID tooltip above the pointer, including inactive-window hover.
The private Lua data directory also includes unchanged FreeSans.ttf, skin.dtd
and skin.catalog so VLC_DATA_PATH retains native Skins2 resource lookup.

All17 conversion/visual checks pass at both scales. The layer audit has714exact
cases and42documented closed-main residuals, with zero unexplained cases.
Centered glyph/ring clearance, flat interior, filename border inset, native
controls and mutation rejection are independently checked. Asset-only previews
are available separately; they do not prove native glyph placement or scrolling.

Exact package/helper hashes are in ui-polish-review.json. Private actual-skin
native hover/tooltip evidence is recorded in native-hover-review.json:68checks
passed, including real embedded video children, exposed/hidden/minimized/covered
windows, old rectangles, restoration, bar retention and private-desktop identity.
Native tooltip windows were created on both skins. The optional500ms private
motion probe did not produce a visible tooltip, so timer-driven display and
above-pointer appearance remain unverified. All test processes closed; the three
protected processes,12guard paths and input desktop were unchanged.
Installation and the companion's coordinated running1x update are separate
records. The earlier8.27/28.27-second measurements remain scoped to the preceding
f628/a1bf packages in fast-load-benchmark.json; this cosmetic revision does not
inherit those exact-hash measurements or a100%parity certification.
