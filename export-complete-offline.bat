@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Chip Fault AI - Export Complete Offline Package
echo ==========================================
echo.

set PACKAGE_DIR=chip-fault-offline-package
set VERSION=1.0.0

echo [INFO] This will create a complete offline deployment package
echo.
pause

echo ==========================================
echo   Step 1/6: Clean and Create Directory
echo ==========================================
echo.

if exist %PACKAGE_DIR% rmdir /s /q %PACKAGE_DIR%
mkdir %PACKAGE_DIR%
mkdir %PACKAGE_DIR%\docker-images
mkdir %PACKAGE_DIR%\scripts
mkdir %PACKAGE_DIR%\config
mkdir %PACKAGE_DIR%\docs
mkdir %PACKAGE_DIR%\bge-model

echo [OK] Directory structure created
echo.

echo ==========================================
echo   Step 2/6: Pull and Build Docker Images
echo ==========================================
echo.
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

echo ==========================================
echo   Step 3/6: Copy BGE Model
echo ==========================================
echo.

if exist bge-model (
    echo     [-] Found BGE model, copying to package...
    xcopy /E /I /Y bge-model %PACKAGE_DIR%\bge-model >nul
    echo     [-] BGE model included
) else (
    echo     [WARNING] BGE model not found in bge-model directory
    echo     [INFO] The system will download on first run (~1.3GB)
    echo     [INFO] For true offline deployment, download BGE model separately
    echo.
    echo     To download BGE model:
    echo     1. Create bge-model directory
    echo     2. Run: python scripts/init_bge_model.py
    echo     3. Re-run this export script
)

echo [OK] BGE model check complete
echo.

echo ==========================================
echo   Step 4/6: Copy Project Files
echo ==========================================
echo.

echo     [-] Copying configuration files...
copy docker-compose.yml %PACKAGE_DIR%\ >nul
copy .env.docker.template %PACKAGE_DIR%\config\ >nul

echo     [-] Copying source code...
mkdir %PACKAGE_DIR%\src
xcopy /E /I /Y src %PACKAGE_DIR%\src >nul

echo     [-] Copying frontend files...
mkdir %PACKAGE_DIR%\frontend-v2
xcopy /E /I /Y frontend-v2\src %PACKAGE_DIR%\frontend-v2\src >nul
copy frontend-v2\package.json %PACKAGE_DIR%\frontend-v2\ >nul
copy frontend-v2\vite.config.js %PACKAGE_DIR%\frontend-v2\ >nul
if exist frontend-v2\index.html copy frontend-v2\index.html %PACKAGE_DIR%\frontend-v2\ >nul

echo     [-] Copying SQL initialization...
if exist sql xcopy /E /I /Y sql %PACKAGE_DIR%\sql >nul

echo     [-] Copying scripts...
if exist scripts xcopy /E /I /Y scripts %PACKAGE_DIR%\scripts >nul

echo [OK] Project files copied
echo.

echo ==========================================
echo   Step 5/6: Create Installation Scripts
echo ==========================================
echo.

echo     [-] Creating one-click install script...

(
echo @echo off
echo setlocal enabledelayedexpansion
echo.
echo echo ==========================================
echo echo   Chip Fault AI - Offline Installation
echo echo ==========================================
echo echo.
echo.
echo REM Check Docker
echo docker --version ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo [ERROR] Docker not installed or not running
echo     echo.
echo     echo Please start Docker Desktop first
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo [OK] Docker is ready
echo echo.
echo.
echo echo ==========================================
echo echo   Step 1: Load Docker Images
echo echo ==========================================
echo echo.
echo.
echo if exist docker-images\postgres.tar ^(
echo     echo     [1/5] Loading PostgreSQL...
echo     docker load -i docker-images\postgres.tar
echo     echo     [OK] PostgreSQL loaded
echo ^) else ^(
echo     echo     [Skip] postgres.tar not found
echo ^)
echo.
echo if exist docker-images\backend.tar ^(
echo     echo     [2/5] Loading Backend...
echo     docker load -i docker-images\backend.tar
echo     echo     [OK] Backend loaded
echo ^) else ^(
echo     echo     [Skip] backend.tar not found
echo ^)
echo.
echo if exist docker-images\frontend.tar ^(
echo     echo     [3/5] Loading Frontend...
echo     docker load -i docker-images\frontend.tar
echo     echo     [OK] Frontend loaded
echo ^) else ^(
echo     echo     [Skip] frontend.tar not found
echo ^)
echo.
echo if exist docker-images\neo4j.tar ^(
echo     echo     [4/5] Loading Neo4j...
echo     docker load -i docker-images\neo4j.tar
echo     echo     [OK] Neo4j loaded
echo ^) else ^(
echo     echo     [Skip] neo4j.tar not found
echo ^)
echo.
echo if exist docker-images\redis.tar ^(
echo     echo     [5/5] Loading Redis...
echo     docker load -i docker-images\redis.tar
echo     echo     [OK] Redis loaded
echo ^) else ^(
echo     echo     [Skip] redis.tar not found
echo ^)
echo.
echo echo ==========================================
echo echo   Step 2: Configure LLM API
echo echo ==========================================
echo echo.
echo echo.
echo if not exist .env ^(
echo     echo     [-] Creating .env from template...
echo     copy config\.env.docker.template .env ^>nul
echo     echo     [OK] .env created
echo     echo.
echo     echo     ==========================================
echo     echo     Select LLM Provider:
echo     echo     ==========================================
echo     echo.
echo     echo       [1] Anthropic Claude  - Cloud API (requires internet)
echo     echo       [2] OpenAI GPT-4      - Cloud API (requires internet)
echo     echo       [3] Local Qwen3       - Completely offline
echo     echo       [4] Skip              - Configure manually later
echo     echo.
echo     set /p CHOICE="Enter choice (1-4): "
echo     echo.
echo     if "%%CHOICE%"=="1" ^(
echo         echo     [Config] Anthropic Claude selected
echo     ^)
echo     if "%%CHOICE%"=="2" ^(
echo         echo     [Config] OpenAI selected
echo     ^)
echo     if "%%CHOICE%"=="3" ^(
echo         echo     [Config] Local Qwen3 selected - Completely offline mode
echo     ^)
echo     if "%%CHOICE%"=="4" ^(
echo         echo     [Skip] You can edit .env file manually later
echo     ^)
echo     echo.
echo     if "%%CHOICE%"=="1" ^(
echo         set /p API_KEY="Enter Anthropic API Key: "
echo     ^)
echo     if "%%CHOICE%"=="2" ^(
echo         set /p API_KEY="Enter OpenAI API Key: "
echo     ^)
echo     if "%%CHOICE%"=="3" ^(
echo         echo     [Info] Using default local Qwen3 configuration
echo         echo            API_BASE: http://localhost:8000/v1
echo             set API_KEY=sk-local
echo     ^)
echo     echo.
echo     echo     [-] Updating .env file...
echo     echo.
echo     if "%%CHOICE%"=="1" ^(
echo         echo # ============================================^> .env.new
echo         echo # LLM Configuration - Anthropic Claude^>^> .env.new
echo         echo # ============================================^>^> .env.new
echo         ANTHROPIC_API_KEY=%%API_KEY%%^>^> .env.new
echo         ANTHROPIC_BASE_URL=https://api.anthropic.com^>^> .env.new
echo         ANTHROPIC_MODEL=claude-3-opus-20240229^>^> .env.new
echo         echo. ^>^> .env.new
echo         echo # OpenAI (disabled)^>^> .env.new
echo         echo # OPENAI_API_KEY=^>^> .env.new
echo         echo # OPENAI_API_BASE=^>^> .env.new
echo         echo # OPENAI_MODEL=^>^> .env.new
echo         findstr /V /C:"ANTHROPIC_API_KEY=" /C:"OPENAI_API_KEY=" .env ^>^> .env.new
echo         move /Y .env.new .env ^>nul
echo     ^)
echo     if "%%CHOICE%"=="2" ^(
echo         echo # ============================================^> .env.new
echo         echo # LLM Configuration - OpenAI^>^> .env.new
echo         echo # ============================================^>^> .env.new
echo         echo # Anthropic (disabled)^>^> .env.new
echo         echo # ANTHROPIC_API_KEY=^>^> .env.new
echo         echo # ANTHROPIC_BASE_URL=^>^> .env.new
echo         echo # ANTHROPIC_MODEL=^>^> .env.new
echo         echo. ^>^> .env.new
echo         OPENAI_API_KEY=%%API_KEY%%^>^> .env.new
echo         OPENAI_API_BASE=https://api.openai.com/v1^>^> .env.new
echo         OPENAI_MODEL=gpt-4-turbo^>^> .env.new
echo         findstr /V /C:"ANTHROPIC_API_KEY=" /C:"OPENAI_API_KEY=" .env ^>^> .env.new
echo         move /Y .env.new .env ^>nul
echo     ^)
echo     if "%%CHOICE%"=="3" ^(
echo         echo # ============================================^> .env.new
echo         echo # LLM Configuration - Local Qwen3 (Completely Offline)^>^> .env.new
echo         echo # ============================================^>^> .env.new
echo         echo # Anthropic (disabled)^>^> .env.new
echo         echo # ANTHROPIC_API_KEY=^>^> .env.new
echo         echo # ANTHROPIC_BASE_URL=^>^> .env.new
echo         echo # ANTHROPIC_MODEL=^>^> .env.new
echo         echo. ^>^> .env.new
echo         OPENAI_API_KEY=%%API_KEY%%^>^> .env.new
echo         OPENAI_API_BASE=http://localhost:8000/v1^>^> .env.new
echo         OPENAI_MODEL=Qwen/Qwen2-7B-Instruct^>^> .env.new
echo         findstr /V /C:"ANTHROPIC_API_KEY=" /C:"OPENAI_API_KEY=" .env ^>^> .env.new
echo         move /Y .env.new .env ^>nul
echo     ^)
echo     if "%%CHOICE%"=="3" ^(
echo         echo     [OK] Configured for COMPLETELY OFFLINE mode
echo         echo     [INFO] Make sure local Qwen3 is running at http://localhost:8000
echo         echo            To start Qwen3: vllm serve Qwen/Qwen2-7B-Instruct --host 0.0.0.0 --port 8000
echo     ^)
echo     if "%%CHOICE%"=="1" ^(
echo         echo     [OK] Configured for Anthropic Claude
echo         echo     [INFO] Internet connection required for API calls
echo     ^)
echo     if "%%CHOICE%"=="2" ^(
echo         echo     [OK] Configured for OpenAI GPT-4
echo         echo     [INFO] Internet connection required for API calls
echo     ^)
echo     echo.
echo ^) else ^(
echo     echo     [OK] .env already exists, skipping configuration
echo     echo     [INFO] Edit .env manually if needed
echo ^)
echo.
echo echo ==========================================
echo echo   Step 3: Start Services
echo echo ==========================================
echo echo.
echo.
echo echo     [-] Starting databases...
echo docker compose up -d postgres neo4j redis
echo timeout /t 10 /nobreak ^>nul
echo.
echo echo     [-] Starting backend...
echo docker compose up -d backend
echo timeout /t 5 /nobreak ^>nul
echo.
echo echo     [-] Starting frontend...
echo docker compose up -d frontend
echo.
echo echo [OK] Services starting...
echo.
echo echo ==========================================
echo echo   Step 4: Wait for Ready
echo echo ==========================================
echo echo.
echo for /l %%%%i in ^(30,-1,1^) do ^(
echo     ^<nul set /p "=   Waiting %%%%i seconds...^r"
echo     ping 127.0.0.1 -n 2 ^>nul
echo ^)
echo echo.
echo.
echo curl -s http://localhost:8889/api/v1/health ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo     [Warning] Backend may still be starting
echo     echo              Check: docker compose logs backend
echo ^) else ^(
echo     echo     [OK] Backend is ready!
echo ^)
echo.
echo echo ==========================================
echo echo   Installation Complete!
echo echo ==========================================
echo echo.
echo echo Access URLs:
echo echo   Frontend:  http://localhost:3000
echo echo   Backend:   http://localhost:8889
echo echo   API Docs: http://localhost:8889/docs
echo echo.
echo echo Default Admin:
echo echo   Username: admin
echo echo   Password: admin123
echo echo.
echo echo Common Commands:
echo echo   docker compose logs -f      ^| View logs
echo echo   docker compose down         ^| Stop all
echo echo   docker compose restart      ^| Restart
echo echo.
echo pause
) > %PACKAGE_DIR%\install.bat

echo     [-] Creating quick start script...

(
echo @echo off
echo echo ==========================================
echo echo   Chip Fault AI - Quick Start
echo echo ==========================================
echo echo.
echo echo Starting all services...
echo docker compose up -d
echo echo.
echo echo Waiting for services to be ready...
echo timeout /t 30 /nobreak ^>nul
echo echo.
echo echo Services started!
echo echo.
echo echo Frontend:  http://localhost:3000
echo echo Backend:   http://localhost:8889
echo echo.
pause
) > %PACKAGE_DIR%\start.bat

echo     [-] Creating stop script...

(
echo @echo off
echo echo Stopping all services...
echo docker compose down
echo echo.
echo echo All services stopped.
pause
) > %PACKAGE_DIR%\stop.bat

echo     [-] Creating status check script...

(
echo @echo off
echo echo ==========================================
echo echo   System Status Check
echo echo ==========================================
echo echo.
echo echo Checking services...
echo docker compose ps
echo echo.
echo echo Backend health:
echo curl -s http://localhost:8889/api/v1/health
echo echo.
echo.
echo echo Log files:
echo echo   docker compose logs backend
echo echo   docker compose logs frontend
echo.
pause
) > %PACKAGE_DIR%\status.bat

echo [OK] Installation scripts created
echo.

echo ==========================================
echo   Step 6/6: Create Documentation
echo ==========================================
echo.

echo     [-] Creating README...

(
echo # Chip Fault AI - Offline Deployment Package
echo.
echo Version: %VERSION%
echo Date: %date% %time%
echo.
echo ## Contents
echo.
echo This package contains everything needed for offline deployment:
echo.
echo - **Docker Images**: Pre-built images for all services
echo - **BGE Model**: Chinese text embedding model (if included)
echo - **Source Code**: Complete application code
echo - **Configuration**: Environment templates
echo - **Scripts**: Installation and management scripts
echo.
echo ## Quick Start
echo.
echo 1. **Extract** this package to your target machine
echo.
echo 2. **Run the installer**:
echo    ```bash
echo    install.bat
echo    ```
echo.
echo 3. **Wait** for services to start (~30 seconds)
echo.
echo 4. **Access** the application:
echo    - Frontend: http://localhost:3000
echo    - Backend: http://localhost:8889
echo.
echo ## System Requirements
echo.
echo - **OS**: Windows 10/11 or Linux
echo - **Docker**: Docker Desktop 4.0+ with WSL 2
echo - **RAM**: 8GB+ recommended
echo - **Disk**: 10GB+ free space
echo.
echo ## Default Credentials
echo.
echo - **Username**: admin
echo - **Password**: admin123
echo.
echo ## Configuration
echo.
echo Edit `.env` file to configure:
echo.
echo - **LLM API**: Choose between Anthropic, OpenAI, or local Qwen3
echo.
echo ### Option 1: Anthropic Claude (Cloud)
echo ```bash
echo ANTHROPIC_API_KEY=your_api_key_here
echo ANTHROPIC_BASE_URL=https://api.anthropic.com
echo ANTHROPIC_MODEL=claude-3-opus-20240229
echo ```
echo.
echo ### Option 2: Local Qwen3 (Offline)
echo ```bash
echo OPENAI_API_KEY=your_api_key_here
echo OPENAI_API_BASE=http://localhost:8000/v1
echo OPENAI_MODEL=Qwen/Qwen2-7B-Instruct
echo ```
echo.
echo ## BGE Model
echo.
echo If `bge-model` folder is included, the system will use it directly.
echo Otherwise, the system will attempt to download on first run.
echo.
echo ## Management Scripts
echo.
echo - `install.bat` - Full installation (one-click)
echo - `start.bat` - Start all services
echo - `stop.bat` - Stop all services
echo - `status.bat` - Check system status
echo.
echo ## Troubleshooting
echo.
echo ### Backend not responding
echo ```bash
echo docker compose logs backend
echo ```
echo.
echo ### Port conflicts
echo Edit `docker-compose.yml` to change port mappings.
echo.
echo ### BGE model errors
echo Ensure `bge-model` folder exists or download it separately.
echo.
echo ## Support
echo.
echo - GitHub: https://github.com/xpengch/chip-fault-agent
echo - Issues: https://github.com/xpengch/chip-fault-agent/issues
) > %PACKAGE_DIR%\README.txt

echo     [-] Creating installation guide...

(
echo # Chip Fault AI - Offline Installation Guide
echo.
echo ## Prerequisites
echo.
echo ### Docker Installation
echo.
echo 1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
echo 2. Install and start Docker Desktop
echo 3. Wait for tray icon to turn green
echo.
echo ### WSL2 Setup (Windows)
echo.
echo If you need WSL2 offline installation:
echo.
echo 1. Download WSL2 kernel update from the offline package
echo 2. Run: wsl_update_x64.msi
echo 3. Restart computer if prompted
echo.
echo ## Installation Steps
echo.
echo ### Step 1: Extract Package
echo.
echo Extract the offline package to a location with at least 10GB free space.
echo.
echo ### Step 2: Run Installer
echo.
echo Double-click `install.bat` and follow the prompts.
echo.
echo ### Step 3: Configure API Key
echo.
echo The installer will open `.env` file. Configure your LLM API:
echo.
echo **For Cloud API (Anthropic/OpenAI)**:
echo - Set your API key
echo - Keep default base URL
echo.
echo **For Local Qwen3**:
echo - Set OPENAI_API_KEY (any value)
echo - Set OPENAI_API_BASE to your Qwen3 endpoint
echo - Set OPENAI_MODEL to your model name
echo.
echo ### Step 4: Start Services
echo.
echo The installer will automatically start all services.
echo.
echo ### Step 5: Access Application
echo.
echo - Frontend: http://localhost:3000
echo - Backend: http://localhost:8889
echo - Admin: admin / admin123
echo.
echo ## Manual Installation
echo.
echo If the automatic installer fails, you can install manually:
echo.
echo ### 1. Load Docker Images
echo.
echo ```bash
echo docker load -i docker-images/postgres.tar
echo docker load -i docker-images/backend.tar
echo docker load -i docker-images/frontend.tar
echo docker load -i docker-images/neo4j.tar
echo docker load -i docker-images/redis.tar
echo ```
echo.
echo ### 2. Create Configuration
echo.
echo ```bash
echo copy config\.env.docker.template .env
echo # Edit .env with your settings
echo ```
echo.
echo ### 3. Start Services
echo.
echo ```bash
echo docker compose up -d postgres neo4j redis
echo docker compose up -d backend
echo docker compose up -d frontend
echo ```
echo.
echo ## Verification
echo.
echo Check all services are running:
echo.
echo ```bash
echo docker compose ps
echo ```
echo.
echo Expected output:
echo - chip-fault-postgres: Up (healthy)
echo - chip-fault-neo4j: Up (healthy)
echo - chip-fault-redis: Up (healthy)
echo - chip-fault-backend: Up (healthy)
echo - chip-fault-frontend: Up (healthy)
echo.
echo ## Uninstallation
echo.
echo To remove all services:
echo.
echo ```bash
echo docker compose down
echo docker volume rm chip-fault-postgres_data chip-fault-neo4j_data chip-fault-redis_data
echo ```
echo.
echo ## Updates
echo.
echo To update the offline package:
echo.
echo 1. Get the new offline package
echo 2. Run `stop.bat`
echo 3. Replace files with new versions
echo 4. Run `install.bat` again
) > %PACKAGE_DIR%\docs\INSTALLATION_GUIDE.txt

echo [OK] Documentation created
echo.

echo ==========================================
echo   Package Export Complete!
echo ==========================================
echo.

echo Package location: %PACKAGE_DIR%\
echo.

echo Calculating package size...
for /f "delims=" %%a in ('dir /s /-c %PACKAGE_DIR%^| find "File(s)"') do set SIZE=%%a
set /a SIZE_MB=%SIZE:~/1024~/1024

echo Package size: ~%SIZE_MB% MB
echo.

echo Contents:
echo   - Docker Images: 5 files
echo   - Source Code: All application files
echo   - Scripts: install.bat, start.bat, stop.bat, status.bat
echo   - Config: .env.docker.template
echo   - Docs: README.txt, installation guide
echo   - BGE Model: Included if found
echo.

echo Next steps:
echo   1. Copy %PACKAGE_DIR%\ to target machine
echo   2. Run install.bat on target machine
echo   3. Configure API key in .env file
echo   4. Access at http://localhost:3000
echo.

echo Would you like to open the package folder now? (Y/N)
set /p OPEN_FOLDER=
if /i "!OPEN_FOLDER!"=="Y" explorer %PACKAGE_DIR%

pause
