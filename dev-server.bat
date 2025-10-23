@echo off
echo ====================================
echo OBS-TV-Animator Development Server
echo ====================================
echo.
echo Starting development server with hot reload on port 8081...
echo Changes to Python, HTML, CSS, and JS files will be reflected immediately!
echo.
echo Access development server at: http://localhost:8081
echo Admin interface at: http://localhost:8081/admin
echo.
echo Press Ctrl+C to stop the development server
echo.

REM Stop any existing containers
docker-compose -f docker-compose.dev.yml down 2>nul

REM Start development server
docker-compose -f docker-compose.dev.yml up --build

echo.
echo Development server stopped.
pause