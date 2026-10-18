param(
    [Parameter(Mandatory=$true)][string]$Destination,
    [string]$SourceDirectory
)
$ErrorActionPreference = 'Stop'
if (-not $SourceDirectory) { $SourceDirectory = Join-Path $PSScriptRoot 'nfs-player' }
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
if (-not (Test-Path -LiteralPath $compiler -PathType Leaf)) { throw '.NET Framework 4 compiler was not found.' }
$sources = @('NfsPlayer.cs','NfsSkin.cs','SkinRuntime.cs','Native.cs','VlcIsolation.cs','NativeHttp.cs','HudCommands.cs') | ForEach-Object {
    (Resolve-Path -LiteralPath (Join-Path $SourceDirectory $_)).Path
}
$directory = [IO.Path]::GetFullPath($Destination)
$output = Join-Path $directory 'NfsPlayer.exe'
if (Test-Path -LiteralPath $output) { throw 'Choose a fresh build directory; existing controller builds are never overwritten.' }
$null = New-Item -ItemType Directory -Path $directory -Force
& $compiler /nologo /target:winexe /main:NfsPlayer /platform:x64 /optimize+ /warnaserror+ "/out:$output" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll /reference:System.Xml.Linq.dll /reference:System.IO.Compression.dll /reference:System.IO.Compression.FileSystem.dll $sources
if ($LASTEXITCODE -ne 0) { throw 'Standalone skin controller compilation failed.' }
$check = Start-Process -FilePath $output -ArgumentList '--self-test' -WindowStyle Hidden -Wait -PassThru
if ($check.ExitCode -ne 0) { throw 'Standalone skin controller pure self-test failed.' }
Get-FileHash -LiteralPath $output -Algorithm SHA256
Write-Output 'Built the standalone controller. Pure self-test only; VLC and browsers were not launched.'
