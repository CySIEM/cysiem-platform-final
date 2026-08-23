# CySIEM Agent Installation Script (Windows)
# This is dot-sourced by the enrollment command, which then calls
# Install-CySiemAgent with the real parameters. It downloads the actual
# agent source from the server and runs it via a Scheduled Task - this
# replaces a previous version of this script that only printed messages
# and never installed anything real.

function Install-CySiemAgent {
    param (
        [Parameter(Mandatory=$true)][string]$Token,
        [Parameter(Mandatory=$true)][string]$Server,
        [Parameter(Mandatory=$true)][string]$AgentId
    )

    $ErrorActionPreference = "Stop"
    Write-Host "--- CySIEM Agent Installation ---" -ForegroundColor Cyan

    # Defensive cleanup: if these values got mangled by whatever the
    # command was copied through (e.g. an editor/chat client that
    # auto-linkifies URLs into "[url](url)" Markdown), strip that back to
    # a plain value instead of failing on it. This backend and frontend do
    # not generate Markdown anywhere - this is a safety net for whatever
    # happened between generation and paste, not a fix to this code.
    $Token = $Token.Trim().Trim('[',']')
    $Server = $Server.Trim().Trim('[',']')
    if ($Server -match '^\[?(https?://[^\]\s]+)\]?\(https?://[^\)]+\)$') { $Server = $Matches[1] }
    $Server = $Server.TrimEnd('/')

    # 1. Check Python is available - this installer does not bundle a
    #    Python runtime, and pretending it does would just fail later.
    #    Fresh Windows installs (and the Microsoft Store Python stub) often
    #    have `py` on PATH but not `python` - check both before giving up.
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
    if (-not $python) {
        Write-Error "Python 3 was not found on PATH (checked 'python' and 'py'). Install Python 3 from https://python.org (check 'Add python.exe to PATH' during install) and re-run this command."
        return
    }

    # 2. Reachability check up front.
    try {
        Invoke-WebRequest -Uri "$Server/" -UseBasicParsing -TimeoutSec 5 | Out-Null
    } catch {
        Write-Error "Cannot reach $Server from this machine. Check the backend is running, SERVER_URL is a reachable address (not 127.0.0.1 if this is a different machine), and no firewall is blocking port 8000."
        return
    }

    $InstallDir = "C:\Program Files\CySIEM\Agent"
    New-Item -Path $InstallDir -ItemType Directory -Force | Out-Null

    # Best-effort: enable Security-log auditing for process creation.
    # Without this, Windows never logs Event ID 4688 at all (not a bug in
    # this agent - it's off by default on most Windows installs), so the
    # collector would have no real process-creation telemetry to report,
    # the same way the Linux collector needs a readable auth.log to work.
    # Non-fatal if it fails (e.g. restricted by Group Policy) - logon
    # events (4624/4625) still work either way.
    try {
        & auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable | Out-Null
        # Also enable command-line logging on process-creation events - this
        # is a SEPARATE setting from the audit subcategory above. Without
        # it, Event 4688 fires but its CommandLine field is empty, which
        # would show as "-" in the dashboard rather than fabricated data -
        # correct behavior, but enabling this gives genuinely richer telemetry.
        New-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit" -Force -ErrorAction SilentlyContinue | Out-Null
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit" -Name "ProcessCreationIncludeCmdLine_Enabled" -Value 1 -Type DWord -ErrorAction SilentlyContinue
        Write-Host "Enabled Security-log auditing for process creation." -ForegroundColor DarkGray
    } catch {
        Write-Host "Could not enable process-creation auditing (may be managed by Group Policy) - process events may be limited." -ForegroundColor DarkYellow
    }

    # 3. Download the real agent source from the server.
    Write-Host "Downloading agent components from $Server..." -ForegroundColor Yellow
    $files = @("main.py", "registration.py", "heartbeat.py", "collector.py", "receiver.py", "sysinfo.py", "config_loader.py")
    foreach ($f in $files) {
        Invoke-WebRequest -Uri "$Server/agent-files/$f" -OutFile (Join-Path $InstallDir $f) -UseBasicParsing
    }

    # 4. Config file.
    # IMPORTANT: Out-File -Encoding utf8 in Windows PowerShell 5.1 (the
    # default powershell.exe, which is exactly what the enrollment command
    # runs) ALWAYS writes a UTF-8 byte-order-mark at the start of the file.
    # Python's json.load() does not skip that BOM, so it saw three
    # invisible bytes before "{" and failed with exactly:
    #   JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    # [System.IO.File]::WriteAllText with an explicit no-BOM UTF8Encoding
    # avoids this entirely, and works the same on both Windows PowerShell
    # 5.1 and PowerShell 7+.
    $Config = @{
        server_url = $Server
        token = $Token
        agent_id = [int]$AgentId
        heartbeat_interval = 5
        log_interval = 10
        version = "1.0.0"
    }
    $jsonText = $Config | ConvertTo-Json
    $configPath = Join-Path $InstallDir "config.json"
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($configPath, $jsonText, $utf8NoBom)

    # Verify what was actually written is valid, non-empty JSON before
    # going any further - fail here with a clear reason rather than
    # discovering it as a cryptic crash inside registration.py.
    $writtenBytes = [System.IO.File]::ReadAllBytes($configPath)
    if ($writtenBytes.Length -eq 0) {
        Write-Error "config.json was written but is empty. Disk full or permissions issue at $InstallDir - fix and re-run."
        return
    }
    try {
        Get-Content $configPath -Raw | ConvertFrom-Json | Out-Null
    } catch {
        Write-Error "config.json was written but is not valid JSON: $_. This should not happen - please report this."
        return
    }

    # 5. Dependencies.
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & $python.Source -m pip install --quiet requests psutil

    # 6. Register now, fail loudly if it doesn't work, before installing the scheduled task.
    Write-Host "Registering agent..." -ForegroundColor Yellow
    Push-Location $InstallDir
    & $python.Source registration.py
    $registered = $LASTEXITCODE -eq 0
    Pop-Location
    if (-not $registered) {
        Write-Error "Registration failed. Not installing the scheduled task - fix the error above and re-run."
        return
    }

    # 7. Persistent execution via Scheduled Task (runs at startup, as SYSTEM,
    #    restarts on failure). This avoids requiring a third-party service
    #    wrapper like NSSM just to get something real running.
    $pythonwPath = (Get-Command pythonw -ErrorAction SilentlyContinue)
    $exe = if ($pythonwPath) { $pythonwPath.Source } else { $python.Source }

    $action = New-ScheduledTaskAction -Execute $exe -Argument "`"$InstallDir\main.py`"" -WorkingDirectory $InstallDir
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

    Unregister-ScheduledTask -TaskName "CySIEMAgent" -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName "CySIEMAgent" -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
    Start-ScheduledTask -TaskName "CySIEMAgent"

    Start-Sleep -Seconds 2
    $task = Get-ScheduledTask -TaskName "CySIEMAgent"
    if ($task.State -eq "Running" -or $task.State -eq "Ready") {
        Write-Host "--- Installation Complete: agent task is running ---" -ForegroundColor Green
        Write-Host "Check status with: Get-ScheduledTask -TaskName CySIEMAgent | Get-ScheduledTaskInfo"
    } else {
        Write-Warning "Task installed but state is '$($task.State)'. Check Task Scheduler for details."
    }
}
