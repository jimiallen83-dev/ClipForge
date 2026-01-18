param(
    [int]$Port = 8000
)

# run_dev.ps1 - activate venv and start uvicorn, writing logs to uvicorn.log
Set-Location $PSScriptRoot

if (-Not (Test-Path .venv)) {
    Write-Error ".venv not found in $PSScriptRoot"
    exit 1
}

# Relax execution policy for current user so activation can run (no prompt)
try {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
} catch {
    # ignore if not permitted
}

Write-Host "Activating .venv and starting uvicorn on port $Port (logs -> uvicorn.out.log / uvicorn.err.log)"
& .venv\Scripts\Activate.ps1

# Start uvicorn via venv python and redirect output to separate files to avoid file locks
Remove-Item .\uvicorn.out.log -ErrorAction SilentlyContinue
Remove-Item .\uvicorn.err.log -ErrorAction SilentlyContinue
Start-Process -FilePath '.\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','app:app','--host','127.0.0.1','--port',$Port,'--log-level','debug' -NoNewWindow -RedirectStandardOutput '.\uvicorn.out.log' -RedirectStandardError '.\uvicorn.err.log'

Write-Host "Uvicorn started in background. Use .\tail_uvicorn.ps1 -Lines 200 to view logs or run .\restart_uvicorn.ps1 to run foreground."
