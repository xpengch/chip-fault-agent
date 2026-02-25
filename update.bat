@echo off
REM System Update Script

echo ==========================================
echo   System Update
echo ==========================================
echo.

REM Stop services
echo [1/4] Stopping current services...
docker compose down
echo.

REM Pull latest code if using git
if exist .git (
    echo [2/4] Pulling latest code...
    git pull
    echo.
)

REM Rebuild images
echo [3/4] Rebuilding images...
docker compose build --no-cache
echo.

REM Start services
echo [4/4] Starting services...
docker compose up -d
echo.

echo [OK] Update complete!
echo.
pause
