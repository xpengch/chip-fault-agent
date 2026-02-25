@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Chip Fault AI - Quick Deploy
echo ==========================================
echo.

REM Check Docker
echo [1/6] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not installed
    pause
    exit /b 1
)
echo [OK] Docker found
echo.

REM Check env file
echo [2/6] Checking configuration...
if not exist .env (
    if exist .env.docker.template (
        echo [!] Creating .env from template...
        copy .env.docker.template .env >nul
        echo [!] Please edit .env and set API key
        notepad .env
        pause
        exit /b 1
    )
)
echo [OK] Configuration found
echo.

REM Create directories
echo [3/6] Creating directories...
if not exist sql mkdir sql
if not exist sql\init.sql echo CREATE EXTENSION IF NOT EXISTS vector; > sql\init.sql
echo [OK] Directories ready
echo.

REM Pull images
echo [4/6] Pulling Docker images...
docker compose pull
echo [OK] Images pulled
echo.

REM Build images
echo [5/6] Building images...
docker compose build
echo [OK] Images built
echo.

REM Start services
echo [6/6] Starting services...
docker compose up -d
echo [OK] Services started
echo.

echo Waiting for services...
timeout /t 10 /nobreak >nul

echo.
echo ==========================================
echo   Deploy Complete!
echo ==========================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8889
echo.
echo Press any key to open browser...
pause >nul

start http://localhost:3000
