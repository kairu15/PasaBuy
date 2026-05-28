$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo

Write-Host "PasaBuy setup is complete."
