# PowerShell script to start the backend server
Write-Host "Starting Network Anomaly Detection Backend Server..." -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Change to the correct directory
Set-Location "network-anomaly-detection"

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install fastapi uvicorn pandas numpy scikit-learn joblib

# Start the server
Write-Host "Starting server on http://localhost:8000..." -ForegroundColor Yellow
Write-Host "Keep this window open while using your frontend!" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host "===============================================" -ForegroundColor Green

python simple_server.py
