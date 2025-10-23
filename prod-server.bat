@echo off
echo ====================================
echo OBS-TV-Animator Production Server
echo ====================================
echo.
echo Starting production server...
echo.

REM Stop any existing containers
docker-compose down 2>nul
docker-compose -f docker-compose.dev.yml down 2>nul

REM Start production server
docker-compose up -d --build

echo.
echo Production server started successfully!
echo Access at: http://localhost:8080
echo.
echo To view logs: docker logs obs-tv-animator -f
echo To stop: docker-compose down
echo.
pause