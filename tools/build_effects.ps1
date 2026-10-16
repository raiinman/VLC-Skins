param([string]$Destination = (Join-Path $PSScriptRoot '..\dist\skin-support'))
$ErrorActionPreference = 'Stop'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) {
    $compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
}
if (-not (Test-Path -LiteralPath $compiler)) { throw '.NET Framework 4 compiler was not found.' }
$null = New-Item -ItemType Directory -Force -Path $Destination
$output = Join-Path (Resolve-Path -LiteralPath $Destination).Path 'SkinEffects.exe'
$source = Join-Path $PSScriptRoot 'SkinEffects.cs'
& $compiler /nologo /target:winexe /platform:anycpu /optimize+ "/out:$output" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll /reference:System.IO.Compression.dll /reference:System.IO.Compression.FileSystem.dll $source
if ($LASTEXITCODE -ne 0) { throw 'Skin effects compilation failed.' }
$test = Start-Process -FilePath $output -ArgumentList '--self-test' -WindowStyle Hidden -Wait -PassThru
if ($test.ExitCode -ne 0) { throw 'Skin effects pure self-test failed.' }
$luaDirectory = Join-Path (Split-Path -Parent $output) 'data/lua/intf'
$null = New-Item -ItemType Directory -Force -Path $luaDirectory
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'nfs_volume_osd.lua') -Destination (Join-Path $luaDirectory 'nfs_volume_osd_v1.lua') -Force
$fontDirectory = Join-Path (Split-Path -Parent $output) 'data/skins/fonts'
$null = New-Item -ItemType Directory -Force -Path $fontDirectory
Copy-Item -LiteralPath (Join-Path $PSScriptRoot '../vendor/FreeSans.ttf') -Destination (Join-Path $fontDirectory 'FreeSans.ttf') -Force
$skinDataDirectory = Split-Path -Parent $fontDirectory
foreach ($resource in @('skin.dtd', 'skin.catalog')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot ('../vendor/' + $resource)) -Destination (Join-Path $skinDataDirectory $resource) -Force
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'companion_hud_apply.py') -Destination (Join-Path (Split-Path -Parent $output) 'companion_hud_apply.py') -Force
$packageDirectory = Split-Path -Parent (Split-Path -Parent $output)
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Start-NFS.ps1') -Destination (Join-Path $packageDirectory 'Start-NFS.ps1') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Playlist-Text-Size.ps1') -Destination (Join-Path $packageDirectory 'Playlist-Text-Size.ps1') -Force
$customizerLauncher = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0Playlist-Text-Size.ps1`"`r`nexit /b %errorlevel%`r`n"
[System.IO.File]::WriteAllText((Join-Path $packageDirectory 'Playlist-Text-Size.cmd'), $customizerLauncher, [System.Text.Encoding]::ASCII)
foreach ($scale in 1, 2) {
    $launcher = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0Start-NFS.ps1`" -Scale $scale`r`nexit /b %errorlevel%`r`n"
    [System.IO.File]::WriteAllText((Join-Path $packageDirectory "Start-${scale}x.cmd"), $launcher, [System.Text.Encoding]::ASCII)
}
Write-Output "Compiled $output; pure manifest/hover self-test passed. No VLC, audio or desktop API test was run."
