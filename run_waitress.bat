@echo off
title SEISMOS Production Server (Waitress WSGI)
echo ========================================================
echo   Starting SEISMOS Production Server (Waitress WSGI)
echo   Listening on http://127.0.0.1:5000
echo ========================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\waitress-serve.exe" (
    ".venv\Scripts\waitress-serve.exe" --port=5000 wsgi:app
) else (
    ".venv\Scripts\python.exe" -m waitress --port=5000 wsgi:app
)

pause
