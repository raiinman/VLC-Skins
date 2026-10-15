# Lower-right pane corner

The transparent-looking black resize bitmap painted a rectangle over the original corner. VLC CtrlImage first caches the image; Windows drawGraphics copies its cached RGB onto the layout with masked SRCCOPY. Alpha 1 makes a pixel participate in the hit/paint mask and does not make that cached copy visually transparent.

The fix keeps the original 23×24 resize area and resizeSE action. Each of seven palettes repeats the matching source corner crop at the existing position, with rightbottom anchors. The crop is (128,33)-(151,57) inside f_bot_right, whose frame origin is (width-164,height-57). At 2x, the complete corner bitmap is resampled before cropping. Transparent outside pixels remain transparent; the grip center remains opaque and hittable.

check_corners.py verifies exact source RGBA, palette selection, five sizes across playlist/video panes, packaged asset equality, and native-style cached RGB copy under an explicit black-cache assumption. It also rejects the previous alpha-1 rectangle. The comparison illustration shows the expected black-cache effect and restored source pixels, not a native screenshot. All native appearance and interaction claims remain pending a later VLC check.

The generic resize_hit resource now contains the blue corner for compatibility with existing derived pane builders. Canonical panes select the matching patch for all seven palettes. Existing YouTube panes embed their source assets and must be rebuilt from the corrected VLT before reloading; a builder using only the generic alias gets the blue patch. No running application, helper source, installed skin or profile was changed.
