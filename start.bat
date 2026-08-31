@echo off
setlocal EnableDelayedExpansion

echo ==================================================
echo               AGNI WATCH
echo ==================================================

if not exist ".run" mkdir .run
if not exist "logs" mkdir logs

echo [1/5] Preparing backend environment...
cd backend
if not exist "venv\Scripts\python.exe" (
    if exist "venv" (
        echo Recreating broken virtual environment...
        rmdir /s /q venv
    ) else (
        echo Creating virtual environment...
    )
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment. Ensure python is installed and on PATH.
        exit /b 1
    )
)
cd ..

echo [2/5] Installing/verifying backend dependencies...
cd backend
venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
venv\Scripts\python.exe -m pip install -r requirements.txt > ..\logs\pip_install.log 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install backend dependencies. Check logs\pip_install.log
    exit /b 1
)
cd ..

echo [3/5] Starting backend...
powershell -Command "$process = Start-Process -FilePath 'backend\venv\Scripts\python.exe' -ArgumentList '-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend' -NoNewWindow -PassThru -RedirectStandardOutput 'logs\backend.log' -RedirectStandardError 'logs\backend_err.log'; $process.Id | Out-File -FilePath '.run\backend.pid' -Encoding ASCII"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start backend.
    exit /b 1
)

echo Waiting for backend...
powershell -Command "$maxRetries=30; $retryCount=0; $connected=$false; while($retryCount -lt $maxRetries) { $result = Test-NetConnection localhost -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue; if ($result) { $connected=$true; break; } Start-Sleep -Seconds 1; $retryCount++; } if ($connected) { Write-Host 'Backend: ONLINE' } else { Write-Host 'BACKEND: FAILED TO START'; Write-Host 'FRONTEND: NOT STARTED'; exit 1 }"
if %errorlevel% neq 0 (
    echo Please inspect logs\backend.log and logs\backend_err.log
    exit /b 1
)

echo [4/5] Installing/verifying frontend dependencies...
cd frontend
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install > ..\logs\npm_install.log 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install frontend dependencies. Check logs\npm_install.log
        exit /b 1
    )
)
cd ..

echo [5/5] Starting frontend...

echo.
echo ==================================================
echo               AGNI WATCH IS READY
echo ==================================================
echo Opening browser...
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo ==================================================
echo.

:: Automatically open browser
start http://localhost:5173

cd frontend
powershell -Command "& { $process = Start-Process -FilePath 'npm.cmd' -ArgumentList 'run dev' -NoNewWindow -PassThru -RedirectStandardOutput '..\logs\frontend.log' -RedirectStandardError '..\logs\frontend_err.log'; $process.Id | Out-File -FilePath '..\.run\frontend.pid' -Encoding ASCII; Wait-Process -Id $process.Id }"
