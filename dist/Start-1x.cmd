@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-NFS.ps1" -Scale 1
exit /b %errorlevel%
