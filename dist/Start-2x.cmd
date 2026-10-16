@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-NFS.ps1" -Scale 2
exit /b %errorlevel%
