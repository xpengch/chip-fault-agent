# ============================================
# 芯片失效分析AI Agent系统 - Windows一键部署脚本
# 适用于 Windows 11 + Docker Desktop
# ============================================

#requires -Version 5.1
#requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Print-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Print-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Print-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 检查Docker环境（支持 Docker Desktop 和 WSL2）
function Test-DockerEnv {
    Print-Info "检查Docker环境..."

    try {
        $null = docker --version
        $null = docker compose version

        # 检测 WSL2 后端
        $wsl = docker info --format '{{.OSType}}'
        if ($wsl -eq "wsl2") {
            Print-Info "Docker运行在WSL2后端"
        } else {
            Print-Info "Docker运行在Windows后端"
        }

        Print-Info "Docker环境检查通过"
    } catch {
        Print-Error "Docker未安装或Docker Compose不可用"
        Write-Host ""
        Write-Host "Windows 11 部署说明："
        Write-Host "1. 安装 Docker Desktop for Windows"
        Write-Host "   下载地址: https://www.docker.com/products/docker-desktop/"
        Write-Host ""
        Write-Host "2. 或启用 WSL2 并使用 Linux Docker"
        Write-Host "   运行: wsl --install"
        Write-Host "   然后使用 deploy.sh 脚本"
        Write-Host ""
        exit 1
    }
}

# 检查环境变量
function Test-EnvConfig {
    Print-Info "检查环境变量配置..."
    
    if (-not (Test-Path .env)) {
        if (Test-Path .env.docker.template) {
            Print-Warn ".env文件不存在，从模板创建..."
            Copy-Item .env.docker.template .env
            Print-Warn "请编辑.env文件，设置正确的API密钥"
            Print-Warn "完成后重新运行此脚本"
            exit 1
        } else {
            Print-Error ".env文件和模板都不存在"
            exit 1
        }
    }

    # 读取并检查ANTHROPIC_API_KEY
    $envContent = Get-Content .env | Where-Object { $_ -match "ANTHROPIC_API_KEY=" }
    if ($envContent -match "your_api_key_here") {
        Print-Error "请设置ANTHROPIC_API_KEY环境变量"
        exit 1
    }

    Print-Info "环境变量检查通过"
}

# 创建目录
function Initialize-Directories {
    Print-Info "创建必要的目录..."
    
    if (-not (Test-Path sql)) {
        New-Item -ItemType Directory -Path sql -Force | Out-Null
    }
    
    if (-not (Test-Path sql\init.sql)) {
        @"
-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;
"@ | Out-File -FilePath sql\init.sql -Encoding utf8
    }

    Print-Info "目录创建完成"
}

# 拉取镜像
function Get-DockerImages {
    Print-Info "拉取Docker镜像..."
    docker compose pull
    Print-Info "镜像拉取完成"
}

# 构建镜像
function Build-DockerImages {
    Print-Info "构建应用镜像..."
    docker compose build
    Print-Info "镜像构建完成"
}

# 启动服务
function Start-Services {
    Print-Info "启动服务..."
    docker compose up -d
    Print-Info "服务启动完成"
}

# 等待服务就绪
function Wait-ForServices {
    Print-Info "等待服务启动..."
    
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8889/api/v1/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Print-Info "后端服务已就绪"
                break
            }
        } catch {
            # 继续等待
        }
        
        $attempt++
        Start-Sleep -Seconds 2
    }

    if ($attempt -eq $maxAttempts) {
        Print-Error "后端服务启动超时"
        exit 1
    }

    Start-Sleep -Seconds 3
    Print-Info "所有服务已启动"
}

# 显示状态
function Show-Status {
    Print-Info "服务状态："
    docker compose ps
}

# 显示访问地址
function Show-Urls {
    Print-Info ""
    Print-Info "=========================================="
    Print-Info "  部署完成！系统已启动"
    Print-Info "=========================================="
    Print-Info ""
    Print-Info "  前端地址: http://localhost:3000"
    Print-Info "  后端API:  http://localhost:8889"
    Print-Info "  API文档:  http://localhost:8889/docs"
    Print-Info "  Neo4j:    http://localhost:7474"
    Print-Info ""
    Print-Info "  查看日志: docker compose logs -f"
    Print-Info "  停止服务: docker compose down"
    Print-Info "  重启服务: docker compose restart"
    Print-Info ""
}

# 主函数
function Main {
    Print-Info "=========================================="
    Print-Info "  芯片失效分析AI Agent系统 - 部署"
    Print-Info "=========================================="
    Print-Info ""

    Test-DockerEnv
    Test-EnvConfig
    Initialize-Directories
    Get-DockerImages
    Build-DockerImages
    Start-Services
    Wait-ForServices
    Show-Status
    Show-Urls
}

# 运行
Main
