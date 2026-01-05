@echo off
title Node.js Backend Server - Keep This Window Open
color 0A
echo.
echo ========================================
echo   NETWORK ANOMALY DETECTION SERVER
echo   (Node.js Version)
echo ========================================
echo.

cd network-anomaly-detection

echo Installing required Node.js packages...
npm install express cors

echo.
echo Starting Node.js backend server...
echo Server will be available at: http://localhost:8000
echo.
echo IMPORTANT: Keep this window open while using your frontend!
echo.

node server.js

echo.
echo Server stopped. Press any key to exit...
pause >nul
