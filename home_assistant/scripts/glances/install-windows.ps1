<#
Set up Glances on a Windows PC so Home Assistant can monitor it.

    .\install-windows.ps1 -HomeAssistantIp <address>

Run it in an ADMINISTRATOR PowerShell window: the firewall rule needs it.

What it does, and why each part is the way it is:
  - Installs Glances into %USERPROFILE%\glances-packages with `pip --target`. A plain
    `pip install --user` can land in an app-private AppData folder (it did when run
    from a Store-packaged app) where Task Scheduler cannot see it.
  - Writes %USERPROFILE%\glances_server.pyw, a launcher that sends output to nul.
    pythonw.exe has no console, and Glances' web server crashes configuring its
    logging without one.
  - Registers the Scheduled Task "Glances web server" to run it at logon.
  - Opens TCP 61208 to the Home Assistant address only, on every network profile.
#>
param(
    [Parameter(Mandatory = $true)][string]$HomeAssistantIp,
    [int]$Port = 61208
)
$ErrorActionPreference = 'Stop'

$python = (Get-Command python).Source
$pythonw = Join-Path (Split-Path $python) 'pythonw.exe'
$packages = Join-Path $env:USERPROFILE 'glances-packages'
$launcher = Join-Path $env:USERPROFILE 'glances_server.pyw'
$errorLog = Join-Path $env:USERPROFILE 'glances_server_error.log'

& $python -m pip install --quiet --upgrade --target $packages 'glances[web]'
if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }

@"
import os, sys, runpy, traceback
sys.path.insert(0, r'$packages')
sys.stdout = sys.stderr = open(os.devnull, 'w')
sys.argv = ['glances', '-w', '--disable-webui', '-B', '0.0.0.0', '-p', '$Port']
try:
    runpy.run_module('glances', run_name='__main__')
except Exception:
    with open(r'$errorLog', 'w') as f:
        traceback.print_exc(file=f)
    raise
"@ | Set-Content -Path $launcher -Encoding utf8

$user = "$env:USERDOMAIN\$env:USERNAME"
$task = 'Glances web server'
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

$rule = 'Glances (Home Assistant only)'
Get-NetFirewallRule -DisplayName $rule -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName $rule -Direction Inbound -Action Allow -Protocol TCP `
    -LocalPort $Port -RemoteAddress $HomeAssistantIp -Profile Any | Out-Null

Start-Sleep -Seconds 8
try {
    Invoke-RestMethod "http://localhost:$Port/api/4/status" | Out-Null
    Write-Host "Glances is answering on port $Port. Add it in Home Assistant with this PC's address."
} catch {
    Write-Error "Glances is not answering yet; see $errorLog"
}
