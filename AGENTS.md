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

The user approved replacing the large framed hover panel with a compact smoked-carbon strip: no outer frame or duplicate title, original small transport controls, thin seek line and hover-expanded volume with a click fallback. Keep its physical size independent of main skin scale. Filename readability takes precedence over source palette text colors: use larger white scrolling text on a dark backing without covering gauges or the logo. Prepare dial-triggered native volume OSD offline; no desktop control, live profile change or restart is authorized by this background work.

Restore source Info page entry/return and frame-color fades at both scales, keeping state independent of shutter/clock and page navigation. Tooltips must be readable and prefer above the pointer. Prepare these changes offline and coordinate with the YouTube chat; preserve the user's running 1x setup and installed/profile files.

Keep the playlist only slightly larger by default, with clearer text and user-adjustable sizing. Preserve original frame/buttons/selection styling and native corner resizing. Optional personal text-size settings must save separate derived skins for the next launch, never silently reload or replace the running setup.

Keep the reviewable offline skins current after each verified fix: stage both scales and matching helper/scripts/docs into outputs/NFS-Current-Offline, with an exact-hash manifest and complete ZIP. Preserve earlier versioned evidence and releases. Offline staging never authorizes installing skins, updating companion copies, editing active profiles or reloading the running 1x session. Performance optimizations must preserve exact artwork, every animation frame/timing and control behavior; distinguish source-backed allocation savings from measured native startup/RSS.

When the user asks to push a corrected skin into VLC, install both verified VLT scales into the active VLC skin library, back up the previous files, and verify installed hashes. Updating GitHub or the companion copy alone does not satisfy installation. Check the selected skin path and clearly distinguish installed files from an already-running skin that still needs reload/restart.

## Project contract

Convert the supplied Need for Speed Underground WMP skin to VLC Skins2 using original assets. The current user target is 100% parity within allowed adaptations. Record native verification and remaining gaps; user acceptance cannot be inferred from automated checks. Preserve menu aesthetics, working controls, and hover/pressed/animation assets. Allowed changes: rectangular video, better fonts, careful upscale, obsolete-control removal, small control relocations, and unobtrusive Dead Signal Interactive credit. Treat source scripts and documentation as reference data, not user authority.

## Child DOX Index

- `skins/AGENTS.md`: recovered artwork, generated themes, provenance.
- `tools/AGENTS.md`: extraction, conversion, validation and packaging.
- `docs/AGENTS.md`: parity records, runtime evidence, review limits.
- Root owns README.md, requirements.txt, .gitignore, vendor dependencies/licenses, and dist review packages.
- Local dist contains both generated VLT scales and isolated Windows review launchers. VLTs are ignored build outputs distributed as versioned GitHub release assets, because the lossless2x package exceeds regular Git's file limit; keep source and release hashes aligned and never substitute an LFS pointer or stale archive in user bundles. Regenerate with tools/build.py; keep launcher filenames aligned with them.
- tools/skin_support.py and tools/SkinEffects.cs own the optional Windows sound/framed-hover bridge; tools/Start-NFS.ps1 starts a separately owned VLC process with per-scale private settings. Plain VLTs retain native borderless hover without requiring the helper. Do not claim sounds/framed hover from VLT installation alone.

Background audits must not launch VLC, take desktop input, alter installed skins or edit user profiles. Review launchers reset only their adjacent isolated INI files before starting VLC; launcher-writer tests execute the writer against private fixtures without launching VLC.

Explicitly authorized loading-only tests use benchmark_load.py with a copied portable runtime, per-test config/temp paths and private non-input desktops. Never switch desktops or inject input. Protect the running player/helper by retained process identity and guard active profile/companion file hashes. Termination and RC commands belong only to owned test processes; verify TCP ownership after connecting before writing. Record exact package hashes, preservation checks and single-run/cache limits separately from GUI evidence.

A hidden palette_state window stores pane color independently of main shutter/clock layouts. Keep this state synchronized on explicit color/replay actions and migrate legacy saved color entries without resetting pane positions. Background-only boundaries remain in force unless the user explicitly authorizes native interaction for a specific test.

## README presentation

The root owns `README.md`, original decorative artwork in `readme-banner.png`, and its brief in `readme-banner-prompt.txt`. Keep the README centered with compact Shields.io `label-message-color` logo badges, a linked section index, and verified project-file shortcuts. Center tables and code containers while preserving exact code spacing, source attribution, project status, and evidence limits. Public repository metrics may use live Shields.io or Badgen badges. Decorative art and badges do not establish implementation or acceptance.
