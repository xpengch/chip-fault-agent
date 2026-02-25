@echo off
REM Register as Windows Service (requires admin)

echo ==========================================
echo   Register as Windows Service
echo ==========================================
echo.

REM Check admin rights
net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Administrator rights required
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Get current directory
set PROJECT_DIR=%CD%

REM Create start script
echo @echo off > start-service.bat
echo cd /d "%PROJECT_DIR%" >> start-service.bat
echo docker compose up -d >> start-service.bat

REM Create stop script
echo @echo off > stop-service.bat
echo cd /d "%PROJECT_DIR%" >> stop-service.bat
echo docker compose down >> stop-service.bat

REM Check for NSSM
where nssm >nul 2>&1
if errorlevel 1 (
    echo [INFO] NSSM not found, creating task scheduler instead
    
   REM Create task for startup
    schtasks /create /tn "ChipFaultAgent" /tr "%PROJECT_DIR%\start-service.bat" /sc onstart /ru SYSTEM /f
    echo [OK] Task scheduled for auto-start
) else (
    REM Register service
    echo [1/2] Registering service...
    nssm install ChipFaultAgent "%PROJECT_DIR%\start-service.bat"
    nssm set ChipFaultAgent AppDirectory "%PROJECT_DIR%"
    nssm set ChipFaultAgent DisplayName "Chip Fault AI Agent"
    nssm set ChipFaultAgent Description "AI-powered chip fault analysis system"
    nssm set ChipFaultAgent Start SERVICE_AUTO_START
    echo [OK] Service registered
)

echo.
echo [OK] Setup complete!
echo.
pause
