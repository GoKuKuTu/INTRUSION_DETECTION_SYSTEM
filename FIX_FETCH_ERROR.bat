@echo off
echo ========================================
echo   FIXING "Failed to fetch" ERROR
echo ========================================
echo.

echo Step 1: Installing required packages...
cd network-anomaly-detection
pip install fastapi uvicorn pandas numpy scikit-learn joblib requests

echo.
echo Step 2: Starting the backend server...
echo The server will run on http://localhost:8000
echo Keep this window open while testing your frontend!
echo.

python start_server.py

echo.
echo Server stopped. Press any key to exit...
pause >nul
