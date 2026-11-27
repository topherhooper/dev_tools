<#
Set up the network watcher on a Windows PC so it reports to Home Assistant.

    .\install-windows.ps1 -WebhookUrl http://<home-assistant>:8123/api/webhook/<id> [-Name "Office PC"]

No administrator rights needed: it runs as you, opens no port and adds no firewall rule.

What it does:
  - Copies netwatch.py to %LOCALAPPDATA%\netwatch and writes config.json beside it.
  - Installs psutil into %LOCALAPPDATA%\netwatch\packages with `pip --target`, because a
    plain `pip install --user` can land where Task Scheduler cannot see it.
  - Registers the Scheduled Task "Network watch" to run it at logon, with pythonw.exe
    so no window appears.

To remove it: Unregister-ScheduledTask "Network watch"; delete %LOCALAPPDATA%\netwatch.
#>
param(
    [Parameter(Mandatory = $true)][string]$WebhookUrl,
    [string]$Name = $env:COMPUTERNAME
)
$ErrorActionPreference = 'Stop'

$python = (Get-Command python).Source
$pythonw = Join-Path (Split-Path $python) 'pythonw.exe'
$dir = Join-Path $env:LOCALAPPDATA 'netwatch'
$packages = Join-Path $dir 'packages'
$launcher = Join-Path $dir 'netwatch_launcher.pyw'
New-Item -ItemType Directory -Force -Path $dir | Out-Null

Copy-Item (Join-Path $PSScriptRoot 'netwatch.py') (Join-Path $dir 'netwatch.py') -Force
@{ url = $WebhookUrl; name = $Name } | ConvertTo-Json |
    Set-Content -Path (Join-Path $dir 'config.json') -Encoding ascii

& $python -m pip install --quiet --upgrade --target $packages psutil
if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }

# pythonw.exe has no console, so anything printed must go somewhere harmless.
@"
import os, sys, runpy, traceback
sys.path.insert(0, r'$packages')
sys.stdout = sys.stderr = open(os.devnull, 'w')
sys.argv = ['netwatch']
try:
    runpy.run_path(r'$dir\netwatch.py', run_name='__main__')
except Exception:
    with open(r'$dir\error.log', 'w') as f:
        traceback.print_exc(file=f)
    raise
"@ | Set-Content -Path $launcher -Encoding utf8

$user = "$env:USERDOMAIN\$env:USERNAME"
$task = 'Network watch'
$action = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$launcher`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName $task -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null
Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
Start-ScheduledTask -TaskName $task

Write-Host "Network watch is installed and running. It learns quietly for 3 days, then reports new programs."
