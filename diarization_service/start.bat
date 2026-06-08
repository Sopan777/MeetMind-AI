@echo off
REM Diarization Microservice Launcher
REM Uses Python 3.12 venv with pyannote.audio 3.1.1 + numpy 1.26.4
set PYTHONNOUSERSITE=1
set PYTHONDONTWRITEBYTECODE=1
cd /d %~dp0
venv\Scripts\python.exe app.py
