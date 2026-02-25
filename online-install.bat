@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Chip Fault AI - One-Click Installer
echo ==========================================
echo.
echo This script will install Chip Fault AI system
echo.

REM ============================================================
REM Check winget availability
REM ============================================================

echo [Check] winget availability...
winget --version >nul 2>&1
set WINGET_AVAILABLE=!errorlevel!

if !WINGET_AVAILABLE! neq 0 (
    echo [Warning] winget not available
    echo.
    echo Install winget first:
    echo   Microsoft Store -^> Search \"App Installer\"
    echo.
    echo Or manually install:
    echo   Python: https://www.python.org/downloads/
    echo   Git: https://github.com/git-for-windows/git/releases/latest
    echo   Docker: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo [OK] winget available
echo.

REM ============================================================
REM Phase 1: Environment Setup
REM ============================================================

echo.
echo ==========================================
echo   Phase 1: Environment Setup
echo ==========================================
echo.

REM --- Python ---
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [Installing] Python 3.12...
    winget install Python.Python.3.12 --accept-package-agreements --silent
    if errorlevel 1 (
        echo [Failed] Manual download: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo [Success] Restart script to continue
    pause
    exit /b 0
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION%
echo.

REM --- Git ---
echo [2/4] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [Installing] Git...
    winget install Git.Git --accept-package-agreements --silent
    if errorlevel 1 (
        echo [Failed] Manual download: https://github.com/git-for-windows/git/releases/latest
        pause
        exit /b 1
    )
    echo [Success] Restart script to continue
    pause
    exit /b 0
)
for /f "tokens=3" %%i in ('git --version') do set GIT_VERSION=%%i
echo [OK] Git %GIT_VERSION%
echo.

REM --- Docker ---
echo [3/4] Checking Docker...

REM Check if docker command works
docker --version >nul 2>&1
if errorlevel 1 (
    REM Check if Docker Desktop is installed
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        echo [Found] Docker Desktop is installed but not running
        echo.
        echo Please start Docker Desktop:
        echo   1. Click Start menu
        echo   2. Find \"Docker Desktop\"
        echo   3. Click to start
        echo   4. Wait for tray icon to turn green
        echo.
        set /p TRY_AGAIN="Press Enter when Docker is running..."

        REM Try again
        docker --version >nul 2>&1
        if errorlevel 1 (
            echo [Still not available] Docker Desktop may need system restart
            echo.
            set /p RESTART="Restart computer now? (Y/N): "
            if /i "!RESTART!"=="Y" (
                shutdown /r /t 10 /c "Restarting for Docker Desktop"
                echo Restarting in 10 seconds...
                pause
                exit /b 0
            )
            pause
            exit /b 1
        )
    ) else (
        echo [Not Installed] Docker Desktop
        echo.
        echo [Installing] Docker Desktop...
        echo This takes several minutes...
        echo.

        winget install Docker.DockerDesktop --accept-package-agreements --silent
        if errorlevel 1 (
            echo [Failed] Manual: https://www.docker.com/products/docker-desktop
            pause
            exit /b 1
        )

        echo.
        echo ==========================================
        echo   Docker Desktop Installed
        echo ==========================================
        echo.
        echo IMPORTANT:
        echo   1. RESTART your computer
        echo   2. Start Docker Desktop
        echo   3. Wait for green tray icon
        echo   4. Run this script again
        echo.

        set /p RESTART="Restart now? (Y/N): "
        if /i "!RESTART!"=="Y" (
            shutdown /r /t 10 /c "Restarting for Docker Desktop"
            echo Restarting in 10 seconds...
            pause
        )
        exit /b 0
    )
)

for /f "tokens=3" %%i in ('docker --version') do set DOCKER_VERSION=%%i
echo [OK] Docker %DOCKER_VERSION%
echo.

REM --- Docker Compose ---
echo [4/4] Checking Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [Waiting] Docker Desktop still starting...
    echo Wait 10 seconds...
    ping 127.0.0.1 -n 11 >nul

    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [Error] Docker Compose not available
        echo Make sure Docker Desktop is fully started
        pause
        exit /b 1
    )
)
for /f "tokens=4" %%i in ('docker compose version') do set COMPOSE_VERSION=%%i
echo [OK] Docker Compose %COMPOSE_VERSION%
echo.

echo ==========================================
echo   All Dependencies Ready
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

set /p DIR_CHOICE="Install directory (1=Current, 2=Custom): "
if "!DIR_CHOICE!"=="2" (
    set /p CUSTOM_DIR="Enter path (e.g. D:\chip_fault_agent): "
    if not exist "!CUSTOM_DIR!" mkdir "!CUSTOM_DIR!"
    cd /d "!CUSTOM_DIR!"
)

echo [1/5] Getting repository...
if exist .git (
    set /p UPDATE="Update repository? (Y/N): "
    if /i "!UPDATE!"=="Y" git pull origin master
) else (
    git clone https://github.com/xpengch/chip-fault-agent.git temp_install
    xcopy temp_install\*.* /E /I /H /Y .
    rmdir /s /q temp_install
)
echo [OK] Repository ready
echo.

echo [2/5] BGE model check...
if not exist bge-model echo Will download on first run (~2.4GB)
echo.

echo [3/5] Configuring environment...
if not exist .env (
    if exist .env.docker.template (
        copy .env.docker.template .env >nul
        echo.
        echo Set your Anthropic API Key:
        echo Get from: https://console.anthropic.com/
        set /p API_KEY="Enter API Key: "
        powershell -Command "(Get-Content .env) -replace 'ANTHROPIC_API_KEY=.*', 'ANTHROPIC_API_KEY=%API_KEY%' | Set-Content .env"
        echo [OK] API Key configured
    )
)
echo [OK] Environment ready
echo.

echo [4/5] Building Docker images (5-10 min)...
docker compose build
echo [OK] Images built
echo.

echo [5/5] Starting services...
docker compose up -d
echo [OK] Services started
echo.

echo Waiting for services (30 seconds)...
for /l %%i in (30,-1,1) do (
    <nul set /p "=   %%i seconds...^r"
    ping 127.0.0.1 -n 2 >nul
)
echo.

curl -s http://localhost:8889/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo [Warning] Backend may still be starting
) else (
    echo [OK] Backend ready
)
echo.

echo ==========================================
echo   Installation Complete
echo ==========================================
echo.
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8889
echo   Docs:      http://localhost:8889/docs
echo.
echo   Admin:     admin / admin123
echo.
echo   Commands:
echo     docker compose logs -f
echo     docker compose down
echo     docker compose restart
echo.

set /p OPEN="Open browser? (Y/N): "
if /i "!OPEN!"=="Y" start http://localhost:3000

pause
