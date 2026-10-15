# Keep pane artwork independent of shutter motion

Opening/closing the main shutter switches layouts. The former pane visibility expressions ORed together main layouts of each color. VLC first makes the old layout inactive, then activates the next one. During that gap no palette matched, so frame and corner controls across the panes were hidden and repainted. Native observations reproduced visible rectangular cutouts.

The skin now stores the selected palette in a hidden palette_state window. Its seven 1x1 transparent layouts are metadata, not visible panes. Auxiliary artwork uses palette_N.isActive. Color cycling changes that state before the main color layout; intro replay selects blue. Shutter and clock actions never touch the palette window, including redundant same-layout selections which would recreate the transient false state.

Fresh themes and review launchers start blue. When upgrading a normal profile with an older saved colored layout, close that VLC instance, then run:

    python tools/migrate_palette.py "C:/path/to/vlcrc"

The explicit-file tool derives the color from the saved main layout and appends/replaces only its hidden palette entry. It backs up original bytes, preserves all other pane positions/visibility and preferences, and leaves unrecognized/empty settings unchanged. It never discovers or changes a default user profile. VLC saves the hidden state on later exits. The YouTube companion performs the equivalent synchronization in its private settings builder and inherits the corrected source frame expressions.

Offline checks cover both scales and all 56 main state combinations plus 57 migration cases. A user-authorized native 1x blue companion retest captured shutter travel in both directions with steady YouTube/video borders. Native 2x/all-color/all-pane timing remains outside that limited observation. See shutter-pane-review.json for exact package scope; no screenshots or browser data are included.
