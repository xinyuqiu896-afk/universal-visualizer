@echo off
setlocal
title Universal Visualizer Launcher

set "ROOT=%~dp0"
set "PY=C:\Users\28299\.workbuddy\binaries\python\envs\default\Scripts\python.exe"

echo [1/3] Starting backend (port 8000) ...
cd /d "%ROOT%backend"
start "backend-8000" cmd /k ""%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo [2/3] Starting frontend (port 5173) ...
cd /d "%ROOT%frontend"
start "frontend-5173" cmd /k "npm run dev"

echo [3/3] Opening browser in 8 seconds ...
timeout /t 8 >nul
start "" http://localhost:5173

echo.
echo Done. Backend: http://localhost:8000/docs
echo Frontend:    http://localhost:5173
echo Close the two windows to stop the app.
pause
