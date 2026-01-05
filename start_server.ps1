# PowerShell script to start the backend server
Write-Host "===============================================" -ForegroundColor Green
Write-Host "  NETWORK ANOMALY DETECTION BACKEND SERVER" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Change to the correct directory
Write-Host "Changing to network-anomaly-detection directory..." -ForegroundColor Yellow
Set-Location "network-anomaly-detection"

# Check if Python is available
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found! Please install Python first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install fastapi uvicorn pandas numpy scikit-learn joblib

Write-Host ""
Write-Host "Starting backend server..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Health check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Keep this window open while using your frontend!" -ForegroundColor Red
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Start the server
python simple_server.py

Write-Host ""
Write-Host "Server stopped. Press Enter to exit..." -ForegroundColor Yellow
Read-Host
