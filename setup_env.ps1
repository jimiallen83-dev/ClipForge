# setup_env.ps1 — create .venv and install requirements on Windows
try {
    $py = Get-Command python -ErrorAction Stop
} catch {
    Write-Host "Python not found. Install from https://www.python.org/downloads/windows/ and ensure 'python' is on PATH." -ForegroundColor Yellow
    exit 1
}

Write-Host "Python found: $($py.Source)" -ForegroundColor Green

if (-not (Test-Path -Path .venv)) {
    Write-Host "Creating virtualenv with 'python -m venv .venv'..."
    python -m venv .venv 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "'python' venv creation failed; trying 'py -3 -m venv .venv'..."
        py -3 -m venv .venv 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to create virtualenv with both 'python' and 'py'. Install Python from https://www.python.org/downloads/windows/ and ensure the launcher is available." -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host "Installing pip and requirements into .venv..."
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "Setup complete. Activate with:`n  . .venv\Scripts\Activate.ps1" -ForegroundColor Green
} else {
    Write-Host "Some packages failed to install. Inspect output above." -ForegroundColor Red
    exit 1
}
