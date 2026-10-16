param([string]$BundleDirectory = $PSScriptRoot, [Alias('SelfTest')][switch]$RunSelfTest, [switch]$FunctionsOnly)
$ErrorActionPreference = 'Stop'

function Get-PlaylistXml([byte[]]$Bytes) {
    $settings = [Xml.XmlReaderSettings]::new()
    $settings.DtdProcessing = [Xml.DtdProcessing]::Ignore
    $settings.XmlResolver = $null
    $stream = [IO.MemoryStream]::new($Bytes, $false)
    $reader = [Xml.XmlReader]::Create($stream, $settings)
    try {
        $document = [Xml.XmlDocument]::new()
        $document.XmlResolver = $null
        $document.Load($reader)
        $fonts = $document.SelectNodes('//Font[@id="playlist"]')
        $trees = $document.SelectNodes('//Playtree')
        if ($fonts.Count -ne 1 -or $trees.Count -ne 1 -or $trees[0].GetAttribute('font') -ne 'playlist' -or $document.SelectNodes('//*[@font="playlist" and not(self::Playtree)]').Count -ne 0) { throw 'This bundle needs one dedicated playlist font and one playlist control.' }
        return $document
    } finally { $reader.Dispose(); $stream.Dispose() }
}

function Set-PlaylistXmlSize([byte[]]$Bytes, [ValidateRange(8,48)][int]$Pixels) {
    $null = Get-PlaylistXml $Bytes
    $utf8 = [Text.UTF8Encoding]::new($false, $true)
    $text = $utf8.GetString($Bytes)
    $tags = @([regex]::Matches($text, '<Font\b[^>]*>') | Where-Object { $_.Value -match '\bid\s*=\s*(["''])playlist\1' })
    if ($tags.Count -ne 1) { throw 'Dedicated playlist font tag is ambiguous.' }
    $sizes = [regex]::Matches($tags[0].Value, '\bsize\s*=\s*(?<quote>["''])(?<value>\d+)\k<quote>')
    if ($sizes.Count -ne 1) { throw 'Dedicated playlist size is missing or ambiguous.' }
    $value = $sizes[0].Groups['value']
    $offset = $tags[0].Index + $value.Index
    $changed = $text.Substring(0,$offset) + $Pixels.ToString([Globalization.CultureInfo]::InvariantCulture) + $text.Substring($offset+$value.Length)
    return ,$utf8.GetBytes($changed)
}

function Get-PlaylistSkinBytes([string]$Path) {
    Add-Type -AssemblyName System.IO.Compression,System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($Path)
    try {
        $themes = @($archive.Entries | Where-Object { $_.FullName -eq 'theme.xml' })
        if ($themes.Count -ne 1 -or $themes[0].Length -gt 16777216) { throw 'Missing, duplicate or oversized theme.xml.' }
        $stream = $themes[0].Open(); $memory = [IO.MemoryStream]::new()
        try { $stream.CopyTo($memory); return ,$memory.ToArray() } finally { $stream.Dispose(); $memory.Dispose() }
    } finally { $archive.Dispose() }
}

function Resolve-PlaylistSkin([string]$Bundle, [ValidateSet(1,2)][int]$Scale) {
    $Bundle = [IO.Path]::GetFullPath($Bundle)
    $name = "Need-for-Speed-Underground-$($Scale)x.vlt"
    $canonical = Join-Path $Bundle $name
    $custom = Join-Path (Join-Path $Bundle 'custom') $name
    try {
        if (-not (Test-Path -LiteralPath $custom -PathType Leaf) -or -not (Test-Path -LiteralPath ($custom+'.json') -PathType Leaf)) { return $canonical }
        $metadata = [IO.File]::ReadAllText($custom+'.json') | ConvertFrom-Json
        if ($metadata.schemaVersion -ne 1 -or $metadata.scale -ne $Scale -or $metadata.pixels -lt 8 -or $metadata.pixels -gt 48 -or [double]$metadata.pixels -ne [int]$metadata.pixels) { return $canonical }
        if ($metadata.sourceBaseHash -notmatch '^[a-fA-F0-9]{64}$' -or $metadata.customHash -notmatch '^[a-fA-F0-9]{64}$') { return $canonical }
        if ((Get-FileHash -LiteralPath $canonical -Algorithm SHA256).Hash -ne $metadata.sourceBaseHash -or (Get-FileHash -LiteralPath $custom -Algorithm SHA256).Hash -ne $metadata.customHash) { return $canonical }
        $document = Get-PlaylistXml (Get-PlaylistSkinBytes $custom)
        if ([int]$document.SelectSingleNode('//Font[@id="playlist"]').GetAttribute('size') -ne $metadata.pixels) { return $canonical }
        return $custom
    } catch { return $canonical }
}

function Save-PlaylistTextSize([string]$Bundle, [ValidateSet(1,2)][int]$Scale, [ValidateRange(8,48)][int]$Pixels) {
    $Bundle = [IO.Path]::GetFullPath($Bundle)
    Add-Type -AssemblyName System.IO.Compression,System.IO.Compression.FileSystem
    $name = "Need-for-Speed-Underground-$($Scale)x.vlt"
    $canonical = Join-Path $Bundle $name
    $sourceHash = (Get-FileHash -LiteralPath $canonical -Algorithm SHA256).Hash
    $replacement = Set-PlaylistXmlSize (Get-PlaylistSkinBytes $canonical) $Pixels
    $directory = Join-Path $Bundle 'custom'
    $null = New-Item -ItemType Directory -Path $directory -Force
    $custom = Join-Path $directory $name
    $temporary = Join-Path $directory ([Guid]::NewGuid().ToString('N')+'.vlt.tmp')
    $metadataTemporary = $temporary+'.json'
    try {
        $inputZip = [IO.Compression.ZipFile]::OpenRead($canonical)
        try {
            $outputZip = [IO.Compression.ZipFile]::Open($temporary, [IO.Compression.ZipArchiveMode]::Create)
            try {
                $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
                foreach ($entry in $inputZip.Entries) {
                    if (-not $names.Add($entry.FullName) -or $entry.FullName -match '(^/|^[a-zA-Z]:|(^|/)\.\.(/|$)|\\)') { throw 'Unsafe or duplicate ZIP entry.' }
                    $copy = $outputZip.CreateEntry($entry.FullName, [IO.Compression.CompressionLevel]::Optimal)
                    $copy.LastWriteTime = $entry.LastWriteTime
                    $copy.ExternalAttributes = $entry.ExternalAttributes
                    $destination = $copy.Open()
                    try {
                        if ($entry.FullName -eq 'theme.xml') { $destination.Write($replacement,0,$replacement.Length) }
                        else { $original = $entry.Open(); try { $original.CopyTo($destination) } finally { $original.Dispose() } }
                    } finally { $destination.Dispose() }
                }
            } finally { $outputZip.Dispose() }
        } finally { $inputZip.Dispose() }
        if ((Get-FileHash -LiteralPath $canonical -Algorithm SHA256).Hash -ne $sourceHash) { throw 'Source bundle changed during customization; retry after its build completes.' }
        $metadata = @{schemaVersion=1;scale=$Scale;pixels=$Pixels;sourceBaseHash=$sourceHash;customHash=(Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash}
        [IO.File]::WriteAllText($metadataTemporary, ($metadata | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
        # Commit metadata last: an interrupted pair safely fails launcher hashes.
        if ([IO.File]::Exists($custom)) { [IO.File]::Replace($temporary,$custom,[NullString]::Value) } else { [IO.File]::Move($temporary,$custom) }
        if ([IO.File]::Exists($custom+'.json')) { [IO.File]::Replace($metadataTemporary,$custom+'.json',[NullString]::Value) } else { [IO.File]::Move($metadataTemporary,$custom+'.json') }
        return $custom
    } finally {
        foreach ($file in @($temporary,$metadataTemporary)) { if ([IO.File]::Exists($file)) { [IO.File]::Delete($file) } }
    }
}

function Test-PlaylistCustomization {
    $scratch = Join-Path ([IO.Path]::GetTempPath()) ('NfsPlaylistTextTest-'+[Guid]::NewGuid().ToString('N'))
    $null = New-Item -ItemType Directory -Path $scratch
    try {
        Add-Type -AssemblyName System.IO.Compression,System.IO.Compression.FileSystem
        $profileFixture = Join-Path $scratch 'vlcrc'
        [IO.File]::WriteAllText($profileFixture,'skins2-config=preserve all saved positions and preferences')
        $profileHash = (Get-FileHash -LiteralPath $profileFixture -Algorithm SHA256).Hash
        foreach ($scale in @(1,2)) {
            $base = Join-Path $scratch "Need-for-Speed-Underground-$($scale)x.vlt"
            $xml = '<Theme><Font id="ui" size="10"/><Font file="font.ttf" id="playlist" size="'+(12*$scale)+'"/><Window><Layout><Playtree font="playlist" action="keep"/></Layout></Window></Theme>'
            $zip = [IO.Compression.ZipFile]::Open($base,[IO.Compression.ZipArchiveMode]::Create)
            try {
                foreach ($item in @(@{Name='theme.xml';Bytes=[Text.Encoding]::UTF8.GetBytes($xml)},@{Name='assets/original.bin';Bytes=[byte[]]@(0,255,128,1,2,0,254)},@{Name='font.ttf';Bytes=[Text.Encoding]::UTF8.GetBytes('exact font bytes')})) {
                    $writer = $zip.CreateEntry($item.Name).Open()
                    try { $writer.Write($item.Bytes,0,$item.Bytes.Length) } finally { $writer.Dispose() }
                }
            } finally { $zip.Dispose() }
            $canonicalHash = (Get-FileHash -LiteralPath $base -Algorithm SHA256).Hash
            if ((Resolve-PlaylistSkin $scratch $scale) -ne $base) { throw 'Fresh scale must select canonical.' }
            $custom = Save-PlaylistTextSize $scratch $scale 19
            if ((Get-FileHash -LiteralPath $base -Algorithm SHA256).Hash -ne $canonicalHash -or (Resolve-PlaylistSkin $scratch $scale) -ne $custom) { throw 'Custom selection/source preservation failed.' }
            $changed = [Text.Encoding]::UTF8.GetString((Get-PlaylistSkinBytes $custom))
            if ($changed -ne $xml.Replace(('id="playlist" size="'+(12*$scale)+'"'), 'id="playlist" size="19"')) { throw 'Only dedicated font size may change.' }
            $a = [IO.Compression.ZipFile]::OpenRead($base); $b = [IO.Compression.ZipFile]::OpenRead($custom)
            try {
                if ($a.Entries.Count -ne $b.Entries.Count) { throw 'ZIP entries changed.' }
                foreach ($entry in $a.Entries) {
                    if ($entry.FullName -eq 'theme.xml') { continue }
                    $readerA = $entry.Open(); $readerB = $b.GetEntry($entry.FullName).Open()
                    $bytesA=[IO.MemoryStream]::new(); $bytesB=[IO.MemoryStream]::new()
                    try { $readerA.CopyTo($bytesA); $readerB.CopyTo($bytesB); if ([Convert]::ToBase64String($bytesA.ToArray()) -cne [Convert]::ToBase64String($bytesB.ToArray())) { throw 'Binary asset payload changed.' } } finally { $readerA.Dispose(); $readerB.Dispose(); $bytesA.Dispose(); $bytesB.Dispose() }
                }
            } finally { $a.Dispose(); $b.Dispose() }
            foreach ($bad in @(7,49)) { $rejected=$false; try { $null=Save-PlaylistTextSize $scratch $scale $bad } catch { $rejected=$true }; if (-not $rejected) { throw 'Out-of-range font size accepted.' } }
            foreach ($badXml in @($xml.Replace('font="playlist"','font="ui"'),$xml.Replace('<Playtree font="playlist" action="keep"/>','<Playtree font="playlist"/><Playtree font="playlist"/>'))) {
                $rejected=$false; try { $null=Set-PlaylistXmlSize ([Text.Encoding]::UTF8.GetBytes($badXml)) 19 } catch { $rejected=$true }; if (-not $rejected) { throw 'Invalid dedicated Playtree accepted.' }
            }
            $sidecar = [IO.File]::ReadAllText($custom+'.json')
            $metadata = $sidecar | ConvertFrom-Json; $metadata.scale=3-$scale
            [IO.File]::WriteAllText($custom+'.json',($metadata|ConvertTo-Json))
            if ((Resolve-PlaylistSkin $scratch $scale) -ne $base) { throw 'Cross-scale custom accepted.' }
            [IO.File]::WriteAllText($custom+'.json',$sidecar)
            [IO.File]::AppendAllText($custom,'changed')
            if ((Resolve-PlaylistSkin $scratch $scale) -ne $base) { throw 'Changed custom hash accepted.' }
            $null=Save-PlaylistTextSize $scratch $scale 48
            [IO.File]::AppendAllText($base,'new canonical build')
            if ((Resolve-PlaylistSkin $scratch $scale) -ne $base) { throw 'Stale canonical hash accepted.' }
            if ((Get-FileHash -LiteralPath $profileFixture -Algorithm SHA256).Hash -ne $profileHash) { throw 'Unrelated saved profile changed.' }
        }
        Write-Output 'PASS playlist ZIP/font/hash/scale fixtures; no GUI, VLC or user profile accessed.'
    } finally {
        # All contents were created by this test under one unique temp folder.
        $resolved = [IO.Path]::GetFullPath($scratch)
        if ((Split-Path $resolved -Leaf) -notlike 'NfsPlaylistTextTest-*' -or (Split-Path $resolved -Parent) -ne [IO.Path]::GetTempPath().TrimEnd('\')) { throw 'Refusing unexpected fixture cleanup path.' }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}

if ($FunctionsOnly) { return }
if ($RunSelfTest) { Test-PlaylistCustomization; exit 0 }

if (-not (Test-Path -LiteralPath (Join-Path $BundleDirectory 'Need-for-Speed-Underground-1x.vlt'))) { $BundleDirectory=Join-Path (Split-Path $PSScriptRoot -Parent) 'dist' }
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$form = [Windows.Forms.Form]::new()
$form.Text='Playlist text size'; $form.ClientSize=[Drawing.Size]::new(520,300); $form.StartPosition='CenterScreen'; $form.FormBorderStyle='FixedDialog'; $form.MaximizeBox=$false
$scaleChoice=[Windows.Forms.ComboBox]::new(); $scaleChoice.DropDownStyle='DropDownList'; $scaleChoice.Items.AddRange(@('1x skin','2x skin')); $scaleChoice.Location=[Drawing.Point]::new(18,18); $scaleChoice.Width=140
$sizeLabel=[Windows.Forms.Label]::new(); $sizeLabel.Text='Physical text size (pixels):'; $sizeLabel.Location=[Drawing.Point]::new(180,22); $sizeLabel.AutoSize=$true
$sizeChoice=[Windows.Forms.NumericUpDown]::new(); $sizeChoice.Minimum=8; $sizeChoice.Maximum=48; $sizeChoice.Location=[Drawing.Point]::new(370,18); $sizeChoice.Width=80
$preview=[Windows.Forms.ListBox]::new(); $preview.Location=[Drawing.Point]::new(18,60); $preview.Size=[Drawing.Size]::new(484,150); $preview.BackColor=[Drawing.Color]::Black; $preview.ForeColor=[Drawing.Color]::FromArgb(201,205,212); $preview.IntegralHeight=$true; $preview.HorizontalScrollbar=$true
$preview.Items.AddRange(@('01  Night Drive.mp4','02  Underground soundtrack.flac','03  A longer playlist filename for readability'))
$status=[Windows.Forms.Label]::new(); $status.Location=[Drawing.Point]::new(18,220); $status.Size=[Drawing.Size]::new(484,38); $status.Text='Preview only. Saved text size applies on the next Start-1x/2x launch.'
$save=[Windows.Forms.Button]::new(); $save.Text='Save'; $save.Location=[Drawing.Point]::new(330,265)
$close=[Windows.Forms.Button]::new(); $close.Text='Close'; $close.Location=[Drawing.Point]::new(420,265); $close.Add_Click({$form.Close()})
$sizeChoice.Add_ValueChanged({$old=$preview.Tag; $preview.Font=[Drawing.Font]::new('Arial',[single]$sizeChoice.Value,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel); $preview.Tag=$preview.Font; $preview.HorizontalExtent=([Windows.Forms.TextRenderer]::MeasureText('03  A longer playlist filename for readability',$preview.Font).Width+16); if ($old) {$old.Dispose()}})
$scaleChoice.Add_SelectedIndexChanged({
    $selected=$scaleChoice.SelectedIndex+1
    $sizeChoice.Value=12*$selected
    try { $selectedSkin=Resolve-PlaylistSkin $BundleDirectory $selected; $document=Get-PlaylistXml (Get-PlaylistSkinBytes $selectedSkin); $sizeChoice.Value=[Math]::Max(8,[Math]::Min(48,[int]$document.SelectSingleNode('//Font[@id="playlist"]').GetAttribute('size'))) } catch { $status.Text='Canonical bundle must include the dedicated playlist font before saving.' }
})
$save.Add_Click({try {$selected=$scaleChoice.SelectedIndex+1; $null=Save-PlaylistTextSize $BundleDirectory $selected ([int]$sizeChoice.Value); $status.Text="Saved for the next Start-$($selected)x launch. Current VLC is unchanged."} catch {$status.Text=$_.Exception.Message}})
$form.Controls.AddRange(@($scaleChoice,$sizeLabel,$sizeChoice,$preview,$status,$save,$close)); $scaleChoice.SelectedIndex=0
try { $null=$form.ShowDialog() } finally { if ($preview.Tag) {$preview.Tag.Dispose()}; $form.Dispose() }
