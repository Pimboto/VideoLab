@echo off
echo ============================================
echo Video Processor API v2 - Server Starter
echo Professional Architecture Edition
echo ============================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo ⚠️  Please review and update .env file if needed
    echo.
)

echo Starting server on http://localhost:8000
echo.
echo 📚 API Documentation:
echo   - Swagger UI: http://localhost:8000/docs
echo   - ReDoc:      http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py
