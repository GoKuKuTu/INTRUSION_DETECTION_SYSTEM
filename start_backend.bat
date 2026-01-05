@echo off
echo Installing required packages...
cd network-anomaly-detection
pip install fastapi uvicorn pandas numpy scikit-learn joblib

echo.
echo Starting the backend server...
echo The server will be available at http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

python simple_server.py

pause
