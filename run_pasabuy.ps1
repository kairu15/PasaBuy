$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found. Run setup_pasabuy.ps1 first."
    exit 1
}

.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8001
