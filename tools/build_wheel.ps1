param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$destination = [IO.Path]::GetFullPath($OutputDirectory)
[IO.Directory]::CreateDirectory($destination) | Out-Null
$vswhere = "${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe"
$visualStudio = & $vswhere -products '*' -latest -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $visualStudio) { throw 'MSVC x64 build tools are required.' }
$source = Join-Path $PSScriptRoot 'OcclusionBridge.c'
$sourceCopy = Join-Path $destination 'OcclusionBridge.c'
if ([IO.Path]::GetFullPath($source) -eq $sourceCopy) { throw 'Build output must not overwrite source.' }
Copy-Item -LiteralPath $source -Destination $sourceCopy
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'WheelBridge.c') -Destination (Join-Path $destination 'WheelBridge.c')
$batch = Join-Path $destination 'compile-wheel.cmd'
$lines = @('@echo off', ('call "{0}\VC\Auxiliary\Build\vcvars64.bat" >nul' -f $visualStudio),
    'if errorlevel 1 exit /b %errorlevel%', ('cd /d "{0}"' -f $destination),
    'cl.exe /nologo /LD /MT /O2 /W4 /WX /guard:cf OcclusionBridge.c user32.lib gdi32.lib advapi32.lib shell32.lib /link /DYNAMICBASE /NXCOMPAT /OUT:NfsWheelBridge64.dll',
    'exit /b %errorlevel%')
[IO.File]::WriteAllLines($batch, $lines, [Text.Encoding]::ASCII)
& $env:ComSpec /d /c "`"$batch`""
if ($LASTEXITCODE -ne 0) { throw "Wheel DLL compilation failed ($LASTEXITCODE)." }
$output = Join-Path $destination 'NfsWheelBridge64.dll'
Get-FileHash -LiteralPath $output -Algorithm SHA256
