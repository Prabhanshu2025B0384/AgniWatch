@echo off
setlocal EnableDelayedExpansion

echo ==================================================
echo               AGNI WATCH - STOP
echo ==================================================

if exist ".run\backend.pid" (
    set /p BACKEND_PID=<".run\backend.pid"
    echo Stopping Backend ^(PID: !BACKEND_PID!^)...
    taskkill /PID !BACKEND_PID! /F /T >nul 2>&1
    del ".run\backend.pid"
) else (
    echo Backend PID not found.
)

if exist ".run\frontend.pid" (
    set /p FRONTEND_PID=<".run\frontend.pid"
    echo Stopping Frontend ^(PID: !FRONTEND_PID!^)...
    taskkill /PID !FRONTEND_PID! /F /T >nul 2>&1
    del ".run\frontend.pid"
) else (
    echo Frontend PID not found.
)

echo All local processes stopped.
