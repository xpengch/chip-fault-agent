#!/bin/bash
# ============================================
# 导出离线部署包 (Linux/Mac版本)
# ============================================

set -e

GREEN='\033[0;32m'
NC='\033[0m'

PACKAGE_DIR="offline-package"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "  导出离线部署包"
echo "=========================================="
echo ""

echo "[1/5] 创建目录结构..."
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR/{docker-images,python-packages,scripts,data}
echo -e "${GREEN}[√]${NC} 目录创建完成"
echo ""

echo "[2/5] 导出Docker镜像..."
docker save pgvector/pgvector:0.5.0-pg16 -o $PACKAGE_DIR/docker-images/postgres.tar & PID=$!
echo -e "\e[A[K[-] PostgreSQL with pgvector"
wait $PID

docker save neo4j:5.24-community -o $PACKAGE_DIR/docker-images/neo4j.tar & PID=$!
echo -e "\e[A[K[-] Neo4j"
wait $PID

docker save redis:7-alpine -o $PACKAGE_DIR/docker-images/redis.tar & PID=$!
echo -e "\e[A[K[-] Redis"
wait $PID

docker save python:3.12-slim -o $PACKAGE_DIR/docker-images/python-base.tar & PID=$!
echo -e "\e[A[K[-] Python base"
wait $PID

echo -e "${GREEN}[√]${NC} Docker镜像导出完成"
echo ""

echo "[3/5] 下载Python依赖..."
mkdir -p python-temp
python3 -m venv python-temp/venv
source python-temp/venv/bin/activate
pip install --upgrade pip -q
pip download -r requirements.txt -d $PACKAGE_DIR/python-packages -q
rm -rf python-temp
echo -e "${GREEN}[√]${NC} Python依赖下载完成"
echo ""

echo "[4/5] 复制项目文件..."
cp docker-compose.yml $PACKAGE_DIR/
cp Dockerfile.backend $PACKAGE_DIR/
cp .env.docker.template $PACKAGE_DIR/
cp offline-import.sh $PACKAGE_DIR/scripts/
cp README_OFFLINE.md $PACKAGE_DIR/

cp -r src $PACKAGE_DIR/
cp -r frontend-v2 $PACKAGE_DIR/
cp -r sql $PACKAGE_DIR/ 2>/dev/null || mkdir -p $PACKAGE_DIR/sql

echo -e "${GREEN}[√]${NC} 项目文件复制完成"
echo ""

echo "[5/5] 打包部署包..."
PACKAGE_FILE="chip-fault-agent-offline-${TIMESTAMP}.tar.gz"
tar -czf $PACKAGE_FILE $PACKAGE_DIR
echo -e "${GREEN}[√]${NC} 部署包已打包: $PACKAGE_FILE"
echo ""

echo "=========================================="
echo "  导出完成！"
echo "=========================================="
echo ""
echo "部署包位置: $PACKAGE_DIR/"
echo "压缩包位置: $PACKAGE_FILE"
echo ""
echo "大小统计:"
du -sh $PACKAGE_DIR
echo ""
echo "下一步:"
echo "1. 将 $PACKAGE_FILE 复制到目标机器"
echo "2. 解压: tar -xzf $PACKAGE_FILE"
echo "3. 运行: cd $PACKAGE_DIR && bash scripts/offline-import.sh"
echo ""
