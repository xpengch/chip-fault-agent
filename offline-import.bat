@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Chip Fault AI - Offline Deployment
echo ==========================================
echo.

REM Check Docker
echo [Check] Docker environment...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not installed!
    echo.
    echo Docker Desktop is required for this application.
    echo.
    if exist DockerDesktopInstaller.exe (
        echo [INFO] Docker Desktop Installer is included in this package!
        echo        Please run: DockerDesktopInstaller.exe
        echo        Then restart your computer and run this script again.
    ) else (
        echo Please download and install Docker Desktop for Windows:
        echo https://www.docker.com/products/docker-desktop
    )
    echo.
    pause
    exit /b 1
)
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose not available!
    echo Please update Docker Desktop
    pause
    exit /b 1
)
echo [OK] Docker environment ready
echo.

echo [1/7] Loading Docker images...
echo     This may take a while...
echo     Note: First load may take several minutes
echo.

if exist docker-images\postgres.tar (
    docker load -i docker-images\postgres.tar
    echo     [-] PostgreSQL with pgvector
)

if exist docker-images\neo4j.tar (
    docker load -i docker-images\neo4j.tar
    echo     [-] Neo4j
)

if exist docker-images\redis.tar (
    docker load -i docker-images\redis.tar
    echo     [-] Redis
)

if exist docker-images\python-base.tar (
    docker load -i docker-images\python-base.tar
    echo     [-] Python base
)

echo [OK] Docker images loaded
echo.

echo [2/7] Creating Python virtual environment...
if not exist venv (
    python -m venv venv
)
echo [OK] Virtual environment created
echo.

echo [3/7] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install --no-index --find-links=python-packages -r requirements.txt
echo [OK] Python dependencies installed
echo.

echo [3.5/7] Checking BGE model...
if exist bge-model (
    echo [OK] BGE model found in bge-model directory
    echo     The model will be mounted to the container
) else (
    echo [WARNING] BGE model not found!
    echo     The system will download it on first run (~1.3GB)
    echo     For true offline deployment, include the bge-model folder
)
echo.

echo [4/7] Configuring environment...
if not exist .env (
    if exist .env.docker.template (
        copy .env.docker.template .env >nul
        echo.
        echo [IMPORTANT] Please edit .env file and set ANTHROPIC_API_KEY
        notepad .env
        echo.
        set /p CONTINUE="Press Enter after configuration..."
    )
)
echo [OK] Environment configured
echo.

echo [5/7] Initializing database...
if not exist sql mkdir sql
if not exist sql\init.sql (
            echo CREATE EXTENSION IF NOT EXISTS vector; > sql\init.sql
)
echo [OK] Database initialized
echo.

echo [6/7] Starting services...
docker compose up -d
echo [OK] Services started
echo.

echo [7/7] Waiting for services to be ready...
timeout /t 30 /nobreak >nul

curl -s http://localhost:8889/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Backend service may not be fully ready
    echo Check logs: docker compose logs
) else (
    echo [OK] Backend service ready
)
echo.

echo ==========================================
echo   Deployment Complete!
echo ==========================================
echo.
echo Access URLs:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8889
echo   Docs:     http://localhost:8889/docs
echo.
echo Common commands:
echo   View logs: docker compose logs -f
echo   Stop:     docker compose down
echo   Restart:  docker compose restart
echo.
pause
