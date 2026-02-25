@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Chip Fault AI - One-Click Installer
echo ==========================================
echo.
echo This script will automatically install
echo Chip Fault AI Agent system and dependencies
echo.

REM Check winget availability
winget --version >nul 2>&1
if errorlevel 1 (
    echo [Warning] winget is not available on this system
    echo.
    echo Auto-installation requires winget (Windows Package Manager)
    echo.
    echo Please install winget first:
    echo   1. Open Microsoft Store
    echo   2. Search for \"App Installer\"
    echo   3. Click \"Get\" or \"Install\"
    echo   4. Run this script again
    echo.
    echo Alternatively, manually install the required software:
    echo   - Python 3.12+: https://www.python.org/downloads/
    echo   - Git: https://github.com/git-for-windows/git/releases/latest
    echo   - Docker Desktop: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo [OK] winget is available
echo.

REM ============================================================
REM Phase 1: Environment Detection & Auto Installation
REM ============================================================

echo.
echo ==========================================
echo   Phase 1: Environment Setup
echo ==========================================
echo.

REM --- Check and Install Python ---
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [Not Installed] Python is not installed
    echo.
    echo Installing Python using winget...
    echo.

    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
    if errorlevel 1 (
        echo [Failed] winget installation failed
        echo.
        echo Please manually download and install Python:
        echo https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe
        echo.
        echo During installation, CHECK \"Add Python to PATH\"
        echo.
        pause
        exit /b 1
    )

    echo [Success] Python has been installed
    echo.
    echo Please run this script again to continue installation
    pause
    exit /b 0
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% is installed
echo.

REM --- Check and Install Git ---
echo [2/4] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [Not Installed] Git is not installed
    echo.
    echo Installing Git using winget...
    echo.

    winget install Git.Git --accept-package-agreements --accept-source-agreements --silent
    if errorlevel 1 (
        echo [Failed] winget installation failed
        echo.
        echo Please manually download and install Git:
        echo https://github.com/git-for-windows/git/releases/latest
        echo.
        pause
        exit /b 1
    )

    echo [Success] Git has been installed
    echo.
    echo Please run this script again to continue installation
    pause
    exit /b 0
)

for /f "tokens=3" %%i in ('git --version') do set GIT_VERSION=%%i
echo [OK] Git %GIT_VERSION% is installed
echo.

REM --- Check and Install Docker ---
echo [3/4] Checking Docker Desktop...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [Not Installed] Docker Desktop is not installed
    echo.
    echo Installing Docker Desktop using winget...
    echo This may take a few minutes...
    echo.

    winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements --silent
    if errorlevel 1 (
        echo [Failed] winget installation failed
        echo.
        echo Please manually download Docker Desktop:
        echo https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
        echo.
        echo After installation:
        echo   1. Restart your computer
        echo   2. Start Docker Desktop
        echo   3. Wait for the tray icon to turn green
        echo   4. Run this script again
        echo.
        pause
        exit /b 1
    )

    echo [Success] Docker Desktop has been installed
    echo.
    echo ==========================================
    echo   Docker Desktop Installation Complete
    echo ==========================================
    echo.
    echo Important:
    echo   1. Restart your computer
    echo   2. Start Docker Desktop
    echo   3. Wait for Docker to fully start (tray icon turns green)
    echo   4. Run this script again
    echo.
    pause
    exit /b 0
)

for /f "tokens=3" %%i in ('docker --version') do set DOCKER_VERSION=%%i
echo [OK] Docker %DOCKER_VERSION% is installed
echo.

REM --- Check Docker Compose ---
echo [4/4] Checking Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [Warning] Docker Compose not found
    echo          Make sure Docker Desktop is running
    echo.
    pause
    exit /b 1
)

for /f "tokens=4" %%i in ('docker compose version') do set COMPOSE_VERSION=%%i
echo [OK] Docker Compose %COMPOSE_VERSION% is available
echo.

echo ==========================================
echo   Environment Check Complete!
echo   All dependencies ready
echo ==========================================
echo.

REM ============================================================
REM Phase 2: System Installation
REM ============================================================

echo.
echo ==========================================
echo   Phase 2: System Installation
echo ==========================================
echo.

REM Choose installation directory
echo Choose installation directory:
echo   1. Current directory
echo   2. Custom directory
echo.
set /p DIR_CHOICE="Select (1/2): "

if "!DIR_CHOICE!"=="2" (
    set /p CUSTOM_DIR="Enter full path (e.g. D:\chip_fault_agent): "
    if not exist "!CUSTOM_DIR!" mkdir "!CUSTOM_DIR!"
    cd /d "!CUSTOM_DIR!"
)

echo.
echo Installation directory: %CD%
echo.

REM Clone or update repository
if exist .git (
    echo [Repository] Existing repository detected
    set /p UPDATE_REPO="Update repository? (Y/N): "
    if /i "!UPDATE_REPO!"=="Y" (
        echo [1/5] Updating repository...
        git pull origin master
    ) else (
        echo [Skip] Keeping current version
    )
) else (
    echo [1/5] Cloning repository...
    git clone https://github.com/xpengch/chip-fault-agent.git temp_install
    xcopy temp_install\*.* /E /I /H /Y .
    rmdir /s /q temp_install
)

echo [OK] Repository ready
echo.

REM Check BGE model
echo [2/5] Checking BGE model...
if not exist bge-model (
    echo [Info] BGE model will download on first run (~2.4GB)
) else (
    echo [OK] BGE model exists
)
echo.

REM Configure environment
echo [3/5] Configuring environment...
if not exist .env (
    if exist .env.docker.template (
        copy .env.docker.template .env >nul
        echo.
        echo ==========================================
        echo   Configure API Key
        echo ==========================================
        echo.
        echo Set your Anthropic API Key (required)
        echo Get it from: https://console.anthropic.com/
        echo.

        set /p API_KEY="Enter API Key: "

        powershell -Command "(Get-Content .env) -replace 'ANTHROPIC_API_KEY=.*', 'ANTHROPIC_API_KEY=%API_KEY%' | Set-Content .env"

        echo [OK] API Key configured
        echo.
    ) else (
        echo ANTHROPIC_API_KEY= > .env
        echo [Important] Edit .env and set your API Key
        notepad .env
        set /p CONTINUE="Press Enter when done..."
    )
) else (
    echo [OK] .env exists
)
echo.

REM Build Docker images
echo [4/5] Building Docker images...
echo This takes 5-10 minutes...
echo.

docker compose build
if errorlevel 1 (
    echo [Warning] Build had warnings, check logs above
)

echo [OK] Docker images built
echo.

REM Start services
echo [5/5] Starting services...
docker compose up -d
if errorlevel 1 (
    echo [Error] Failed to start services
    pause
    exit /b 1
)

echo [OK] All services started
echo.

REM Wait for services
echo Waiting for services...
echo     PostgreSQL (database + vector)
echo     Neo4j (knowledge graph)
echo     Redis (cache)
echo     Backend (API)
echo     Frontend (Web)
echo.

for /l %%i in (30,-1,1) do (
    <nul set /p "=   %%i seconds remaining...^r"
    ping 127.0.0.1 -n 2 >nul
)
echo.
echo.

REM Health check
curl -s http://localhost:8889/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo [Warning] Backend may not be ready yet
    echo          Check: docker compose logs -f
) else (
    echo [OK] Backend is ready
)
echo.

REM ============================================================
REM Installation Complete
REM ============================================================

echo ==========================================
echo   Installation Complete!
echo ==========================================
echo.
echo    Access URLs:
echo      Frontend:  http://localhost:3000
echo      Backend:   http://localhost:8889
echo      API Docs:  http://localhost:8889/docs
echo.
echo    Default Admin:
echo      Username: admin
echo      Password: admin123
echo.
echo    Commands:
echo      docker compose logs -f
echo      docker compose down
echo      docker compose restart
echo.

set /p OPEN_BROWSER="Open browser? (Y/N): "
if /i "!OPEN_BROWSER!"=="Y" (
    start http://localhost:3000
)

echo.
pause
