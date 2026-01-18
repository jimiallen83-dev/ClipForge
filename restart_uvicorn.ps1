param(
    [int]$Port = 8000
)

Set-Location $PSScriptRoot

# Stop python processes that originate from the project folder
Get-Process -Name python -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -and ($_.Path -like "*\OneDrive\Desktop\ClipForge\*") } |
    ForEach-Object {
        Write-Host "Stopping process" $_.Id
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }

Remove-Item uvicorn.log -ErrorAction SilentlyContinue

Write-Host "Starting uvicorn (foreground) on port $Port - use Ctrl+C to stop"
& .\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port $Port --log-level debug
