@echo off
setlocal
set "VLC=%ProgramFiles%\VideoLAN\VLC\vlc.exe"
if not exist "%VLC%" set "VLC=%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe"
if not exist "%VLC%" (
  echo VLC was not found. Select the VLT in VLC Preferences, Interface, Use custom skin.
  pause
  exit /b 1
)
set "NFS_REVIEW_CONFIG=%~dp0parity-1x-vlcrc.ini"
set "NFS_REVIEW_SKIN=%~dp0Need-for-Speed-Underground-1x.vlt"
if not exist "%NFS_REVIEW_SKIN%" (
  echo The bundled 1x skin was not found. Extract the complete review package first.
  pause
  exit /b 1
)
powershell.exe -NoLogo -NoProfile -NonInteractive -Command "try { [System.IO.File]::WriteAllLines($env:NFS_REVIEW_CONFIG, @('[skins2]', ('skins2-last=' + $env:NFS_REVIEW_SKIN), 'skins2-config='), [System.Text.UTF8Encoding]::new($false)); exit 0 } catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }"
if errorlevel 1 (
  echo Review settings could not be reset. VLC was not started.
  pause
  exit /b 1
)
start "" "%VLC%" --no-one-instance --no-media-library --no-metadata-network-access --no-qt-privacy-ask --config="%NFS_REVIEW_CONFIG%" --intf=skins2
