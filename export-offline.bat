@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Export Offline Deployment Package
echo ==========================================
echo.

set PACKAGE_DIR=offline-package

echo [1/5] Creating directory structure...
if exist %PACKAGE_DIR% rmdir /s /q %PACKAGE_DIR%
mkdir %PACKAGE_DIR%
mkdir %PACKAGE_DIR%\docker-images
mkdir %PACKAGE_DIR%\python-packages
mkdir %PACKAGE_DIR%\scripts
mkdir %PACKAGE_DIR%\data
echo [OK] Directory created
echo.

echo [2/5] Exporting Docker images...
echo     This may take a while...
echo.

echo     Building and exporting PostgreSQL with pgvector...
docker compose build postgres
docker save chip-fault-postgres -o %PACKAGE_DIR%\docker-images\postgres.tar
echo     [-] PostgreSQL with pgvector

docker save neo4j:5.24-community -o %PACKAGE_DIR%\docker-images\neo4j.tar
echo     [-] Neo4j

docker save redis:7-alpine -o %PACKAGE_DIR%\docker-images\redis.tar
echo     [-] Redis

docker save python:3.12-slim -o %PACKAGE_DIR%\docker-images\python-base.tar
echo     [-] Python base

echo [OK] Docker images exported
echo.

echo [3/5] Downloading Python dependencies...
mkdir python-temp
python -m venv python-temp\venv
python-temp\venv\Scripts\pip install --upgrade pip
python-temp\venv\Scripts\pip download -r requirements.txt -d %PACKAGE_DIR%\python-packages
rmdir /s /q python-temp
echo [OK] Python dependencies downloaded
echo.

echo [4/5] Copying project files...
copy docker-compose.yml %PACKAGE_DIR%\ >nul
copy Dockerfile.backend %PACKAGE_DIR%\ >nul
copy .env.docker.template %PACKAGE_DIR%\ >nul
copy offline-import.bat %PACKAGE_DIR%\ >nul
copy README_OFFLINE.md %PACKAGE_DIR%\ >nul

mkdir %PACKAGE_DIR%\frontend-v2
copy frontend-v2\Dockerfile.frontend %PACKAGE_DIR%\frontend-v2\ >nul
copy frontend-v2\nginx.conf %PACKAGE_DIR%\frontend-v2\ >nul
copy frontend-v2\package.json %PACKAGE_DIR%\frontend-v2\ >nul

xcopy /E /I /Y src %PACKAGE_DIR%\src >nul
if exist sql xcopy /E /I /Y sql %PACKAGE_DIR%\sql >nul
echo [OK] Project files copied
echo.

echo [5/5] Creating package info...
echo Package created: %PACKAGE_DIR% > %PACKAGE_DIR%\package-info.txt
echo Date: %date% %time% >> %PACKAGE_DIR%\package-info.txt
echo [OK] Package info created
echo.

echo ==========================================
echo   Export Complete!
echo ==========================================
echo.
echo Package location: %PACKAGE_DIR%\
echo.
echo Estimated size:
dir %PACKAGE_DIR% /s
echo.
echo Next steps:
echo 1. Copy offline-package folder to target machine
echo 2. Run offline-import.bat on target machine
echo.
pause
