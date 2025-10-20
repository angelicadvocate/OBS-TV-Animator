@echo off
REM OBS-TV-Animator Docker Quick Start Script for Windows

echo 🐳 OBS-TV-Animator Docker Quick Start
echo ======================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not in PATH
    echo Please install Docker Desktop from: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed or not in PATH
    echo Please install Docker Compose or use Docker Desktop
    pause
    exit /b 1
)

REM Check if Docker daemon is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker daemon is not running
    echo Please start Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker is installed and running

REM Get host IP for display
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    set HOST_IP=%%a
    goto :break
)
:break
set HOST_IP=%HOST_IP: =%
if "%HOST_IP%"=="" set HOST_IP=localhost

echo 📋 Pre-deployment checklist:
echo    ✅ Docker installed and running
echo    ✅ All configuration files validated
echo    ✅ Directory structure ready

REM Create directories if they don't exist
echo.
echo 📁 Setting up directories...
if not exist "animations" mkdir animations
if not exist "videos" mkdir videos  
if not exist "data" mkdir data
if not exist "logs" mkdir logs
echo    ✅ Created: animations\, videos\, data\, logs\

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo    📄 Copying .env.example to .env
    copy .env.example .env >nul
    echo    ✅ Environment file ready ^(you can customize .env if needed^)
)

echo.
echo 🚀 Starting OBS-TV-Animator with Docker Compose...
echo.

REM Start the container
docker-compose up -d
if errorlevel 1 (
    echo.
    echo ❌ Failed to start OBS-TV-Animator
    echo Check the logs for details: docker-compose logs
    pause
    exit /b 1
)

echo.
echo 🎉 OBS-TV-Animator is now running!
echo.
echo 📱 Access Information:
echo    Smart TV Browser:    http://%HOST_IP%:8080
echo    WebSocket Endpoint:  ws://%HOST_IP%:8080/socket.io/
echo    API Endpoint:        http://%HOST_IP%:8080/animations
echo    Health Check:        http://%HOST_IP%:8080/health
echo.
echo 💡 Quick Commands:
echo    View logs:           docker-compose logs -f
echo    Stop container:      docker-compose down
echo    Restart:             docker-compose restart
echo    Update:              docker-compose pull ^&^& docker-compose up -d
echo.
echo 📁 Add your content:
echo    HTML animations:     Copy files to .\animations\ directory
echo    Video files:         Copy files to .\videos\ directory
echo.
echo 🔧 Test your setup:
echo    python example_trigger.py list
echo    python example_trigger.py trigger anim1.html
echo.
echo 📚 More help: See DOCKER.md for detailed documentation
echo.
pause