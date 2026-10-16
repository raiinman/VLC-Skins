# 1x release film

The replacement release film is a product demonstration with a 2007 desktop mood. The rejected preview remains intact. The edit uses exact original artwork and continuous native captures, not generated UI or a slide presentation.

## Direction

- Deliver 1920 × 1080, 60 fps, H.264/AAC with fast-start metadata. Lower-rate recordings retain their real cadence; do not invent intermediate control states.
- The complete edit is 54 seconds. If native fullscreen cannot be captured honestly, `--omit-fullscreen` produces a tighter 48-second film, removing that demonstration and claim rather than padding with an unchanged pane.
- Keep the product dominant. Use restrained charcoal, original carbon detail and blue accents. Macro crops reveal actual original artwork. They are editorial enlargements of the 1x art, not a new 2x skin.
- Preserve all 81 intro frames at their original 10 fps, uninterrupted, with the source cue beginning after its original 1.5-second delay.
- Cut on real action. Show shutters, palettes, Info, playlist and EQ where captured. Follow real YouTube discovery/handoff with moving native 4K playback and its actual quality menu. Show framed and borderless fullscreen only from actual recordings.
- Brief labels explain the distinction between the single VLT skin and optional ready-to-run companion. YouTube, original sounds and framed hover require that companion. Do not imply that exporting at 1080p or displaying a quality menu establishes native 4K.
- Original, restrained rhythmic sound design supports the original effects. Duck the backing around the full intro. Do not imitate a musician or use unlicensed recordings.

## Inputs and privacy

`tools/release_promo.py` accepts an explicit reviewed capture manifest. Each native segment identifies its PNG frame directory or local MP4, cadence, selected source interval, provenance and privacy review. MP4s are decoded into a local sequence without frame interpolation. Where capture timestamps exist, the edit follows those timestamps, not the container's nominal frame rate; a slow capture must not speed up native actions. Account identifiers are excluded before the source is accepted. Generated frames, soundtrack, footage and final media stay outside Git.

The Blender film is credited `(c) 2008 Blender Foundation / www.bigbuckbunny.org`, CC BY 3.0. Original skin artwork: The Skins Factory. VLC conversion: Dead Signal Interactive. Preserve readable credit in the final film and sidecar credits.

## Verification

Record an ordered edit decision list and source hashes. A final render requires explicit observed-action verification for every native segment; discovery-only footage cannot substitute for handoff, and an unchanged framed pane cannot substitute for fullscreen. Probe and fully decode the export. Audit every encoded frame for unexpected black/freeze intervals and inspect original-resolution frames at cuts, labels, boot phases and native control actions. Distinguish expected held source-animation frames from accidental frozen footage. Report audio peak/loudness checks separately from listening; do not claim listening when no audition occurred.

No desktop input, VLC launch, live-profile access or public posting is performed by the renderer. The root release workflow owns distribution and publication. 2x remains on hold.

## Release export

The final film is the approved 48-second edit, `NFS-Underground-VLC-1x-Release.mp4`. Native fullscreen was omitted because its transition was not captured successfully. Native playlist, EQ and Info receive approximately seven seconds at their actual capture cadence; the genuine public-card click is followed by real moving native 4K and its 2160p60 menu. No UI was redrawn. The first 16 seconds use original source-art animation composition, distinct from the following native recordings.

- Export: 1920 × 1080, 60 fps, H.264/AAC stereo, 48 kHz. Lower-rate native capture retains its actual timestamps, without interpolated control states.
- Full decode: 2,880 frames, zero decode errors, zero unexpected black frames; continuous native-playback motion gate passed. Every encoded frame was measured and original-resolution frames were extracted immediately before, at and after each cut.
- Full-resolution review covered boot, palette, native pane details, discovery, moving playback, readable quality selection and final credits. Public Blender content only; no personal account details in final frames.
- Audio measured mean −19.1 dBFS, peak −3.1 dBFS. Original cues are synchronized editorially; listening was not performed and this film is not speaker-audibility evidence.
- SHA256: `cd7e580983be6b0dcb5e9f66fcd5d80b2fd6003aba12fd2a3870de75c423ff08`.

Local output contains the MP4, poster, credits, reviewed source manifest, ordered edit decisions, encoded-frame audit and cut frames. The rejected preview and earlier failed native captures remain separate historical records. Existing preview documentation was intentionally retained as history, not relabeled as this release film.
