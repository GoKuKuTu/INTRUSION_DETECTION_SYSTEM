@echo off
echo Testing API connection...
echo.

echo Testing health endpoint...
curl -X GET "http://localhost:8000/health" 2>nul
echo.

echo Testing prediction endpoint...
curl -X POST "http://localhost:8000/predict" -H "Content-Type: application/json" -d "{\"features\": [100.5, 50.0, 1024.0, 1.0, 80.0]}" 2>nul
echo.

echo If you see JSON responses above, the API is working!
echo If you see errors, make sure the backend server is running.
pause
