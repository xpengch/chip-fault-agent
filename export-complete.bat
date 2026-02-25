@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Complete Offline Package Export
echo   (Includes BGE Model)
echo ==========================================
echo.

set PACKAGE_DIR=offline-package-complete

echo [Step 1/7] Creating directory structure...
if exist %PACKAGE_DIR% rmdir /s /q %PACKAGE_DIR%
mkdir %PACKAGE_DIR%\docker-images
mkdir %PACKAGE_DIR%\python-packages
mkdir %PACKAGE_DIR%\bge-model
mkdir %PACKAGE_DIR%\src
mkdir %PACKAGE_DIR%\frontend-v2
mkdir %PACKAGE_DIR%\sql
mkdir %PACKAGE_DIR%\scripts
echo [OK] Directory created
echo.

echo [Step 2/7] Exporting Docker images...
echo     PostgreSQL with pgvector...
docker save chip_fault_agent-postgres:latest -o %PACKAGE_DIR%\docker-images\postgres.tar
echo     [-] PostgreSQL

docker pull neo4j:5.24-community >nul 2>&1
docker save neo4j:5.24-community -o %PACKAGE_DIR%\docker-images\neo4j.tar
echo     [-] Neo4j

docker pull redis:7-alpine >nul 2>&1
docker save redis:7-alpine -o %PACKAGE_DIR%\docker-images\redis.tar
echo     [-] Redis

docker pull python:3.12-slim >nul 2>&1
docker save python:3.12-slim -o %PACKAGE_DIR%\docker-images\python-base.tar
echo     [-] Python base

echo [OK] Docker images exported
echo.

echo [Step 3/7] Downloading Python dependencies...
mkdir python-temp
python -m venv python-temp\venv
python-temp\venv\Scripts\pip install --upgrade pip -q
python-temp\venv\Scripts\pip download -r requirements.txt -d %PACKAGE_DIR%\python-packages -q
rmdir /s /q python-temp
echo [OK] Python dependencies downloaded
echo.

echo [Step 4/7] Copying project files...
copy docker-compose.yml %PACKAGE_DIR%\ >nul
copy Dockerfile.backend %PACKAGE_DIR%\ >nul
copy Dockerfile.postgres %PACKAGE_DIR%\ >nul
copy .env.docker.template %PACKAGE_DIR%\.env.template
copy offline-import.bat %PACKAGE_DIR%\ >nul
copy README_OFFLINE.md %PACKAGE_DIR%\ >nul
echo [OK] Project files copied
echo.

echo [Step 5/7] Copying source code...
robocopy src %PACKAGE_DIR%\src /E /NFL /NDL /NJH /NJS >nul
robocopy frontend-v2 %PACKAGE_DIR%\frontend-v2 /E /NFL /NDL /NJH /NJS >nul
if exist sql robocopy sql %PACKAGE_DIR%\sql /E /NFL /NDL /NJH /NJS >nul
echo [OK] Source code copied
echo.

echo [Step 6/7] Downloading BGE model...
echo     Model: BAAI/bge-large-zh-v1.5
echo     Size: ~1.3GB
echo     This may take 10-20 minutes...
echo.

python download-bge.py
echo [OK] BGE model downloaded
echo.

echo [Step 7/7] Creating package info...
echo Package: Chip Fault AI Agent - Complete Offline Package > %PACKAGE_DIR%\package-info.txt
echo Date: %date% %time% >> %PACKAGE_DIR%\package-info.txt
echo.
echo Contents: >> %PACKAGE_DIR%\package-info.txt
echo - Docker images (PostgreSQL+pgvector, Neo4j, Redis) >> %PACKAGE_DIR%\package-info.txt
echo - Python dependencies >> %PACKAGE_DIR%\package-info.txt
echo - BGE embedding model (BAAI/bge-large-zh-v1.5) >> %PACKAGE_DIR%\package-info.txt
echo - Complete source code >> %PACKAGE_DIR%\package-info.txt
echo. >> %PACKAGE_DIR%\package-info.txt
echo Installation: Run offline-import.bat on target machine >> %PACKAGE_DIR%\package-info.txt
echo [OK] Package info created
echo.

echo ==========================================
echo   Export Complete!
echo ==========================================
echo.
echo Package location: %PACKAGE_DIR%\
echo.

echo Package contents:
for /f "tokens=*" %%d in ('dir /s /-c %PACKAGE_DIR%') do set SIZE=%%d
echo Total size: %SIZE% bytes
echo.

echo Directory structure:
tree /F %PACKAGE_DIR% | findstr /V "bytes"
echo.

echo Next steps:
echo 1. Copy entire %PACKAGE_DIR%\ folder to target machine
echo 2. On target machine, run:
echo    cd %PACKAGE_DIR%
echo    offline-import.bat
echo.
pause
ENDOFSCRIPT
