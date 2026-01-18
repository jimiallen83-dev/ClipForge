#!/usr/bin/env pwsh
# launch_app.ps1 - start a new PowerShell window which runs the server and opens the browser
Set-Location $PSScriptRoot
$script = (Join-Path $PSScriptRoot 'run_in_new.ps1')
if (-Not (Test-Path $script)) {
    Write-Error "run_in_new.ps1 not found in $PSScriptRoot"
    exit 1
}

Write-Host "Launching new PowerShell window to run the server..."
Start-Process -FilePath powershell -ArgumentList '-NoExit','-ExecutionPolicy','Bypass','-File',"$script"
Write-Host "New window started. Watch it until it prints 'Uvicorn running on http://127.0.0.1:8000' or 'health:'."
