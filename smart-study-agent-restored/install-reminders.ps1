$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\pythonw.exe'
if (!(Test-Path $python)) { throw 'Create .venv first' }
$action = New-ScheduledTaskAction -Execute $python -Argument '-m infrastructure.notification_runner' -WorkingDirectory $root
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$login = New-ScheduledTaskTrigger -AtLogOn -User $user
$repeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
if (Get-ScheduledTask -TaskName 'SmartStudyAgentReminders' -ErrorAction SilentlyContinue) { throw 'Task already exists; review it first' }
Register-ScheduledTask -TaskName 'SmartStudyAgentReminders' -Action $action -Trigger @($login,$repeat) -Settings $settings -User $user -RunLevel Limited
