@echo off
echo ====================================
echo OBS-TV-Animator LOCAL Dev Server
echo ====================================
echo.
echo Starting LOCAL Python development server...
echo No Docker required - runs directly on your machine!
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.11+ first.
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import flask, flask_socketio, flask_login" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Python requirements...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install requirements. Please check pip installation.
        pause
        exit /b 1
    )
)

echo.
echo 🚀 Starting local development server on port 5000...
echo   TV Display: http://localhost:5000
echo   Admin Panel: http://localhost:5000/admin
echo.
echo Press Ctrl+C to stop the server
echo.

python dev_local.py

echo.
echo Local development server stopped.
pause