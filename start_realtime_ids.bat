@echo off
REM Startup script for Real-Time IDS (Windows)

echo Starting Real-Time Intrusion Detection System...
echo.

cd network-anomaly-detection

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start the real-time IDS
echo Starting Real-Time IDS API server...
python start_realtime_ids.py %*

pause

