param(
    [ValidateSet(1,2)][int]$Scale = 1,
    [string]$VlcPath,
    [switch]$SelfTest
)
$ErrorActionPreference = 'Stop'

function Set-OsdSupport($StartInfo, [string]$DataRoot) {
    $StartInfo.Arguments += ' --osd --extraintf=luaintf --lua-intf=nfs_volume_osd_v1'
    # Child-process-only data lookup. Installed library/plugin lookup is left
    # intact; this bundle has no HTTP interface or altered recent-item policy.
    $StartInfo.EnvironmentVariables['VLC_DATA_PATH'] = [IO.Path]::GetFullPath($DataRoot)
}

function Set-SkinPath([string]$Text, [string]$SkinPath) {
    $line = 'skins2-last=' + $SkinPath
    if ($Text -match '(?m)^skins2-last=[^\r\n]*') {
        return [regex]::Replace($Text, '(?m)^skins2-last=[^\r\n]*', [System.Text.RegularExpressions.MatchEvaluator]{param($m) $line})
    }
    return $Text + "`r`n[skins2]`r`n" + $line + "`r`nskins2-config=`r`n"
}

function Get-EffectsGeometry([int]$AssetScale, $EffectsManifest) {
    if ($AssetScale -notin @(1,2)) { throw 'Unsupported asset scale.' }
    $schema = if ($null -eq $EffectsManifest) { 1 } else { [int]$EffectsManifest.schemaVersion }
    if ($schema -notin @(1,2)) { throw 'Unsupported effects schema.' }
    $closedWidth = if ($schema -eq 2) { 362 } else { 427*$AssetScale }
    $closedHeight = if ($schema -eq 2) { 1 } else { $AssetScale }
    if ($null -ne $EffectsManifest) {
        $openWidth = if ($schema -eq 2) { 361 } else { 426*$AssetScale }
        $openHeight = if ($schema -eq 2) { 64 } else { 146*$AssetScale }
        if ($EffectsManifest.scale -ne $AssetScale -or $EffectsManifest.hover.width -ne $openWidth -or $EffectsManifest.hover.height -ne $openHeight -or $EffectsManifest.hover.closedWidth -ne $closedWidth -or $EffectsManifest.hover.closedHeight -ne $closedHeight) { throw 'Invalid effects geometry for selected scale.' }
        $closedWidth = [int]$EffectsManifest.hover.closedWidth
        $closedHeight = [int]$EffectsManifest.hover.closedHeight
    }
    return @{Schema=$schema;ClosedWidth=$closedWidth;ClosedHeight=$closedHeight;NativeWidth=$(if ($schema -eq 2) {360} else {425*$AssetScale});NativeHeight=$(if ($schema -eq 2) {64} else {146*$AssetScale})}
}

function Read-EffectsManifest([string]$SkinPath) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($SkinPath)
    try {
        $entries = @($archive.Entries | Where-Object { $_.FullName -eq 'nfs-effects.json' })
        if ($entries.Count -ne 1 -or $entries[0].Length -gt 65536) { throw 'Missing, duplicate or oversized effects manifest.' }
        $reader = [IO.StreamReader]::new($entries[0].Open())
        try { $manifest = ($reader.ReadToEnd() | ConvertFrom-Json) } finally { $reader.Dispose() }
        $themes = @($archive.Entries | Where-Object { $_.FullName -eq 'theme.xml' })
        if ($themes.Count -ne 1 -or $themes[0].Length -gt 16777216) { throw 'Missing, duplicate or oversized skin XML.' }
        $settings = [Xml.XmlReaderSettings]::new()
        $settings.DtdProcessing = [Xml.DtdProcessing]::Ignore
        $settings.XmlResolver = $null
        $stream = $themes[0].Open()
        $xmlReader = [Xml.XmlReader]::Create($stream, $settings)
        try { $theme = [Xml.XmlDocument]::new(); $theme.XmlResolver = $null; $theme.Load($xmlReader) } finally { $xmlReader.Dispose(); $stream.Dispose() }
        $clock = $theme.SelectSingleNode('/Theme/Window[@id="clock_state"]')
        $hasClock = $null -ne $clock
        if ($hasClock) {
            $sizes = @{clock_elapsed_a=151;clock_elapsed_b=152;clock_remaining_a=153;clock_remaining_b=154}
            if ($clock.SelectNodes('Layout').Count -ne 4) { throw 'Invalid packaged clock state.' }
            foreach ($name in $sizes.Keys) {
                $layout = $clock.SelectSingleNode('Layout[@id="'+$name+'"]')
                if ($null -eq $layout -or $layout.GetAttribute('width') -ne [string]$sizes[$name] -or $layout.GetAttribute('height') -ne '17') { throw 'Invalid packaged clock geometry.' }
            }
        }
        $manifest | Add-Member -NotePropertyName clockRefresh -NotePropertyValue $hasClock -Force
        $snap = $theme.SelectSingleNode('/Theme/Window[@id="snapping_command"]')
        if ($null -ne $snap) {
            $snapState = $theme.SelectSingleNode('/Theme/Window[@id="snapping_state"]')
            if ($null -eq $snapState -or $snap.GetAttribute('x') -ne '-31000' -or $snap.GetAttribute('y') -ne '-29800' -or $snap.SelectNodes('Layout').Count -ne 2 -or $snapState.SelectNodes('Layout').Count -ne 3) { throw 'Invalid packaged snapping protocol.' }
            foreach ($pair in @(@('snapping_requested',192),@('snapping_ready',191))) {
                $layout = $snap.SelectSingleNode('Layout[@id="'+$pair[0]+'"]')
                if ($null -eq $layout -or $layout.GetAttribute('width') -ne [string]$pair[1] -or $layout.GetAttribute('height') -ne '17') { throw 'Invalid packaged snapping command.' }
            }
        }
        $manifest | Add-Member -NotePropertyName snappingToggle -NotePropertyValue ($null -ne $snap) -Force
        return $manifest
    } finally { $archive.Dispose() }
}

function Initialize-SupportState([string]$Text, [int]$AssetScale, $EffectsManifest = $null) {
    $geometry = Get-EffectsGeometry $AssetScale $EffectsManifest
    $saved = [regex]::Match($Text, '(?m)^skins2-config=([^\r\n]+)')
    if (-not $saved.Success) { return $Text }
    $pattern = '\["([^"\r\n]+)"\s+"([^"\r\n]+)"\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+([01])\]'
    $entries = [regex]::Matches($saved.Groups[1].Value, $pattern)
    $main = @($entries | Where-Object { $_.Groups[1].Value -eq 'main' })
    if ($main.Count -ne 1 -or ([regex]::Replace($saved.Groups[1].Value, $pattern, '')).Trim()) { return $Text }
    $clockRefresh = $null -ne $EffectsManifest -and $EffectsManifest.clockRefresh -eq $true
    $clockEntries = @($entries | Where-Object { $_.Groups[1].Value -eq 'clock_state' })
    $clockMode = if ($main[0].Groups[2].Value -match '_remaining$') { 'remaining' } else { 'elapsed' }
    if ($clockEntries.Count -eq 1 -and $clockEntries[0].Groups[2].Value -match '^clock_(elapsed|remaining)(_[ab])?$') {
        $clockMode = $Matches[1]
    }
    $resetInfoFrame = @($entries | Where-Object { $_.Groups[1].Value -eq 'info_frame_state' }).Count -gt 0
    $snappingToggle = $null -ne $EffectsManifest -and $EffectsManifest.snappingToggle -eq $true
    $owned = @('nfs_fx_button','nfs_fx_shutter','nfs_fx_intro','nfs_fx_info','nfs_fx_logo','nfs_hover_command','videoHoverController','fullscreenController','hover_volume_state','info_frame_state','clock_state')
    if ($snappingToggle) { $owned += @('snapping_command','snapping_state') }
    $parts = @($entries | Where-Object { $_.Groups[1].Value -notin $owned } | ForEach-Object { $_.Value })
    $keys = @('button','shutter','intro','info','logo')
    for ($index=0; $index -lt $keys.Count; $index++) {
        $key = $keys[$index]
        $state = if ($key -eq 'intro' -and $main[0].Groups[2].Value -eq 'main_start') { 'trigger' } else { 'ready' }
        $width = if ($state -eq 'trigger') { 51+$index } else { 41+$index }
        $parts += '["nfs_fx_' + $key + '" "nfs_fx_' + $key + '_' + $state + '" -31000 -31000 ' + $width + ' 17 1]'
    }
    $commandWidth = if ($geometry.Schema -eq 2) { 133 } else { 67 }
    $parts += '["nfs_hover_command" "nfs_hover_command_layout" -31000 -30900 ' + $commandWidth + ' 17 1]'
    $parts += '["videoHoverController" "video_hover_closed" -31000 -30800 ' + $geometry.ClosedWidth + ' ' + $geometry.ClosedHeight + ' 1]'
    $parts += '["fullscreenController" "fullscreen_controls" 0 0 ' + $geometry.NativeWidth + ' ' + $geometry.NativeHeight + ' 0]'
    if ($geometry.Schema -eq 2) { $parts += '["hover_volume_state" "hover_volume_collapsed" -31000 -30700 71 19 1]' }
    if ($resetInfoFrame) { $parts += '["info_frame_state" "info_frame_idle" 0 0 1 1 0]' }
    if ($clockRefresh) {
        $clockWidth = if ($clockMode -eq 'remaining') {153} else {151}
        $parts += '["clock_state" "clock_'+$clockMode+'_a" -31000 -30200 '+$clockWidth+' 17 1]'
    }
    if ($snappingToggle) {
        $parts += '["snapping_command" "snapping_ready" -31000 -29800 191 17 1]'
        $parts += '["snapping_state" "snapping_unavailable" -31000 -29700 201 1 1]'
    }
    return $Text.Substring(0,$saved.Groups[1].Index) + ($parts -join '') + $Text.Substring($saved.Groups[1].Index+$saved.Groups[1].Length)
}

if ($SelfTest) {
    $startFixture = [Diagnostics.ProcessStartInfo]::new()
    $startFixture.Arguments = '--intf=skins2'
    $originalDataPath = $env:VLC_DATA_PATH
    $originalPluginPath = $startFixture.EnvironmentVariables['VLC_PLUGIN_PATH']
    Set-OsdSupport $startFixture "C:\Unicode-é & O'Brien\skin-support\data"
    if ($startFixture.Arguments -ne '--intf=skins2 --osd --extraintf=luaintf --lua-intf=nfs_volume_osd_v1' -or $startFixture.EnvironmentVariables['VLC_DATA_PATH'] -ne "C:\Unicode-é & O'Brien\skin-support\data" -or $env:VLC_DATA_PATH -ne $originalDataPath -or $startFixture.EnvironmentVariables['VLC_PLUGIN_PATH'] -ne $originalPluginPath) { throw 'Private OSD launch scope failed.' }
    $fixture = "[core]`r`nvolume=123`r`n[skins2]`r`nskins2-last=old`r`nskins2-config=saved`r`n"
    $result = Set-SkinPath $fixture "C:\Unicode-é & O'Brien\skin.vlt"
    if (-not $result.Contains('volume=123') -or -not $result.Contains('skins2-config=saved') -or $result.Contains('skins2-last=old')) { throw 'Private config preservation failed.' }
    if ((Set-SkinPath '' 'C:\skin.vlt') -notmatch 'skins2-last=C:\\skin.vlt') { throw 'Fresh profile failed.' }
    foreach ($assetScale in @(1,2)) {
        $geometry = '["main" "main_3" -5 20 300 298 1]["video" "video_1" 8 9 1234 987 1]'
        $migrated = Initialize-SupportState ("skins2-config="+$geometry) $assetScale
        if (-not $migrated.Contains($geometry) -or -not $migrated.Contains('"nfs_fx_button" "nfs_fx_button_ready"') -or -not $migrated.Contains('"video_hover_closed"')) { throw 'Support state migration failed.' }
        if ((Initialize-SupportState $migrated $assetScale) -ne $migrated) { throw 'Support state migration must be idempotent.' }
        if (-not $migrated.Contains(('"video_hover_closed" -31000 -30800 '+(427*$assetScale)+' '+$assetScale+' 1]')) -or $migrated.Contains('hover_volume_state')) { throw 'Legacy geometry changed.' }
        $legacy = [pscustomobject]@{schemaVersion=1;scale=$assetScale;hover=[pscustomobject]@{width=(426*$assetScale);height=(146*$assetScale);closedWidth=(427*$assetScale);closedHeight=$assetScale}}
        if ((Initialize-SupportState ("skins2-config="+$geometry) $assetScale $legacy) -ne $migrated) { throw 'Packaged legacy manifest migration changed.' }
        $manifest = [pscustomobject]@{schemaVersion=2;scale=$assetScale;hover=[pscustomobject]@{width=361;height=64;closedWidth=362;closedHeight=1}}
        $compact = Initialize-SupportState ("skins2-config="+$geometry+'["hover_volume_state" "hover_volume_expanded" 2 3 72 19 1]') $assetScale $manifest
        foreach ($expected in @($geometry,'"video_hover_closed" -31000 -30800 362 1 1]','"fullscreen_controls" 0 0 360 64 0]','"nfs_hover_command_layout" -31000 -30900 133 17 1]','"hover_volume_collapsed" -31000 -30700 71 19 1]')) {
            if (-not $compact.Contains($expected)) { throw 'Compact support state migration failed.' }
        }
        if ($compact.Contains('"hover_volume_expanded"') -or (Initialize-SupportState $compact $assetScale $manifest) -ne $compact) { throw 'Compact support reset/idempotence failed.' }
        $infoSaved = '["info" "info_menu" -2 13 826 564 1]["info_page_state" "info_state_c_sub_2_3" 0 0 1 1 0]'
        $infoFixture = $compact + $infoSaved + '["info_frame_state" "info_frame_7" 0 0 1 1 0]'
        $infoResult = Initialize-SupportState $infoFixture $assetScale $manifest
        if (-not $infoResult.Contains($infoSaved) -or $infoResult.Contains('"info_frame_7"') -or -not $infoResult.Contains('["info_frame_state" "info_frame_idle" 0 0 1 1 0]') -or (Initialize-SupportState $infoResult $assetScale $manifest) -ne $infoResult) { throw 'Info frame reset must preserve saved content/geometry and be idempotent.' }
        $manifest | Add-Member -NotePropertyName clockRefresh -NotePropertyValue $true -Force
        $manifest | Add-Member -NotePropertyName snappingToggle -NotePropertyValue $true -Force
        $snapFixture = 'skins2-config='+$geometry+'["snapping_command" "snapping_requested" 1 2 192 17 1]["snapping_state" "snapping_disabled" 3 4 203 1 1]'
        $snapReset = Initialize-SupportState $snapFixture $assetScale $manifest
        if (-not $snapReset.Contains($geometry) -or $snapReset.Contains('"snapping_requested"') -or $snapReset.Contains('"snapping_disabled"') -or -not $snapReset.Contains('["snapping_command" "snapping_ready" -31000 -29800 191 17 1]') -or -not $snapReset.Contains('["snapping_state" "snapping_unavailable" -31000 -29700 201 1 1]') -or (Initialize-SupportState $snapReset $assetScale $manifest) -ne $snapReset) { throw 'Snapping transient reset must preserve panes, reset stale requests and be idempotent.' }
        foreach ($legacyMode in @('elapsed','remaining')) {
            $suffix = if ($legacyMode -eq 'remaining') {'_remaining'} else {''}
            $mainSaved = '["main" "main_7_closing'+$suffix+'" -5 20 300 298 1]'
            $videoSaved = '["video" "video_1" 8 9 1234 987 1]'
            $clockResult = Initialize-SupportState ('skins2-config='+$mainSaved+$videoSaved) $assetScale $manifest
            $width = if ($legacyMode -eq 'remaining') {153} else {151}
            $expectedClock = '["clock_state" "clock_'+$legacyMode+'_a" -31000 -30200 '+$width+' 17 1]'
            if (-not $clockResult.Contains($mainSaved+$videoSaved) -or -not $clockResult.Contains($expectedClock) -or (Initialize-SupportState $clockResult $assetScale $manifest) -ne $clockResult) { throw 'Legacy clock mode/geometry migration failed.' }
            $opposite = if ($legacyMode -eq 'remaining') {'elapsed'} else {'remaining'}
            $savedClock = '["clock_state" "clock_'+$opposite+'_b" 1 2 1 1 0]'
            $preserved = Initialize-SupportState ('skins2-config='+$mainSaved+$videoSaved+$savedClock) $assetScale $manifest
            $oppositeWidth = if ($opposite -eq 'remaining') {153} else {151}
            if (-not $preserved.Contains('["clock_state" "clock_'+$opposite+'_a" -31000 -30200 '+$oppositeWidth+' 17 1]') -or -not $preserved.Contains($mainSaved+$videoSaved)) { throw 'Existing independent clock mode was lost.' }
        }
        $manifest.hover.width = 722
        $rejected = $false
        try { $null = Get-EffectsGeometry $assetScale $manifest } catch { $rejected = $true }
        if (-not $rejected) { throw 'Invalid compact geometry accepted.' }
    }
    Write-Output 'PASS private launcher configuration; no process or user profile accessed.'
    exit 0
}

# This file ships beside the VLTs. Source-tree invocation uses dist/ instead.
. (Join-Path $PSScriptRoot 'Playlist-Text-Size.ps1') -FunctionsOnly
$bundle = $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $bundle "Need-for-Speed-Underground-$($Scale)x.vlt"))) {
    $bundle = Join-Path (Split-Path $PSScriptRoot -Parent) 'dist'
}
$skin = Resolve-PlaylistSkin $bundle $Scale
$helper = Join-Path $bundle 'skin-support/SkinEffects.exe'
$osdData = Join-Path $bundle 'skin-support/data'
$osdScript = Join-Path $osdData 'lua/intf/nfs_volume_osd_v1.lua'
foreach ($required in @($skin,$helper,$osdScript)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Missing bundle file: $required" }
}
$effectsManifest = Read-EffectsManifest $skin
$effectsGeometry = Get-EffectsGeometry $Scale $effectsManifest
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
$updated = Initialize-SupportState (Set-SkinPath $text $skin) $Scale $effectsManifest
[IO.File]::WriteAllText($config, $updated, [Text.UTF8Encoding]::new($false))
$start = New-Object Diagnostics.ProcessStartInfo
$start.FileName = $VlcPath
$start.Arguments = '--no-one-instance --no-one-instance-when-started-from-file --no-media-library --no-metadata-network-access --no-qt-privacy-ask --embedded-video --skinned-video --intf=skins2 --config="' + $config + '"'
if ($effectsGeometry.Schema -eq 2) { $start.Arguments += ' --qt-fs-opacity=0.85' }
$start.UseShellExecute = $false
$start.EnvironmentVariables['APPDATA'] = $profileAppData
Set-OsdSupport $start $osdData
$player = [Diagnostics.Process]::Start($start)
@{pid=$player.Id;startedTicks=$player.StartTime.ToUniversalTime().Ticks} | ConvertTo-Json | Set-Content -LiteralPath $runningFile -Encoding UTF8
$helperArguments = @('--pid', $player.Id, '--skin', ('"' + $skin + '"'))
$savedVideo = [regex]::Match($updated, '\["video" "video_1" -?\d+ -?\d+ (\d+) (\d+) [01]\]')
if ($savedVideo.Success) { $helperArguments += @('--video-size', ($savedVideo.Groups[1].Value+'x'+$savedVideo.Groups[2].Value)) }
Start-Process -FilePath $helper -ArgumentList $helperArguments -WindowStyle Hidden | Out-Null
