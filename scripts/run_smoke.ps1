#!/usr/bin/env pwsh
Write-Output "Activate venv and run smoke test"
. .\.venv\Scripts\Activate.ps1
python smoke_test.py
