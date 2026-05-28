@echo off
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Run setup_pasabuy.ps1 first.
    exit /b 1
)
".venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8001
