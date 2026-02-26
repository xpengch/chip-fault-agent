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
echo [1/5] Loading PostgreSQL with pgvector (pre-built)...
if exist %IMAGE_DIR%\postgres.tar (
    docker load -i %IMAGE_DIR%\postgres.tar
    echo [OK] PostgreSQL loaded
) else (
    echo [Skip] postgres.tar not found
)
echo.

echo [2/5] Loading Backend (pre-built)...
if exist %IMAGE_DIR%\backend.tar (
    docker load -i %IMAGE_DIR%\backend.tar
    echo [OK] Backend loaded
) else (
    echo [Skip] backend.tar not found
)
echo.

echo [3/5] Loading Frontend (pre-built)...
if exist %IMAGE_DIR%\frontend.tar (
    docker load -i %IMAGE_DIR%\frontend.tar
    echo [OK] Frontend loaded
) else (
    echo [Skip] frontend.tar not found
)
echo.

echo [4/5] Loading Neo4j...
if exist %IMAGE_DIR%\neo4j.tar (
    docker load -i %IMAGE_DIR%\neo4j.tar
    echo [OK] Neo4j loaded
) else (
    echo [Skip] neo4j.tar not found
)
echo.

echo [5/5] Loading Redis...
if exist %IMAGE_DIR%\redis.tar (
    docker load -i %IMAGE_DIR%\redis.tar
    echo [OK] Redis loaded
) else (
    echo [Skip] redis.tar not found
)
echo.

echo ==========================================
echo   All Docker images loaded!
echo ==========================================
echo.
echo You can now run: docker compose up -d
echo.
pause
