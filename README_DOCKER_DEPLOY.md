# 芯片失效分析AI Agent系统 - Docker部署指南

## 快速开始

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

### 一键部署

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows:**
```powershell
.\deploy.ps1
```

**手动部署:**
```bash
# 1. 配置环境变量
cp .env.docker.template .env
# 编辑 .env 文件，设置 ANTHROPIC_API_KEY

# 2. 启动服务
docker compose up -d

# 3. 查看状态
docker compose ps
```

## 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3000 | React前端 |
| 后端 | 8889 | FastAPI后端 |
| PostgreSQL | 5432 | 主数据库 |
| Neo4j | 7474, 7687 | 图数据库 |
| Redis | 6379 | 缓存 |

## 访问地址

- 前端: http://localhost:3000
- 后端: http://localhost:8889
- API文档: http://localhost:8889/docs
- Neo4j: http://localhost:7474

## 常用命令

```bash
docker compose up -d          # 启动
docker compose down           # 停止
docker compose restart        # 重启
docker compose logs -f        # 日志
docker compose ps             # 状态
```

## 环境变量

复制 `.env.docker.template` 为 `.env` 并配置：

```bash
ANTHROPIC_API_KEY=your_api_key_here
POSTGRES_PASSWORD=your_password
NEO4J_PASSWORD=your_password
REDIS_PASSWORD=your_password
```

## 数据持久化

- postgres_data: PostgreSQL数据
- neo4j_data: Neo4j数据
- redis_data: Redis数据
- bge_model_cache: BGE模型缓存

## 备份恢复

```bash
# 备份
docker compose exec postgres pg_dump -U postgres chip_analysis > backup.sql

# 恢复
docker compose exec -T postgres psql -U postgres chip_analysis < backup.sql
```
