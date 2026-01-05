@echo off
title Backend Server - Keep This Window Open
color 0A
echo.
echo ========================================
echo   NETWORK ANOMALY DETECTION SERVER
echo ========================================
echo.
echo Starting backend server...
echo Server will be available at: http://localhost:8000
echo.
echo IMPORTANT: Keep this window open while using your frontend!
echo.
echo ========================================
echo.

cd network-anomaly-detection
python simple_server.py

echo.
echo Server stopped. Press any key to exit...
pause >nul
