@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Export Offline Deployment Package
echo ==========================================
echo.

set PACKAGE_DIR=offline-package

echo [1/4] Creating directory structure...
if exist %PACKAGE_DIR% rmdir /s /q %PACKAGE_DIR%
mkdir %PACKAGE_DIR%
mkdir %PACKAGE_DIR%\docker-images
mkdir %PACKAGE_DIR%\python-packages
mkdir %PACKAGE_DIR%\scripts
mkdir %PACKAGE_DIR%\data
echo [OK] Directory created
echo.

echo [2/4] Building and exporting Docker images...
echo     This will take 10-15 minutes...
echo.

echo     [-] Pulling base images...
docker pull postgres:16
docker pull node:20-alpine
docker pull nginx:alpine
docker pull python:3.12-slim
docker pull neo4j:5.24-community
docker pull redis:7-alpine

echo     [-] Building PostgreSQL with pgvector (~5 min)...
docker compose build postgres
docker tag chip_fault_agent-postgres:latest chip-fault-postgres:latest

echo     [-] Building backend (~5 min)...
docker compose build backend
docker tag chip_fault_agent-backend:latest chip-fault-backend:latest

echo     [-] Building frontend (~3 min)...
docker compose build frontend
docker tag chip_fault_agent-frontend:latest chip-fault-frontend:latest

echo     [-] Exporting all images...
docker save chip-fault-postgres:latest -o %PACKAGE_DIR%\docker-images\postgres.tar
docker save chip-fault-backend:latest -o %PACKAGE_DIR%\docker-images\backend.tar
docker save chip-fault-frontend:latest -o %PACKAGE_DIR%\docker-images\frontend.tar
docker save neo4j:5.24-community -o %PACKAGE_DIR%\docker-images\neo4j.tar
docker save redis:7-alpine -o %PACKAGE_DIR%\docker-images\redis.tar

echo [OK] Docker images exported
echo.

echo [3/4] Copying project files...
copy docker-compose.yml %PACKAGE_DIR%\ >nul
copy .env.docker.template %PACKAGE_DIR%\ >nul
copy offline-import.bat %PACKAGE_DIR%\ >nul
copy README_OFFLINE.md %PACKAGE_DIR%\ >nul

xcopy /E /I /Y src %PACKAGE_DIR%\src >nul
if exist sql xcopy /E /I /Y sql %PACKAGE_DIR%\sql >nul
echo [OK] Project files copied
echo.

echo [3/4] Creating BGE model package...
if exist bge-model (
    echo     [-] Found existing BGE model
    echo     [-] Copying to offline package...
    xcopy /E /I /Y bge-model %PACKAGE_DIR%\bge-model >nul
    echo     [-] BGE model included
) else (
    echo     [WARNING] BGE model not found in bge-model directory
    echo     [WARNING] Offline package will not include BGE model
    echo     [WARNING] System will download on first run if not present
)
echo [OK] BGE model check complete
echo.

echo [4/4] Creating package info...
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
