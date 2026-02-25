#!/bin/bash
# ============================================
# 离线部署导入脚本 (Linux版本)
# ============================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "  芯片失效分析AI Agent系统 - 离线部署"
echo "=========================================="
echo ""

# 检查Docker
print_info "检查Docker环境..."
if ! command -v docker &> /dev/null; then
    print_error "Docker未安装！"
    echo "请先安装Docker和Docker Compose"
    exit 1
fi
if ! command -v docker compose &> /dev/null; then
    print_error "Docker Compose未安装！"
    exit 1
fi
print_info "Docker环境正常"
echo ""

# 加载Docker镜像
print_info "加载Docker镜像..."
for img in docker-images/*.tar; do
    if [ -f "$img" ]; then
        name=$(basename "$img" .tar)
        echo "  [-] $name"
        docker load -i "$img" > /dev/null 2>&1
    fi
done
print_info "Docker镜像加载完成"
echo ""

# 创建Python虚拟环境
print_info "创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
print_info "虚拟环境创建完成"
echo ""

# 安装Python依赖
print_info "安装Python依赖..."
pip install --no-index --find-links=python-packages -r requirements.txt
print_info "Python依赖安装完成"
echo ""

# 配置环境
print_info "配置环境..."
if [ ! -f ".env" ]; then
    if [ -f ".env.docker.template" ]; then
        cp .env.docker.template .env
        print_warn "请编辑.env文件，设置ANTHROPIC_API_KEY"
        read -p "编辑完成后按回车继续..."
    fi
fi
print_info "环境配置完成"
echo ""

# 初始化数据库
print_info "初始化数据库..."
mkdir -p sql
if [ ! -f "sql/init.sql" ]; then
    cat > sql/init.sql << 'SQL'
-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;
SQL
fi
print_info "数据库初始化完成"
echo ""

# 启动服务
print_info "启动服务..."
docker compose up -d
print_info "服务启动完成"
echo ""

# 等待服务就绪
print_info "等待服务启动..."
sleep 30

# 检查服务状态
if curl -sf http://localhost:8889/api/v1/health > /dev/null 2>&1; then
    print_info "后端服务就绪"
else
    print_warn "后端服务可能未完全启动，请运行: docker compose logs"
fi
echo ""

echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8889"
echo "  文档: http://localhost:8889/docs"
