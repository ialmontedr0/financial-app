#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Install FIP API as a Windows service using NSSM or as a scheduled task.
#>

$ServiceName = "FIPAPI"
$AppPath = "C:\Program Files\FinancialIntelligencePlatform"
$PythonExe = (Get-Command python).Source
$UvRun = (Get-Command uv).Source

Write-Host "Installing $ServiceName..."

# Create directory
if (-not (Test-Path $AppPath)) {
    New-Item -ItemType Directory -Path $AppPath -Force | Out-Null
}

# Copy files (assuming this runs from the repo root)
Copy-Item -Recurse -Force "backend" "$AppPath\backend"
Copy-Item -Force "pyproject.toml" "$AppPath\"
Copy-Item -Force "uv.lock" "$AppPath\"

# Check if NSSM is available
$nssm = Get-Command nssm -ErrorAction SilentlyContinue

if ($nssm) {
    & nssm install $ServiceName "$UvRun" "run uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4 --log-level info"
    & nssm set $ServiceName AppDirectory $AppPath
    & nssm set $ServiceName DisplayName "Financial Intelligence Platform API"
    & nssm set $ServiceName Description "Backend API for the Financial Intelligence Platform"
    & nssm set $ServiceName Start SERVICE_AUTO_START
    & nssm set $ServiceName AppStdout "$AppPath\logs\stdout.log"
    & nssm set $ServiceName AppStderr "$AppPath\logs\stderr.log"
    & nssm start $ServiceName
    Write-Host "Service installed and started via NSSM"
}
else {
    Write-Warning "NSSM not found. Registering as scheduled task (auto-start on boot)..."
    $Action = New-ScheduledTaskAction -Execute "$UvRun" -Argument "run uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4 --log-level info" -WorkingDirectory $AppPath
    $Trigger = New-ScheduledTaskTrigger -AtStartup
    $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    Register-ScheduledTask -TaskName $ServiceName -Action $Action -Trigger $Trigger -Principal $Principal -Description "Financial Intelligence Platform API"
    Start-ScheduledTask -TaskName $ServiceName
    Write-Host "Scheduled task created and started"
}

Write-Host "Installation complete"
