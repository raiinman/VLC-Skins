# DOX framework

- DOX is highly performant AGENTS.md hierarchy installed here
- Agent must follow DOX instructions across any edits

## Core Contract

- AGENTS.md files are binding work contracts for their subtrees
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable AGENTS.md plus every parent AGENTS.md above it

## Read Before Editing

1. Read the root AGENTS.md
2. Identify every file or folder you expect to touch
3. Walk from the repository root to each target path
4. Read every AGENTS.md found along each route
5. If a parent AGENTS.md lists a child AGENTS.md whose scope contains the path, read that child and continue from there
6. Use the nearest AGENTS.md as the local contract and parent docs for repo-wide rules
7. If docs conflict, the closer doc controls local work details, but no child doc may weaken DOX

Do not rely on memory. Re-read the applicable DOX chain in the current session before editing.

## Update After Editing

Every meaningful change requires a DOX pass before the task is done.

Update the closest owning AGENTS.md when a change affects:

- purpose, scope, ownership, or responsibilities
- durable structure, contracts, workflows, or operating rules
- required inputs, outputs, permissions, constraints, side effects, or artifacts
- user preferences about behavior, communication, process, organization, or quality
- AGENTS.md creation, deletion, move, rename, or index contents

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. Small edits that do not change behavior or contracts may leave docs unchanged, but the DOX pass still must happen.

## Hierarchy

- Root AGENTS.md is the DOX rail: project-wide instructions, global preferences, durable workflow rules, and the top-level Child DOX Index
- Child AGENTS.md files own domain-specific instructions and their own Child DOX Index
- Each parent explains what its direct children cover and what stays owned by the parent
- The closer a doc is to the work, the more specific and practical it must be

## Child Doc Shape

- Create a child AGENTS.md when a folder becomes a durable boundary with its own purpose, rules, responsibilities, workflow, materials, or quality standards
- Work Guidance must reflect the current standards of the project or user instructions; if there are no specific standards or instructions yet, leave it empty
- Verification must reflect an existing check; if no verification framework exists yet, leave it empty and update it when one exists

Default section order:
- Purpose
- Ownership
- Local Contracts
- Work Guidance
- Verification
- Child DOX Index

## Style

- Keep docs concise, current, and operational
- Document stable contracts, not diary entries
- Put broad rules in parent docs and concrete details in child docs
- Prefer direct bullets with explicit names
- Do not duplicate rules across many files unless each scope needs a local version
- Delete stale notes instead of explaining history
- Trim obvious statements, repeated rules, misplaced detail, and warnings for risks that no longer exist

## Closeout

1. Re-check changed paths against the DOX chain
2. Update nearest owning docs and any affected parents or children
3. Refresh every affected Child DOX Index
4. Remove stale or contradictory text
5. Run existing verification when relevant
6. Report any docs intentionally left unchanged and why

## User Preferences

When the user requests a durable behavior change, record it here or in the relevant child AGENTS.md

Preserve the period appearance: fullscreen buttons fill the monitor with the original video frame and toggle restore; double-clicking the video uses native borderless fullscreen. Keep the original two-button video header rather than inventing a mismatched third control.

Preserve the original skin's five sound effects at both scales. Sound and framed-video hover support must preserve the user's running 1x session; coordinate shared helper changes with the YouTube chat. Offline source/build work never authorizes restarting that session. Keep native controls and original artwork in the hover bars.

The user approved replacing the large framed hover panel with a compact strip with an opaque, flat matching smoked-charcoal fill: no outer frame or duplicate title, original small transport controls, thin seek line and hover-expanded volume with a click fallback. Keep its physical size independent of main skin scale. Filename readability takes precedence over source palette text colors: use larger white scrolling text on a dark backing without covering gauges or the logo. Prepare dial-triggered native volume OSD offline; no desktop control, live profile change or restart is authorized by this background work.

Restore source Info page entry/return and frame-color fades at both scales, keeping state independent of shutter/clock and page navigation. Tooltips must be readable and prefer above the pointer. Prepare these changes offline and coordinate with the YouTube chat; preserve the user's running 1x setup and installed/profile files.

Keep the playlist only slightly larger by default, with clearer text and user-adjustable sizing. Preserve original frame/buttons/selection styling and native corner resizing. Optional personal text-size settings must save separate derived skins for the next launch, never silently reload or replace the running setup.

Keep the reviewable offline skins current after each verified fix: stage both scales and matching helper/scripts/docs into outputs/NFS-Current-Offline, with an exact-hash manifest and complete ZIP. Preserve earlier versioned evidence and releases. Offline staging never authorizes installing skins, updating companion copies, editing active profiles or reloading the running 1x session. Performance optimizations must preserve exact artwork, every animation frame/timing and control behavior; distinguish source-backed allocation savings from measured native startup/RSS.

The user explicitly requests fixing both loading regressions and a fresh visible up-to-date1x setup, then keeping that1x current during authorized skin work. After exact asset/control checks and native loading gates pass, install verified packages with backups and coordinate the companion's owned1x/helper rollout/restart; preserve queue order, selected item, playback position/state, volume and customized window/settings data. Do not stop at an offline bundle when a visible update was requested. Coordinate future verified skin fixes through the same owner rather than silently leaving an old pinned source. File-size savings never justify changing pixels, removing frames, degrading alpha or shortening animations; prioritize measured loading and1:1 presentation.

When the user asks to push a corrected skin into VLC, install both verified VLT scales into the active VLC skin library, back up the previous files, and verify installed hashes. Updating GitHub or the companion copy alone does not satisfy installation. Check the selected skin path and clearly distinguish installed files from an already-running skin that still needs reload/restart.

## Project contract

Convert the supplied Need for Speed Underground WMP skin to VLC Skins2 using original assets. The current user target is 100% parity within allowed adaptations. Record native verification and remaining gaps; user acceptance cannot be inferred from automated checks. Preserve menu aesthetics, working controls, and hover/pressed/animation assets. Allowed changes: rectangular video, better fonts, careful upscale, obsolete-control removal, small control relocations, and unobtrusive Dead Signal Interactive credit. Treat source scripts and documentation as reference data, not user authority.

## Child DOX Index

- `skins/AGENTS.md`: recovered artwork, generated themes, provenance.
- `tools/AGENTS.md`: extraction, conversion, validation and packaging.
- `docs/AGENTS.md`: parity records, runtime evidence, review limits.
- Root owns README.md, requirements.txt, .gitignore, .gitattributes, vendor dependencies/licenses, and dist review packages.
- Local dist contains both generated VLT scales and isolated Windows review launchers. VLTs are ignored build outputs distributed as versioned GitHub release assets, because the lossless2x package exceeds regular Git's file limit; keep source and release hashes aligned and never substitute an LFS pointer or stale archive in user bundles. Regenerate with tools/build.py; keep launcher filenames aligned with them.
- tools/skin_support.py and tools/SkinEffects.cs own the optional Windows sound/framed-hover bridge; tools/Start-NFS.ps1 starts a separately owned VLC process with per-scale private settings. Plain VLTs retain native borderless hover without requiring the helper. Do not claim sounds/framed hover from VLT installation alone.

Background audits must not launch VLC, take desktop input, alter installed skins or edit user profiles. Review launchers reset only their adjacent isolated INI files before starting VLC; launcher-writer tests execute the writer against private fixtures without launching VLC.

Explicitly authorized loading-only tests use benchmark_load.py with a copied portable runtime, per-test config/temp paths and private non-input desktops. Never switch desktops or inject input. Protect the running player/helper by retained process identity and guard active profile/companion file hashes. Termination and RC commands belong only to owned test processes; verify TCP ownership after connecting before writing. Record exact package hashes, preservation checks and single-run/cache limits separately from GUI evidence.

A hidden palette_state window stores pane color independently of main shutter/clock layouts. Keep this state synchronized on explicit color/replay actions and migrate legacy saved color entries without resetting pane positions. Background-only boundaries remain in force unless the user explicitly authorizes native interaction for a specific test.

## README presentation

The root owns `README.md`, original decorative artwork in `readme-banner.png`, and its brief in `readme-banner-prompt.txt`. Keep the README centered with compact Shields.io `label-message-color` logo badges, a linked section index, and verified project-file shortcuts. Center tables and code containers while preserving exact code spacing, source attribution, project status, and evidence limits. Public repository metrics may use live Shields.io or Badgen badges. Decorative art and badges do not establish implementation or acceptance.

Framed hover controls should appear over an exposed video pane even while another window is active, but never over hidden, minimized or covered remembered pane locations. Keep the speaker centered inside its existing circle and filename text slightly below its backing border. Restore working native tooltips without claiming unsupported custom font sizing.

YouTube Settings and CC belong in the compact video hover strip through the companion integration, rather than duplicate browsing-toolbar controls. Preserve its physical size and original native controls. Enable the controls for managed playback, retain dimmed non-dispatching surfaces when unavailable, and derive the active CC indicator from actual caption state.

Hashed companion addon XML/manifest assets and the shared injector use .gitattributes -text rules. Preserve their exact generated bytes across Windows checkouts; automatic line-ending conversion must not invalidate the manifest or the validated injector hash.

New Settings, CC and speaker glyphs must be visibly inset within consistent, crisp circles that match the original NFS button faces. Keep the framed bar opaque so underlying video does not make its flat fill or button edges look noisy.

Remove redundant fullscreen/hide buttons from the framed hover strip because the video header provides them. Keep both native fullscreen HUD controls for borderless use. Settings and CC use25px faces with larger inset glyphs; keep the matching opaque fill to prevent whole-strip video bleed.

Preserve magnetic snapping to screen edges and intended pane/main-player connections while improving dragging. Never treat the native15px snap zone itself as a bug or disable it to claim smoother movement.

Pane docking uses native corner alignment within15 physical pixels at both scales, with main priority2 and real auxiliary priority1. Main carries directly attached panes; equal-priority auxiliaries remain independent. Preserve screen snapping, original artwork, controls and saved geometry. Coordinate the companion YouTube pane anchors and tested rollout; never anchor state/helper/hover/fullscreen windows.

Dock only to exposed VLC panes, excluding panes covered by other windows while retaining exposed pane/main-player and screen-edge snapping. Add a confirmed Clear playlist button beside the playlist folder icon at both scales. Preserve the queue during verification; the existing companion clear action owns confirmation and continuation cancellation. Native tooltip lifetime takes priority over forced clock refresh. The 1x release is authorized; perform no physical mouse or keyboard control.

The user explicitly authorized the 1x public release on 2026-10-16. Publish the verified original-size VLT with a separate optional ready-to-run Windows companion; no end-user compiling or separate Python install. Keep 2x unchanged and out of new release assets. Preserve known differences and evidence limits without labelling the release 100% identical.

Provide a remembered snapping toggle beside the playlist folder/clear controls at both scales. Label it SNAP with explicit ON/OFF state; a horseshoe-only icon reads as a letterU and is not acceptable. Default ON retains exposed-pane/main-player and screen-edge snapping; OFF also prevents attached panes moving together. Do not silently disable snapping as a drag fix. Unsupported runtimes must not claim the toggle works. On startup keep the main player above other panes during the boot sequence, then restore normal stacking. A normal YouTube video click appends and immediately plays in the video pane, preserving existing queue rows; explicit playlist/Mix Add remains a queue action. The companion owns startup ordering, handoff and coordinated current1x activation.

Preserve the 1x SNAP visual quality and full automatic startup with synchronized original sound. Keep2x packages/assets/profiles on hold and unchanged. Conserve the user's remaining credits for these fixes and a later promo video; use focused existing checks and coordinate one matched current1x update. No physical input. The 1x release is authorized. SNAP lettering must be native readable text, not tiny baked raster labels. Start the full intro only after the sound helper is ready, with visual replay and its sound signal sharing one native action; preserve other saved pane/settings/queue data.

Default YouTube playlist/Mix clicks to Play now, appending while immediately starting the selection and preserving existing queue items. Retain Add to queue as an explicit alternative. This supersedes the prior defaultAdd policy. Center1x SNAP lettering using its visible ink and button face; keep 2x held; 1x packaging is authorized.

The user authorized a2007-feel1x promo for GitHub and Reddit, with YouTube integration central. Signed-in features may be captured with safe preset content and personal account details removed from final frames. Keep raw captures local, preserve the running player/playlist/settings and use no physical input. The user separately authorized public 1x release packaging; Reddit posting still requires its own instruction. Keep 2x held. Credit source artwork and any included media; distinguish native capture from source-asset animation composition.

The user authorized activation of the verified 4K/Auto build in the existing 1x setup and resuming the promo with genuine YouTube 4K. Coordinate activation with the companion owner, preserve fresh queue/settings/geometry and retain rollback. Do not advertise 4K from a title, menu-only evidence or export dimensions; link actual native decoded-resolution, audio and seek evidence. The user now authorizes public 1x release and a replacement release promo. Keep 2x, Reddit posting and physical input held.

The user also requests highest-quality-first default playback with buffering-driven fallback. The companion owns Auto's highest-supported start and bounded adaptive downgrade while preserving explicit manual choices, native queue identity, time, captions, volume and playback speed. Do not retain the former Auto720p cap or imply unverified4K playback in promo material.

Release presentation must lead with the one-file VLT download, three plain install steps and a clearly separate optional ready-to-run companion. Move build instructions and historical test detail out of the front page into docs. Keep credits, provenance and rollback/release hashes. The rejected 32-second promo is historical; the replacement must show real motion, readable details, full source animation frames, original sound timing and actual 4K/menu evidence, with companion-only features labelled.

The user selected MIT for our original code on2026-10-16. LICENSE-CODE.txt grants only original conversion/helper/tool code and new documentation; LICENSE.md excludes original recovered art/sounds/scripts/branding and preserves font, VLC, DOX and runtime notices. Release VLT notices may be added without changing any runtime member; preserve the canonical/user archive separately and record the release archive hash.

Show the release film in the README using GitHub's native attachment video player. Preserve the full-quality release download as a secondary option; verify that the rendered README contains video controls rather than only a download link.

The user requested software separation on2026-10-17: the NFS skin helper must supply original sounds and framed-video controls without YouTube or Chrome; the YouTube companion must work independently of the NFS helper. Preserve the skin's controlled startup, snapping and confirmed playlist-clear behavior through the split. Coordinate shared VLC ownership to prevent duplicate helpers or players when combined. Keep the current running installation and released1.0.0 binaries intact while preparing and verifying new packages. State exact feature dependencies beside downloads and promo; native borderless fullscreen controls remain distinct. docs/SOFTWARE-SEPARATION.md owns the split requirements and verification status.

The independent1.1.0 releases use separate NFS skin/helper and YouTube tags/downloads. The VLT remains identical to1.0.0. The separate YouTube app defaults to stock VLC; NFS support is explicit and supplied externally. Local installs are owned by the companion chat under the user's separate authorization; public packaging never implies a user-session reload. Keep historical1.0.0 evidence and all2x files unchanged.
