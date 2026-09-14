$ErrorActionPreference = 'Stop'
$labRoot = Split-Path $PSScriptRoot -Parent
$labPython = Join-Path $env:USERPROFILE '.venvs\quantum-noise-detective\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $labPython)) { throw 'Install the project environment first.' }
$labIdentity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$labAction = New-ScheduledTaskAction -Execute $labPython -Argument ('"' + (Join-Path $labRoot 'launch.py') + '" --no-browser') -WorkingDirectory $labRoot
$labTriggers = @((New-ScheduledTaskTrigger -AtLogOn -User $labIdentity), (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)))
$labSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$labPrincipal = New-ScheduledTaskPrincipal -UserId $labIdentity -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'Quantum Noise Detective' -Action $labAction -Trigger $labTriggers -Settings $labSettings -Principal $labPrincipal -Description 'Keep the local Quantum Noise Detective lab running while signed in; recover stopped services.' -Force
Start-ScheduledTask -TaskName 'Quantum Noise Detective'
