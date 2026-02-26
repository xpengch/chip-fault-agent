@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Load Offline Docker Images
echo ==========================================
echo.
echo This will load Docker images from offline package
echo.

set IMAGE_DIR=offline-package\docker-images

if not exist %IMAGE_DIR% (
    echo [ERROR] Offline images not found at %IMAGE_DIR%
    echo.
    echo Please make sure you have the offline-package directory
    pause
    exit /b 1
)

echo [Found] Offline Docker images:
echo.
for %%f in (%IMAGE_DIR%\*.tar) do (
    echo   - %%~nxf
)
echo.

set /p CONFIRM="Load these images? (Y/N): "
if /i not "!CONFIRM!"=="Y" (
    echo Cancelled
    pause
    exit /b 0
)

echo.
echo [1/6] Loading PostgreSQL with pgvector (pre-built)...
if exist %IMAGE_DIR%\postgres.tar (
    docker load -i %IMAGE_DIR%\postgres.tar
    echo [OK] PostgreSQL loaded
) else (
    echo [Skip] postgres.tar not found
)
echo.

echo [2/6] Loading Node.js (for frontend build)...
if exist %IMAGE_DIR%\node-alpine.tar (
    docker load -i %IMAGE_DIR%\node-alpine.tar
    echo [OK] Node.js loaded
) else (
    echo [Skip] node-alpine.tar not found
)
echo.

echo [3/6] Loading Nginx (for frontend)...
if exist %IMAGE_DIR%\nginx-alpine.tar (
    docker load -i %IMAGE_DIR%\nginx-alpine.tar
    echo [OK] Nginx loaded
) else (
    echo [Skip] nginx-alpine.tar not found
)
echo.

echo [4/6] Loading Neo4j...
if exist %IMAGE_DIR%\neo4j.tar (
    docker load -i %IMAGE_DIR%\neo4j.tar
    echo [OK] Neo4j loaded
) else (
    echo [Skip] neo4j.tar not found
)
echo.

echo [5/6] Loading Redis...
if exist %IMAGE_DIR%\redis.tar (
    docker load -i %IMAGE_DIR%\redis.tar
    echo [OK] Redis loaded
) else (
    echo [Skip] redis.tar not found
)
echo.

echo [6/6] Loading Python base (for backend)...
if exist %IMAGE_DIR%\python-base.tar (
    docker load -i %IMAGE_DIR%\python-base.tar
    echo [OK] Python base loaded
) else (
    echo [Skip] python-base.tar not found
)
echo.

echo ==========================================
echo   All Docker images loaded!
echo ==========================================
echo.
echo You can now run: docker compose up -d
echo.
pause
