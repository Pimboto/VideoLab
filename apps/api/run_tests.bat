@echo off
echo ============================================
echo Video Processor API v2 - Test Runner
echo ============================================
echo.

echo Checking if server is running...
curl -s http://localhost:8000/health >nul 2>&1

if %errorlevel% neq 0 (
    echo.
    echo Server is not running!
    echo.
    echo Please start the server first:
    echo   python app_v2.py
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo Server is running! ✓
echo.
echo Starting comprehensive tests...
echo.

python test_api_v2.py

echo.
echo Tests completed!
echo.
pause
