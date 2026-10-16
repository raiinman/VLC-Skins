@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Playlist-Text-Size.ps1"
exit /b %errorlevel%
