#!/bin/bash
# ============================================
# 芯片失���分析AI Agent系统 - 一键部署脚本
# ============================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    print_info "检查Docker环境..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    print_info "Docker环境检查通过 ✓"
}

# 检查环境变量文件
check_env() {
    print_info "检查环境变量配置..."
    
    if [ ! -f .env ]; then
        if [ -f .env.docker.template ]; then
            print_warn ".env文件不存在，从模板创建..."
            cp .env.docker.template .env
            print_warn "请编辑.env文件，设置正确的API密钥"
            print_warn "完成后重新运行此脚本"
            exit 1
        else
            print_error ".env文件和模板都不存在"
            exit 1
        fi
    fi

    # 检查必需的环境变量
    source .env
    if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_api_key_here" ]; then
        print_error "请设置ANTHROPIC_API_KEY环境变量"
        exit 1
    fi

    print_info "环境变量检查通过 ✓"
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p sql
    mkdir -p logs
    
    # 创建初始化SQL文件
    if [ ! -f sql/init.sql ]; then
        cat > sql/init.sql << 'SQL'
-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建数据库
-- (数据库已在初始化时创建)
SQL
    fi

    print_info "目录创建完成 ✓"
}

# 拉取镜像
pull_images() {
    print_info "拉取Docker镜像..."
    docker compose pull
    print_info "镜像拉取完成 ✓"
}

# 构建镜像
build_images() {
    print_info "构建应用镜像..."
    docker compose build
    print_info "镜像构建完成 ✓"
}

# 启动服务
start_services() {
    print_info "启动服务..."
    docker compose up -d
    print_info "服务启动完成 ✓"
}

# 等待服务就绪
wait_for_services() {
    print_info "等待服务启动..."
    
    # 等待后端健康检查
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost:8889/api/v1/health > /dev/null 2>&1; then
            print_info "后端服务已就绪 ✓"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        print_error "后端服务启动超时"
        exit 1
    fi

    sleep 3
    print_info "所有服务已启动 ✓"
}

# 显示服务状态
show_status() {
    print_info "服务状态："
    docker compose ps
}

# 显示访问地址
show_urls() {
    print_info ""
    print_info "=========================================="
    print_info "  部署完成！系统已启动"
    print_info "=========================================="
    print_info ""
    print_info "  前端地址: http://localhost:3000"
    print_info "  后端API:  http://localhost:8889"
    print_info "  API文档:  http://localhost:8889/docs"
    print_info "  Neo4j:    http://localhost:7474"
    print_info ""
    print_info "  查看日志: docker compose logs -f"
    print_info "  停止服务: docker compose down"
    print_info "  重启服务: docker compose restart"
    print_info ""
}

# 主函数
main() {
    print_info "=========================================="
    print_info "  芯片失效分析AI Agent系统 - 部署"
    print_info "=========================================="
    print_info ""

    check_docker
    check_env
    create_directories
    pull_images
    build_images
    start_services
    wait_for_services
    show_status
    show_urls
}

# 运行主函数
main
