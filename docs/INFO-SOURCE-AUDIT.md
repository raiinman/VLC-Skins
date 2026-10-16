# What accompanies the original information sound

The supplied archive contains no missing Info video. Opening infoView calls
loadInfoPrefs(): it saves the open state, initializes size and frame palette,
then plays imode.wav. The18.043-second file is PCM audio only. The original
info view has no video control, movie assignment, download or timed slideshow.

Its menu/car artwork and pages are static images: one About page, four Story
pages, nine Screenshots pages and one Web Destinations page. The original does
have short visual transitions: selected pages fade from alpha50 to255 over
400ms, returning to the menu fades out over500ms, and palette-frame changes
use a default700ms fade. These are not synchronized to the18-second sound.
The subsequent offline candidate restores page and frame fades on both scales;
INFO-FADES.md records its native implementation, verification and transient
limitations. It does not add an invented Info cinematic.

All247 archive members were checked against the extracted source and provenance
CRCs:217PNG,22JPEG, one GIF, five WAV, one WMS and one JavaScript file. Every
image decoded. The only animated image is intro_anim.gif:59frames at100ms each,
used by the separate main-player startup with intro4.wav. User-media video
controls belong to other views, not infoView. No movie asset was omitted.

info-source-audit.json records callback/resource references and scope. These
findings concern the supplied archive; unrelated historical downloads were
not examined. Source scripts were inspected as reference data, not executed.
