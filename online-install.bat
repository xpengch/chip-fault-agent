@echo off
setlocal enabledelayedexpansion

chcp 65001 >nul 2>&1

echo ==========================================
echo   Chip Fault AI - 一键安装程序
echo ==========================================
echo.
echo 本程序将自动安装 Chip Fault AI 系统
echo 包括所有必需的环境和依赖
echo.

REM ============================================================
REM 第一阶段：环境检测与自动安装
REM ============================================================

echo.
echo ==========================================
echo   第一阶段：环境准备
echo ==========================================
echo.

REM --- 检查并安装 Python ---
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [未安装] Python 未安装
    echo.
    echo 正在下载 Python 安装程序...
    echo.

    REM 创建临时目录
    if not exist "%TEMP%\chip_fault_installer" mkdir "%TEMP%\chip_fault_installer"

    REM 下载 Python (使用 winget)
    echo 尝试使用 winget 安装 Python...
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements >nul 2>&1
    if errorlevel 1 (
        echo [失败] winget 安装失败，尝试手动下载...
        echo.
        echo 请手动下载并安装 Python 3.12:
        echo https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe
        echo.
        echo 安装时请勾选 "Add Python to PATH"
        pause
        exit /b 1
    )

    echo [成功] Python 已安装
    echo.
    echo 请重新运行此脚本以继续安装
    pause
    exit /b 0
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% 已安装
echo.

REM --- 检查并安装 Git ---
echo [2/4] 检查 Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [未安装] Git 未安装
    echo.
    echo 正在安装 Git...
    echo.

    winget install Git.Git --accept-package-agreements --accept-source-agreements >nul 2>&1
    if errorlevel 1 (
        echo [失败] winget 安装失败
        echo.
        echo 请手动下载并安装 Git:
        echo https://github.com/git-for-windows/git/releases/latest
        pause
        exit /b 1
    )

    echo [成功] Git 已安装
    echo.
    echo 请重新运行此脚本以继续安装
    pause
    exit /b 0
)

for /f "tokens=3" %%i in ('git --version') do set GIT_VERSION=%%i
echo [OK] Git %GIT_VERSION% 已安装
echo.

REM --- 检查并安装 Docker ---
echo [3/4] 检查 Docker Desktop...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [未安装] Docker Desktop 未安装
    echo.
    echo Docker Desktop 是运行本系统必需的
    echo.

    set /p INSTALL_DOCKER="是否自动安装 Docker Desktop? (Y/N): "
    if /i "!INSTALL_DOCKER!"=="Y" (
        echo.
        echo 正在下载 Docker Desktop...
        echo 这可能需要几分钟时间...
        echo.

        if not exist "%TEMP%\chip_fault_installer\DockerDesktopInstaller.exe" (
            echo 正在从网络下载...
            powershell -Command "Invoke-WebRequest -Uri 'https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe' -OutFile '%TEMP%\chip_fault_installer\DockerDesktopInstaller.exe'"
            if errorlevel 1 (
                echo [失败] 下载失败
                echo.
                echo 请手动下载 Docker Desktop:
                echo https://www.docker.com/products/docker-desktop
                pause
                exit /b 1
            )
        )

        echo 正在安装 Docker Desktop...
        echo 请按照安装向导完成安装
        echo.
        "%TEMP%\chip_fault_installer\DockerDesktopInstaller.exe"

        echo.
        echo ==========================================
        echo   Docker Desktop 安装完成
        echo ==========================================
        echo.
        echo 重要提示:
        echo   1. 请重启计算机
        echo   2. 启动 Docker Desktop
        echo   3. 等待 Docker 完全启动（托盘图标变绿）
        echo   4. 重新运行本脚本
        echo.
        pause
        exit /b 0
    ) else (
        echo.
        echo 请手动下载并安装 Docker Desktop:
        echo https://www.docker.com/products/docker-desktop
        pause
        exit /b 1
    )
)

for /f "tokens=3" %%i in ('docker --version') do set DOCKER_VERSION=%%i
echo [OK] Docker %DOCKER_VERSION% 已安装
echo.

REM --- 检查 Docker Compose ---
echo [4/4] 检查 Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [警告] Docker Compose 未找到
    echo         请确保 Docker Desktop 已完全启动
    pause
    exit /b 1
)

for /f "tokens=4" %%i in ('docker compose version') do set COMPOSE_VERSION=%%i
echo [OK] Docker Compose %COMPOSE_VERSION% 可用
echo.

echo ==========================================
echo   环境检查完成！所有依赖已就绪
echo ==========================================
echo.

REM ============================================================
REM 第二阶段：Docker 安装
REM ============================================================

echo.
echo ==========================================
echo   第二阶段：系统安装
echo ==========================================
echo.

REM 确定安装目录
echo 请选择安装目录:
echo   1. 当前目录
echo   2. 自定义目录
echo.
set /p DIR_CHOICE="选择 (1/2): "

if "!DIR_CHOICE!"=="2" (
    set /p CUSTOM_DIR="请输入完整路径 (例: D:\chip_fault_agent): "
    if not exist "!CUSTOM_DIR!" mkdir "!CUSTOM_DIR!"
    cd /d "!CUSTOM_DIR!"
)

echo.
echo 安装目录: %CD%
echo.

REM 克隆或更新仓库
if exist .git (
    echo [仓库] 检测到已存在的仓库
    set /p UPDATE_REPO="是否更新仓库? (Y/N): "
    if /i "!UPDATE_REPO!"=="Y" (
        echo [1/5] 更新仓库...
        git pull origin master
    ) else (
        echo [跳过] 保持现有版本
    )
) else (
    echo [1/5] 克隆仓库...
    git clone https://github.com/xpengch/chip-fault-agent.git temp_install
    xcopy temp_install\*.* /E /I /H /Y .
    rmdir /s /q temp_install
)

echo [OK] 仓库准备完成
echo.

REM 检查 BGE 模型
echo [2/5] 检查 BGE 模型...
if not exist bge-model (
    echo [提示] BGE 模型将在首次运行时自动下载 (~2.4GB)
    echo       如需预先下载，请运行: download-bge.py
) else (
    echo [OK] BGE 模型已存在
)
echo.

REM 配置环境变量
echo [3/5] 配置环境变量...
if not exist .env (
    if exist .env.docker.template (
        copy .env.docker.template .env >nul
        echo.
        echo ==========================================
        echo   配置 API Key
        echo ==========================================
        echo.
        echo 请设置您的 Anthropic API Key
        echo 这是运行本系统必需的
        echo.
        echo 获取方式: https://console.anthropic.com/
        echo.

        set /p API_KEY="请输入 API Key: "

        REM 更新 .env 文件
        powershell -Command "(Get-Content .env) -replace 'ANTHROPIC_API_KEY=.*', 'ANTHROPIC_API_KEY=%API_KEY%' | Set-Content .env"

        echo.
        echo [OK] API Key 已配置
        echo.
    ) else (
        echo [警告] .env.docker.template 不存在
        echo         创建基本配置文件...
        echo ANTHROPIC_API_KEY= > .env
        echo.
        echo [重要] 请编辑 .env 文件并设置 API Key
        notepad .env
        echo.
        set /p CONTINUE="配置完成后按 Enter 继续..."
    )
) else (
    echo [OK] .env 配置文件已存在
)
echo.

REM 构建 Docker 镜像
echo [4/5] 构建 Docker 镜像...
echo 这可能需要 5-10 分钟，请耐心等待...
echo.

docker compose build
if errorlevel 1 (
    echo [警告] 构建过程中出现警告
    echo         检查上方日志获取详情
)

echo [OK] Docker 镜像构建完成
echo.

REM 启动服务
echo [5/5] 启动服务...
docker compose up -d
if errorlevel 1 (
    echo [错误] 服务启动失败
    echo         请检查 Docker 是否正在运行
    pause
    exit /b 1
)

echo [OK] 所有服务已启动
echo.

REM 等待服务就绪
echo 等待服务启动中...
echo     * PostgreSQL (数据库 + 向量搜索)
echo     * Neo4j (知识图谱)
echo     * Redis (缓存)
echo     * Backend (API 服务)
echo     * Frontend (Web 界面)
echo.

REM 显示倒计时
for /l %%i in (30,-1,1) do (
    <nul set /p "=   等待 %%i 秒...^r"
    timeout /t 1 /nobreak >nul
)
echo.
echo.

REM 健康检查
echo 正在检查服务状态...
curl -s http://localhost:8889/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo [警告] 后端服务可能尚未完全就绪
    echo         请执行以下命令查看日志:
    echo           docker compose logs -f
    echo.
    echo 服务可能需要更长时间启动，请稍后访问
) else (
    echo [OK] 后端服务已就绪
)
echo.

REM ============================================================
REM 安装完成
REM ============================================================

echo ==========================================
echo   安装完成！
echo ==========================================
echo.
echo.
echo    访问地址:
echo.
echo      前端界面:  http://localhost:3000
echo      后端 API:  http://localhost:8889
echo      API 文档:  http://localhost:8889/docs
echo.
echo.
echo    默认管理员账户:
echo      用户名: admin
echo      密 码:   admin123
echo.
echo.
echo    常用命令:
echo      查看日志: docker compose logs -f
echo      停止服务: docker compose down
echo      重启服务: docker compose restart
echo      查看状态: docker compose ps
echo.
echo.
echo    文档:
echo      https://github.com/xpengch/chip-fault-agent
echo.
echo.

REM 可选：打开浏览器
set /p OPEN_BROWSER="是否在浏览器中打开系统? (Y/N): "
if /i "!OPEN_BROWSER!"=="Y" (
    echo 正在打开浏览器...
    start http://localhost:3000
)

echo.
echo 感谢使用 Chip Fault AI 系统！
echo.
pause
