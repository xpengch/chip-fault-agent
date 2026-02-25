@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Chip Fault AI - Online Installation
echo ==========================================
echo.
echo This script will install the Chip Fault AI Agent
echo system with automatic dependency download.
echo.

REM Check Python
echo [Check] Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed!
    echo.
    echo Please install Python 3.12+ from:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% detected
echo.

REM Check Git
echo [Check] Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not installed!
    echo.
    echo Please install Git from:
    echo https://git-scm.com/download/win
    pause
    exit /b 1
)

for /f "tokens=3" %%i in ('git --version') do set GIT_VERSION=%%i
echo [OK] Git %GIT_VERSION% detected
echo.

REM Check Docker (optional)
echo [Check] Docker (optional for full deployment)...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Docker not installed
    echo          You can still use development mode
    set DOCKER_AVAILABLE=0
) else (
    echo [OK] Docker detected
    set DOCKER_AVAILABLE=1

    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Docker Compose not available
        set DOCKER_COMPOSE_AVAILABLE=0
    ) else (
        echo [OK] Docker Compose available
        set DOCKER_COMPOSE_AVAILABLE=1
    )
)
echo.

REM Ask installation mode
echo ==========================================
echo   Select Installation Mode
echo ==========================================
echo.
echo 1. Quick Start (Docker) - Recommended for production
echo    - Install all services with Docker
echo    - Requires Docker Desktop
echo.
echo 2. Development Mode - For developers
echo    - Install dependencies locally
echo    - Run services manually
echo.
echo 3. Minimal Mode - Backend only
echo    - Install Python dependencies only
echo.
set /p MODE="Select mode (1/2/3): "

if "%MODE%"=="1" (
    if !DOCKER_AVAILABLE!==0 (
        echo [ERROR] Docker mode selected but Docker not available!
        echo        Please install Docker Desktop first
        pause
        exit /b 1
    )
    goto :docker_install
)

if "%MODE%"=="2" goto :dev_install
if "%MODE%"=="3" goto :minimal_install

echo [ERROR] Invalid selection
pause
exit /b 1

:docker_install
echo.
echo ==========================================
echo   Docker Installation
echo ==========================================
echo.

REM Clone or update repository
if exist "git config --get remote.origin.url" >nul 2>&1 (
    echo [INFO] Repository already exists
    set /p UPDATE="Update repository? (y/n): "
    if /i "!UPDATE!"=="y" (
        echo [1/5] Updating repository...
        git pull origin master
    )
) else (
    echo [1/5] Cloning repository...
    git clone https://github.com/xpengch/chip-fault-agent.git
    cd chip_fault_agent
)

echo [OK] Repository ready
echo.

REM Download BGE model
echo [2/5] Checking BGE model...
if not exist bge-model (
    echo BGE model will be downloaded on first run
    echo Run download-bge.py to download it now (optional)
) else (
    echo [OK] BGE model found
)
echo.

REM Configure environment
echo [3/5] Configuring environment...
if not exist .env (
    if exist .env.docker.template (
        copy .env.docker.template .env >nul
        echo.
        echo [IMPORTANT] Please edit .env file and set:
        echo              - ANTHROPIC_API_KEY
        echo.
        notepad .env
        echo.
        set /p CONTINUE="Press Enter after configuration..."
    ) else (
        echo [WARNING] .env.docker.template not found
        echo          Creating basic .env file...
        echo ANTHROPIC_API_KEY=your_api_key_here > .env
        echo Please edit .env and set your API key
        notepad .env
    )
) else (
    echo [OK] .env file exists
)
echo.

REM Build Docker images
echo [4/5] Building Docker images...
docker compose build
if errorlevel 1 (
    echo [WARNING] Docker build had issues
    echo          Check logs above for details
)
echo [OK] Docker images ready
echo.

REM Start services
echo [5/5] Starting services...
docker compose up -d
echo [OK] Services started
echo.

REM Wait for services
echo Waiting for services to be ready...
timeout /t 30 /nobreak >nul

curl -s http://localhost:8889/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Backend service may not be fully ready
    echo          Check logs: docker compose logs -f
) else (
    echo [OK] Backend service ready
)
echo.

goto :success

:dev_install
echo.
echo ==========================================
echo   Development Installation
echo ==========================================
echo.

REM Check if in repository
if not exist "git config --get remote.origin.url" >nul 2>&1 (
    echo [1/6] Cloning repository...
    git clone https://github.com/xpengch/chip-fault-agent.git
    cd chip_fault_agent
)

echo [2/6] Creating virtual environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
echo [OK] Virtual environment created
echo.

echo [3/6] Installing Python dependencies...
python -m pip install --upgrade pip -q
pip install -r requirements.txt
echo [OK] Dependencies installed
echo.

echo [4/6] Downloading BGE model...
python scripts/init_bge_model.py
echo [OK] BGE model initialized
echo.

echo [5/6] Configuring environment...
if not exist .env (
    if exist .env.docker.template (
        copy .env.docker.template .env >nul
    ) else (
        echo ANTHROPIC_API_KEY=your_api_key_here > .env
        echo POSTGRES_HOST=localhost >> .env
        echo NEO4J_URI=bolt://localhost:7687 >> .env
        echo REDIS_HOST=localhost >> .env
    )
    echo.
    echo [IMPORTANT] Please edit .env file and set your API keys
    notepad .env
)
echo [OK] Environment configured
echo.

echo [6/6] Installing frontend dependencies...
cd frontend-v2
call npm install
echo [OK] Frontend dependencies installed
cd ..
echo.

echo ==========================================
echo   Development Setup Complete!
echo ==========================================
echo.
echo To start the development servers:
echo.
echo 1. Start databases (if using Docker):
echo    docker compose up -d postgres neo4j redis
echo.
echo 2. Start backend (new terminal):
echo    .\venv\Scripts\activate
echo    uvicorn src.api.app:app --host 0.0.0.0 --port 8889 --reload
echo.
echo 3. Start frontend (new terminal):
echo    cd frontend-v2
echo    npm run dev
echo.
pause
exit /b 0

:minimal_install
echo.
echo ==========================================
echo   Minimal Installation (Backend Only)
echo ==========================================
echo.

echo [1/4] Creating virtual environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
echo [OK] Virtual environment created
echo.

echo [2/4] Installing Python dependencies...
python -m pip install --upgrade pip -q
pip install -r requirements.txt
echo [OK] Dependencies installed
echo.

echo [3/4] Configuring environment...
if not exist .env (
    echo ANTHROPIC_API_KEY=your_api_key_here > .env
    echo POSTGRES_HOST=localhost >> .env
    echo NEO4J_URI=bolt://localhost:7687 >> .env
    echo REDIS_HOST=localhost >> .env
    echo.
    echo [IMPORTANT] Please edit .env file and set your API keys
    notepad .env
)
echo [OK] Environment configured
echo.

echo [4/4] Initializing BGE model...
python scripts/init_bge_model.py
echo [OK] BGE model initialized
echo.

echo ==========================================
echo   Minimal Installation Complete!
echo ==========================================
echo.
echo To start the backend:
echo.
echo 1. Activate virtual environment:
echo    .\venv\Scripts\activate
echo.
echo 2. Start the server:
echo    uvicorn src.api.app:app --host 0.0.0.0 --port 8889
echo.
pause
exit /b 0

:success
echo ==========================================
echo   Installation Complete!
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
echo   Status:   docker compose ps
echo.
echo Documentation:
echo   https://github.com/xpengch/chip-fault-agent
echo.
pause
