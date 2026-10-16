param(
    [ValidateSet(1,2)][int]$Scale = 1,
    [string]$VlcPath,
    [switch]$SelfTest
)
$ErrorActionPreference = 'Stop'

function Set-SkinPath([string]$Text, [string]$SkinPath) {
    $line = 'skins2-last=' + $SkinPath
    if ($Text -match '(?m)^skins2-last=[^\r\n]*') {
        return [regex]::Replace($Text, '(?m)^skins2-last=[^\r\n]*', [System.Text.RegularExpressions.MatchEvaluator]{param($m) $line})
    }
    return $Text + "`r`n[skins2]`r`n" + $line + "`r`nskins2-config=`r`n"
}

function Initialize-SupportState([string]$Text, [int]$AssetScale) {
    $saved = [regex]::Match($Text, '(?m)^skins2-config=([^\r\n]+)')
    if (-not $saved.Success) { return $Text }
    $pattern = '\["([^"\r\n]+)"\s+"([^"\r\n]+)"\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+([01])\]'
    $entries = [regex]::Matches($saved.Groups[1].Value, $pattern)
    $main = @($entries | Where-Object { $_.Groups[1].Value -eq 'main' })
    if ($main.Count -ne 1 -or ([regex]::Replace($saved.Groups[1].Value, $pattern, '')).Trim()) { return $Text }
    $owned = @('nfs_fx_button','nfs_fx_shutter','nfs_fx_intro','nfs_fx_info','nfs_fx_logo','nfs_hover_command','videoHoverController','fullscreenController')
    $parts = @($entries | Where-Object { $_.Groups[1].Value -notin $owned } | ForEach-Object { $_.Value })
    $keys = @('button','shutter','intro','info','logo')
    for ($index=0; $index -lt $keys.Count; $index++) {
        $key = $keys[$index]
        $state = if ($key -eq 'intro' -and $main[0].Groups[2].Value -eq 'main_start') { 'trigger' } else { 'ready' }
        $width = if ($state -eq 'trigger') { 51+$index } else { 41+$index }
        $parts += '["nfs_fx_' + $key + '" "nfs_fx_' + $key + '_' + $state + '" -31000 -31000 ' + $width + ' 17 1]'
    }
    $parts += '["nfs_hover_command" "nfs_hover_command_layout" -31000 -30900 67 17 1]'
    $parts += '["videoHoverController" "video_hover_closed" -31000 -30800 ' + (427*$AssetScale) + ' ' + $AssetScale + ' 1]'
    $parts += '["fullscreenController" "fullscreen_controls" 0 0 ' + (425*$AssetScale) + ' ' + (146*$AssetScale) + ' 0]'
    return $Text.Substring(0,$saved.Groups[1].Index) + ($parts -join '') + $Text.Substring($saved.Groups[1].Index+$saved.Groups[1].Length)
}

if ($SelfTest) {
    $fixture = "[core]`r`nvolume=123`r`n[skins2]`r`nskins2-last=old`r`nskins2-config=saved`r`n"
    $result = Set-SkinPath $fixture "C:\Unicode-é & O'Brien\skin.vlt"
    if (-not $result.Contains('volume=123') -or -not $result.Contains('skins2-config=saved') -or $result.Contains('skins2-last=old')) { throw 'Private config preservation failed.' }
    if ((Set-SkinPath '' 'C:\skin.vlt') -notmatch 'skins2-last=C:\\skin.vlt') { throw 'Fresh profile failed.' }
    foreach ($assetScale in @(1,2)) {
        $geometry = '["main" "main_3" -5 20 300 298 1]["video" "video_1" 8 9 1234 987 1]'
        $migrated = Initialize-SupportState ("skins2-config="+$geometry) $assetScale
        if (-not $migrated.Contains($geometry) -or -not $migrated.Contains('"nfs_fx_button" "nfs_fx_button_ready"') -or -not $migrated.Contains('"video_hover_closed"')) { throw 'Support state migration failed.' }
        if ((Initialize-SupportState $migrated $assetScale) -ne $migrated) { throw 'Support state migration must be idempotent.' }
    }
    Write-Output 'PASS private launcher configuration; no process or user profile accessed.'
    exit 0
}

# This file ships beside the VLTs. Source-tree invocation uses dist/ instead.
$bundle = $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $bundle "Need-for-Speed-Underground-$($Scale)x.vlt"))) {
    $bundle = Join-Path (Split-Path $PSScriptRoot -Parent) 'dist'
}
$skin = Join-Path $bundle "Need-for-Speed-Underground-$($Scale)x.vlt"
$helper = Join-Path $bundle 'skin-support/SkinEffects.exe'
foreach ($required in @($skin,$helper)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Missing bundle file: $required" }
}
if (-not $VlcPath) {
    foreach ($candidate in @("$env:ProgramFiles\VideoLAN\VLC\vlc.exe", "${env:ProgramFiles(x86)}\VideoLAN\VLC\vlc.exe")) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { $VlcPath = $candidate; break }
    }
}
if (-not $VlcPath -or -not (Test-Path -LiteralPath $VlcPath -PathType Leaf)) { throw 'Installed VLC was not found.' }
$profileAppData = Join-Path $env:LOCALAPPDATA "NfsUnderground\profiles\$($Scale)x\AppData"
$profileVlc = Join-Path $profileAppData 'vlc'
New-Item -ItemType Directory -Path $profileVlc -Force | Out-Null
$runningFile = Join-Path $profileVlc 'running.json'
if (Test-Path -LiteralPath $runningFile) {
    $running = Get-Content -LiteralPath $runningFile -Raw | ConvertFrom-Json
    $existingPlayer = Get-Process -Id $running.pid -ErrorAction SilentlyContinue
    if ($existingPlayer -and $existingPlayer.StartTime.ToUniversalTime().Ticks -eq [long]$running.startedTicks) {
        throw 'This scale is already running from this launcher. Its profile was left untouched.'
    }
}
$config = Join-Path $profileVlc 'vlcrc'
$text = if (Test-Path -LiteralPath $config) { [IO.File]::ReadAllText($config) } else { '' }
$updated = Initialize-SupportState (Set-SkinPath $text $skin) $Scale
[IO.File]::WriteAllText($config, $updated, [Text.UTF8Encoding]::new($false))
$start = New-Object Diagnostics.ProcessStartInfo
$start.FileName = $VlcPath
$start.Arguments = '--no-one-instance --no-one-instance-when-started-from-file --no-media-library --no-metadata-network-access --no-qt-privacy-ask --embedded-video --skinned-video --intf=skins2 --config="' + $config + '"'
$start.UseShellExecute = $false
$start.EnvironmentVariables['APPDATA'] = $profileAppData
$player = [Diagnostics.Process]::Start($start)
@{pid=$player.Id;startedTicks=$player.StartTime.ToUniversalTime().Ticks} | ConvertTo-Json | Set-Content -LiteralPath $runningFile -Encoding UTF8
$helperArguments = @('--pid', $player.Id, '--skin', ('"' + $skin + '"'))
$savedVideo = [regex]::Match($updated, '\["video" "video_1" -?\d+ -?\d+ (\d+) (\d+) [01]\]')
if ($savedVideo.Success) { $helperArguments += @('--video-size', ($savedVideo.Groups[1].Value+'x'+$savedVideo.Groups[2].Value)) }
Start-Process -FilePath $helper -ArgumentList $helperArguments -WindowStyle Hidden | Out-Null
