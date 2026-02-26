# 芯片失效分析AI Agent系统 - 完整离线部署指南

## 📦 一键离线部署包

本指南帮助您创建一个完整的离线部署包，包含所有必要组件，可在无网络环境下一键部署。

---

## 📋 系统要求

### 目标机器配置

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows 10/11 或 Ubuntu 20.04+ | Windows 11 Pro / Ubuntu 22.04 LTS |
| 内存 | 8GB RAM | 16GB RAM |
| 磁盘 | 20GB 可用空间 | 50GB SSD |
| CPU | 4核心 | 8核心 |
| Docker | Docker Desktop 4.0+ | Docker Desktop 4.20+ |

### Docker 安装

**Windows:**
1. 下载 Docker Desktop: https://www.docker.com/products/docker-desktop
2. 运行安装程序
3. 启动 Docker Desktop，等待托盘图标变绿

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl start docker
```

---

## 🚀 方法一：使用完整导出脚本（推荐）

### 步骤 1：在有网络的机器上导出

```powershell
# 进入项目目录
cd D:\chip-fault-agent

# 运行完整导出脚本
.\export-complete-offline.bat
```

**脚本会自动：**
1. ✅ 拉取并构建所有 Docker 镜像（~15分钟）
2. ✅ 导出 5 个 Docker 镜像文件
3. ✅ 复制完整源代码
4. ✅ 包含 BGE 模型（如果存在）
5. ✅ 生成一键安装脚本
6. ✅ 创建文档和配置模板

**导出内容：**
```
chip-fault-offline-package/
├── docker-images/              # 预构建镜像（~6GB）
│   ├── postgres.tar            # PostgreSQL + pgvector
│   ├── backend.tar             # 后端服务
│   ├── frontend.tar            # 前端服务
│   ├── neo4j.tar               # 图数据库
│   └── redis.tar               # 缓存
├── src/                        # 完整源代码
├── frontend-v2/                # 前端源代码
├── bge-model/                  # BGE 模型（可选）
├── scripts/                    # 工具脚本
├── config/                     # 配置文件
│   └── .env.docker.template
├── install.bat                 # 一键安装脚本 ⭐
├── start.bat                   # 启动脚本
├── stop.bat                    # 停止脚本
├── status.bat                  # 状态检查脚本
├── docker-compose.yml          # Docker 编排文件
├── README.txt                  # 使用说明
└── docs/                       # 详细文档
    └── INSTALLATION_GUIDE.txt
```

**总大小：约 8-10 GB**（取决于是否包含 BGE 模型）

---

### 步骤 2：传输到离线环境

**方式 A：移动存储**
```
复制整个 chip-fault-offline-package/ 到 U 盘/移动硬盘
```

**方式 B：内网传输**
```powershell
# Windows 之间
robocopy chip-fault-offline-package \\target-machine\c$\ /E

# 或压缩后传输
tar -czf chip-fault-offline.tar.gz chip-fault-offline-package/
```

---

### 步骤 3：在离线机器上安装

```powershell
# 1. 进入部署包目录
cd chip-fault-offline-package

# 2. 运行一键安装脚本
install.bat
```

**安装脚本会自动：**
1. ✅ 加载所有 Docker 镜像
2. ✅ 创建配置文件 (.env)
3. ✅ 打开编辑器配置 API 密钥
4. ✅ 启动所有服务
5. ✅ 等待服务就绪
6. ✅ 显示访问地址

---

### 步骤 4：配置 API 密钥

安装脚本会自动打开 `.env` 文件，根据您的需求配置：

**选项 A：Anthropic Claude（云端）**
```bash
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=claude-3-opus-20240229
```

**选项 B：本地 Qwen3（完全离线）**
```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=http://localhost:8000/v1
OPENAI_MODEL=Qwen/Qwen2-7B-Instruct
```

---

### 步骤 5：访问应用

安装完成后，访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | Web 界面 |
| 后端 | http://localhost:8889 | API 服务 |
| API 文档 | http://localhost:8889/docs | Swagger 文档 |

**默认管理员账号：**
- 用户名：`admin`
- 密码：`admin123`

---

## 🔧 方法二：手动导出（高级用户）

### 1. 导出 Docker 镜像

```powershell
# 拉取基础镜像
docker pull postgres:16
docker pull node:20-alpine
docker pull nginx:alpine
docker pull python:3.12-slim
docker pull neo4j:5.24-community
docker pull redis:7-alpine

# 构建自定义镜像
docker compose build postgres
docker compose build backend
docker compose build frontend

# 导出镜像
docker save chip-fault-postgres:latest -o postgres.tar
docker save chip-fault-backend:latest -o backend.tar
docker save chip-fault-frontend:latest -o frontend.tar
docker save neo4j:5.24-community -o neo4j.tar
docker save redis:7-alpine -o redis.tar
```

### 2. 准备 BGE 模型（可选）

```python
# 在有网络的机器上
import os
from sentence_transformers import SentenceTransformer

os.environ['TRANSFORMERS_CACHE'] = './bge-model'
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

# bge-model/ 目录包含所有模型文件
# 将此目录复制到离线环境
```

### 3. 复制项目文件

```powershell
# 创建部署包目录
mkdir chip-fault-offline-package
cd chip-fault-offline-package

# 复制必要文件
mkdir docker-images
move *.tar docker-images\

mkdir src
xcopy /E /I ..\src src\

mkdir frontend-v2
xcopy /E /I ..\frontend-v2 frontend-v2\

copy ..\docker-compose.yml .
copy ..\.env.docker.template config\
```

---

## ✅ 验证部署

### 检查服务状态

```powershell
# 查看所有容器
docker compose ps

# 预期输出：
# NAME                    STATUS    PORTS
# chip-fault-postgres     Up (healthy)   0.0.0.0:5432->5432/tcp
# chip-fault-neo4j        Up (healthy)   7474->7474/tcp, 7687->7687/tcp
# chip-fault-redis        Up (healthy)   6379->6379/tcp
# chip-fault-backend      Up (healthy)   0.0.0.0:8889->8889/tcp
# chip-fault-frontend     Up            3000->3000/tcp
```

### 健康检查

```powershell
# 后端健康检查
curl http://localhost:8889/api/v1/health

# 预期响应：
# {"status":"healthy","version":"1.0.0"}
```

### 测试分析功能

1. 打开浏览器访问 http://localhost:3000
2. 使用 admin/admin123 登录
3. 上传芯片日志进行分析
4. 查看 AI 分析结果

---

## 🛠️ 日常管理

### 启动服务

```powershell
start.bat
# 或
docker compose up -d
```

### 停止服务

```powershell
stop.bat
# 或
docker compose down
```

### 查看状态

```powershell
status.bat
# 或
docker compose ps
```

### 查看日志

```powershell
# 所有服务日志
docker compose logs -f

# 特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 重启服务

```powershell
docker compose restart backend
docker compose restart frontend
```

---

## 📊 完全离线（包含 BGE 模型）

### 下载 BGE 模型

**在有网络的机器上：**

运行 BGE 模型下载脚本：
```powershell
python scripts/init_bge_model.py
```

或使用 Python 代码：
```python
import os
from sentence_transformers import SentenceTransformer

os.environ['TRANSFORMERS_CACHE'] = './bge-model'
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
```

### 添加到部署包

```powershell
# 将 bge-model 文件夹复制到部署包
xcopy /E /I bge-model chip-fault-offline-package\bge-model\
```

### 验证模型使用

部署后，检查日志确认 BGE 模型已加载：
```
[BgeManager] BGE model loaded from /app/models
```

---

## 🔄 更新部署包

### 在有网络的机器上

```powershell
# 1. 拉取最新代码
git pull origin master

# 2. 重新导出
.\export-complete-offline.bat

# 3. 传输到离线环境
```

### 在离线机器上

```powershell
# 1. 停止服务
stop.bat

# 2. 替换文件（保留数据）
# 复制新版本的 src/, frontend-v2/, docker-compose.yml 等

# 3. 重新启动
install.bat
```

---

## 🐛 故障排除

### 问题 1：镜像加载失败

```powershell
# 检查镜像文件
dir docker-images\

# 手动加载
docker load -i docker-images\postgres.tar
docker load -i docker-images\backend.tar
docker load -i docker-images\frontend.tar
docker load -i docker-images\neo4j.tar
docker load -i docker-images\redis.tar
```

### 问题 2：端口冲突

编辑 `docker-compose.yml`，修改端口映射：
```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # 修改为其他端口
```

### 问题 3：内存不足

```powershell
# 增加 Docker 内存限制
# Docker Desktop → Settings → Resources → Memory
# 设置为 8GB+
```

### 问题 4：BGE 模型错误

```powershell
# 检查 bge-model 文件夹
dir bge-model\

# 确认模型文件存在
# 应包含：config.json, model.safetensors, tokenizer.json 等
```

### 问题 5：后端无法启动

```powershell
# 查看详细日志
docker compose logs backend

# 常见原因：
# - .env 配置错误
# - 数据库连接失败
# - API 密钥无效
```

---

## 📦 部署包目录结构详解

```
chip-fault-offline-package/
│
├── 📁 docker-images/              # Docker 镜像（必须）
│   ├── postgres.tar               # PostgreSQL + pgvector
│   ├── backend.tar                # 后端服务（已构建）
│   ├── frontend.tar               # 前端服务（已构建）
│   ├── neo4j.tar                  # Neo4j 图数据库
│   └── redis.tar                  # Redis 缓存
│
├── 📁 src/                        # 后端源代码（必须）
│   ├── agents/                    # Agent 实现
│   ├── api/                       # FastAPI 路由
│   ├── config/                    # 配置管理
│   ├── database/                  # 数据库模型
│   ├── mcp/                       # MCP 工具层
│   └── context/                   # 上下文管理
│
├── 📁 frontend-v2/                # 前端源代码（必须）
│   ├── src/                       # React 组件
│   ├── package.json               # npm 依赖
│   └── vite.config.js             # Vite 配置
│
├── 📁 bge-model/                  # BGE 模型（可选，推荐）
│   ├── config.json                # 模型配置
│   ├── model.safetensors          # 模型权重
│   ├── tokenizer.json             # 分词器
│   └── vocab.txt                  # 词汇表
│
├── 📁 config/                     # 配置文件（必须）
│   └── .env.docker.template       # 环境变量模板
│
├── 📁 scripts/                    # 工具脚本（可选）
│   └── init_bge_model.py          # BGE 模型下载
│
├── 📄 docker-compose.yml          # Docker 编排（必须）
│
├── 📄 install.bat                 # 一键安装 ⭐
├── 📄 start.bat                   # 快速启动
├── 📄 stop.bat                    # 快速停止
├── 📄 status.bat                  # 状态检查
│
├── 📄 README.txt                  # 快速指南
└── 📁 docs/                       # 详细文档
    ├── INSTALLATION_GUIDE.txt
    └── TROUBLESHOOTING.txt
```

---

## 🎯 快速检查清单

部署前确认：

- [ ] Docker Desktop 已安装并运行
- [ ] 有至少 20GB 可用磁盘空间
- [ ] 有至少 8GB RAM
- [ ] 已复制完整部署包到目标机器

部署后验证：

- [ ] 所有容器状态为 Up
- [ ] 前端可访问 (http://localhost:3000)
- [ ] 后端健康检查通过
- [ ] 可以登录 (admin/admin123)
- [ ] 可以上传并分析日志
- [ ] BGE 模型已加载（如适用）

---

## 📞 技术支持

如遇问题，请提供以下信息：

1. **系统信息**
   ```powershell
   docker version
   docker compose version
   ```

2. **容器状态**
   ```powershell
   docker compose ps
   ```

3. **错误日志**
   ```powershell
   docker compose logs backend
   docker compose logs frontend
   ```

4. **网络检查**
   ```powershell
   netstat -ano | findstr "3000"
   netstat -ano | findstr "8889"
   ```

**获取帮助：**
- GitHub Issues: https://github.com/xpengch/chip-fault-agent/issues
- 文档: https://github.com/xpengch/chip-fault-agent/wiki
