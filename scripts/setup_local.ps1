#!/usr/bin/env pwsh
Write-Output "Setting up local Python environment..."
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Write-Output "Done. To run smoke test: python smoke_test.py"
