param(
    [string]$Helper = (Join-Path $PSScriptRoot '..\dist\skin-support\SkinEffects.exe'),
    [string]$InstalledVlc = (Join-Path $env:ProgramFiles 'VideoLAN\VLC\vlc.exe')
)
$ErrorActionPreference = 'Stop'
# Filesystem-only fixture test: never instantiate Target or call desktop/audio APIs.
$assembly = [Reflection.Assembly]::LoadFile((Resolve-Path -LiteralPath $Helper).Path)
$trust = $assembly.GetType('NfsSkinSupport.RuntimeTrust', $true)
$method = $trust.GetMethod('Validate', [Reflection.BindingFlags]'NonPublic,Static')
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('NfsRuntimeCheck-' + [Guid]::NewGuid().ToString('N'))
$hash = (Get-FileHash -LiteralPath $InstalledVlc -Algorithm SHA256).Hash.ToLowerInvariant()
$directory = Join-Path (Join-Path $fixture 'VlcRuntime') $hash
$runtime = Join-Path $directory 'vlc.exe'
$portable = Join-Path $directory 'portable'
$null = New-Item -ItemType Directory -Path $portable -Force
Copy-Item -LiteralPath $InstalledVlc -Destination $runtime
function Invoke-Validation([object[]]$Arguments) {
    $plain = [object[]]::new($Arguments.Length)
    for ($index = 0; $index -lt $Arguments.Length; $index++) { $plain[$index] = $Arguments[$index].PSObject.BaseObject }
    $null = $method.Invoke($null, $plain)
}
function Assert-Rejected([object[]]$Arguments) {
    try { Invoke-Validation $Arguments }
    catch {
        $failure = $_.Exception
        while ($failure.InnerException) { $failure = $failure.InnerException }
        if ($failure -is [IO.InvalidDataException]) { return }
        throw
    }
    throw 'Runtime trust accepted a negative fixture.'
}
try {
    $valid = [object[]]@($runtime, [long]123, $runtime, $InstalledVlc, [long]123)
    Invoke-Validation $valid
    Assert-Rejected @($runtime, [long]123, $runtime, $InstalledVlc, [long]124)
    Assert-Rejected @((Join-Path $fixture 'other.exe'), [long]123, $runtime, $InstalledVlc, [long]123)
    Assert-Rejected @($runtime, [long]123, $runtime, $runtime, [long]123)
    Assert-Rejected @($runtime, [long]123, 'relative/vlc.exe', $InstalledVlc, [long]123)
    [IO.Directory]::Delete($portable, $false)
    Assert-Rejected $valid
    $null = New-Item -ItemType Directory -Path $portable
    $stream = [IO.File]::Open($runtime, [IO.FileMode]::Open, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.WriteByte(0) } finally { $stream.Dispose() }
    Assert-Rejected $valid
    Write-Output 'PASS: copied runtime validation; rejects start-time/path/reference/relative-path/portable-dir/hash mismatches. No VLC, desktop or audio launched.'
}
finally {
    # Remove only the explicitly created fixture files/directories; no recursion.
    if ([IO.File]::Exists($runtime)) { [IO.File]::Delete($runtime) }
    if ([IO.Directory]::Exists($portable)) { [IO.Directory]::Delete($portable, $false) }
    [IO.Directory]::Delete($directory, $false)
    [IO.Directory]::Delete((Join-Path $fixture 'VlcRuntime'), $false)
    [IO.Directory]::Delete($fixture, $false)
}
