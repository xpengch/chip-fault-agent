@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Chip Fault AI - System Startup
echo ==========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not running
    echo.
    echo Please start Docker Desktop first:
    echo   1. Click Start menu
    echo   2. Find \"Docker Desktop\"
    echo   3. Wait for tray icon to turn green
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check .env file
if not exist .env (
    echo [Setup] Creating .env from template...
    if exist .env.docker.template (
        copy .env.docker.template .env >nul
        echo [OK] .env created
        echo.
        echo [IMPORTANT] Please edit .env file:
        echo   1. Set ANTHROPIC_API_KEY (or local Qwen3 API)
        echo.
        notepad .env
        set /p CONTINUE="Press Enter when done..."
    ) else (
        echo [Warning] .env.docker.template not found
        echo Creating basic .env...
        echo ANTHROPIC_API_KEY= > .env
        echo Please edit .env and set your API key
        notepad .env
        set /p CONTINUE="Press Enter when done..."
    )
) else (
    echo [OK] .env exists
)
echo.

REM Start services
echo [1/3] Starting databases...
docker compose up -d postgres neo4j redis
timeout /t 5 /nobreak >nul
echo [OK] Databases started
echo.

echo [2/3] Starting backend...
docker compose up -d backend
echo [OK] Backend started
echo.

echo [3/3] Starting frontend...
docker compose up -d frontend
echo [OK] Frontend started
echo.

echo ==========================================
echo   System Starting...
echo   Please wait 30 seconds for services to be ready
echo ==========================================
echo.

for /l %%i in (30,-1,1) do (
    <nul set /p "=   Waiting %%i seconds...^r"
    ping 127.0.0.1 -n 2 >nul
)
echo.

REM Health check
curl -s http://localhost:8889/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo [Warning] Backend may still be starting
    echo          Check: docker compose logs backend
) else (
    echo [OK] Backend is ready!
)
echo.

echo ==========================================
echo   System Started Successfully!
echo ==========================================
echo.
echo    Access URLs:
echo      Frontend:  http://localhost:3000
echo      Backend:   http://localhost:8889
echo      API Docs: http://localhost:8889/docs
echo.
echo    Default Admin:
echo      Username: admin
echo      Password: admin123
echo.
echo    Commands:
echo      View logs: docker compose logs -f
echo      Stop all:   docker compose down
echo      Restart:   docker compose restart
echo.
echo    Common Issues:
echo      - If frontend shows offline: Check VITE_API_BASE_URL
echo      - If backend errors: Check docker compose logs backend
echo      - If BGE model error: Check bge-model folder exists
echo.

pause
