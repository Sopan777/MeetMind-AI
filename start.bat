@echo off
REM Master Launcher for MeetingMind AI Backends
REM This script runs both the main backend and diarization service in a single terminal window.
cd /d %~dp0
backend\venv\Scripts\python.exe -u start_all.py
