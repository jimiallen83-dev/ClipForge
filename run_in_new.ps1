# run_in_new.ps1
# Intended to be executed inside a new PowerShell window.
Set-Location $PSScriptRoot

# Activate venv (no error if already active)
if (Test-Path .venv\Scripts\Activate.ps1) {
    & .venv\Scripts\Activate.ps1
}

# Remove old logs
Remove-Item .\uvicorn.out.log -ErrorAction SilentlyContinue
Remove-Item .\uvicorn.err.log -ErrorAction SilentlyContinue

Write-Host "Starting uvicorn in background (logs -> uvicorn.out.log / uvicorn.err.log)"
$proc = Start-Process -FilePath (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') -ArgumentList '-m','uvicorn','app:app','--host','127.0.0.1','--port','8000','--log-level','info' -WorkingDirectory $PSScriptRoot -NoNewWindow -RedirectStandardOutput (Join-Path $PSScriptRoot 'uvicorn.out.log') -RedirectStandardError (Join-Path $PSScriptRoot 'uvicorn.err.log') -PassThru

# Poll /health until available (30s timeout)
Write-Host "Waiting for /health..."
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri http://127.0.0.1:8000/health -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r -and $r.Content) {
            Write-Host "health: $($r.Content)"
            $healthy = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if ($healthy) {
    Write-Host "Opening browser to http://127.0.0.1:8000 and docs"
    Start-Process "http://127.0.0.1:8000"
    Start-Process "http://127.0.0.1:8000/docs"
} else {
    Write-Host "Server didn't respond to /health within timeout. Check uvicorn.err.log and uvicorn.out.log"
}

Write-Host "Server PID: $($proc.Id). Window will remain open. Press Enter to exit and stop the background process." 
Read-Host "Press Enter to exit"

# When user exits, attempt to stop the started process
try {
    if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force }
} catch {
}
