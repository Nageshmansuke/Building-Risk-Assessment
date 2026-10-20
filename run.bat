@echo off
title QuakeGuard AI - Building Risk Predictor
echo ========================================================
echo   Starting QuakeGuard AI - Building Seismic Risk Predictor
echo ========================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    echo Using project virtual environment...
    ".venv\Scripts\python.exe" app.py
) else (
    echo Using system Python...
    python app.py
)

pause
