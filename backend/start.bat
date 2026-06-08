@echo off
REM Launches the backend with a clean Python environment, preventing Anaconda bleed-in
set PYTHONNOUSERSITE=1
set PYTHONDONTWRITEBYTECODE=1
cd /d %~dp0
venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
