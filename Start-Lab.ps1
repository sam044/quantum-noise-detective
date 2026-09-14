$ErrorActionPreference = 'Stop'
$projectPython = Join-Path $env:USERPROFILE '.venvs\quantum-noise-detective\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'The project Python environment is missing. Follow docs/SETUP.md first.'
}
& $projectPython (Join-Path $PSScriptRoot 'launch.py') --background
