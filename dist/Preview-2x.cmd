@echo off
setlocal
set "VLC=%ProgramFiles%\VideoLAN\VLC\vlc.exe"
if not exist "%VLC%" set "VLC=%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe"
if not exist "%VLC%" (
  echo VLC was not found. Select the VLT in VLC Preferences, Interface, Use custom skin.
  pause
  exit /b 1
)
start "" "%VLC%" --no-one-instance --no-media-library --no-metadata-network-access --no-qt-privacy-ask --config="%~dp0review-vlcrc.ini" --intf=skins2 --skins2-last="%~dp0Need-for-Speed-Underground-2x.vlt" --skins2-config=
