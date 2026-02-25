# 芯片失效分析AI Agent系统 - 离线部署指南

## 适用场景

- 内网环境（无法访问公网）
- 空气隔离网络
- 需要快速部署的生产环境

---

## 一、在有网络的机器上：准备部署包

### Windows 机器

```powershell
# 1. 打开PowerShell，进入项目目录
cd D:\chip-fault-agent

# 2. 运行导出脚本
.\export-offline.bat

# 3. 等待完成，生成的文件在 offline-package\ 目录
```

### Linux/Mac 机器

```bash
# 1. 进入项目目录
cd /path/to/chip-fault-agent

# 2. 运行导出脚本
chmod +x export-offline.sh
./export-offline.sh

# 3. 生成的文件在 offline-package/ 目录
```

---

## 二、部署包内容

```
offline-package/
├── docker-images/          # Docker镜像（约4GB）
│   ├── postgres.tar        # PostgreSQL镜像
│   ├── neo4j.tar          # Neo4j镜像
│   ├── redis.tar          # Redis镜像
│   └── python-base.tar    # Python基础镜像
├── python-packages/        # Python依赖包（约2GB）
│   ├── langgraph-*.whl
│   ├── torch-*.whl
│   └── ... (200+ 包)
├── src/                    # 源代码
├── frontend-v2/            # 前端代码
├── sql/                    # 数据库脚本
├── docker-compose.yml      # Docker编排文件
├── Dockerfile.backend      # 后端Dockerfile
├── .env.docker.template    # 环境变量模板
└── offline-import.bat      # 离线安装脚本
```

**总大小：约 6-8 GB**

---

## 三、在目标机器上：离线部署

### 1. 传输部署包

**方式A：移动存储**
```
复制 offline-package/ 到U盘/移动硬盘
```

**方式B：内网传输**
```powershell
# 在源机器
robocopy offline-package \target-machine\c$\chip-fault-agent /E

# 或使用压缩包
tar -czf offline-package.tar.gz offline-package/
scp offline-package.tar.gz user@target:/tmp/
```

### 2. 确保目标机器有Docker

**如果没有Docker，需要先安装：**

**Windows:**
1. 在有网络的机器下载Docker Desktop
   - 地址：https://www.docker.com/products/docker-desktop/
2. 复制安装包到目标机器
3. 运行安装

**Linux:**
```bash
# 离线安装Docker（需要预先下载deb/rpm包）
sudo dpkg -i docker-ce_*.deb
sudo systemctl start docker
```

### 3. 运行离线安装

**Windows:**
```powershell
cd C:\chip-fault-agent\offline-package
.\offline-import.bat
```

**Linux:**
```bash
cd /opt/chip-fault-agent/offline-package
chmod +x offline-import.sh
./offline-import.sh
```

---

## 四、验证部署

```bash
# 检查容器状态
docker compose ps

# 预期输出：
# NAME                    STATUS    PORTS
# chip-fault-backend      Up        0.0.0.0:8889->8889
# chip-fault-frontend     Up        0.0.0.0:3000->3000
# chip-fault-postgres     Up        0.0.0.0:5432
# chip-fault-neo4j        Up        0.0.0.0:7474-7687
# chip-fault-redis        Up        0.0.0.0:6379

# 检查后端健康
curl http://localhost:8889/api/v1/health

# 访问前端
浏览器打开: http://localhost:3000
```

---

## 五、常见问题

### Q1: 镜像加载失败
```bash
# 检查镜像文件完整性
md5sum docker-images/*.tar

# 单独加载失败的镜像
docker load -i docker-images/postgres.tar
```

### Q2: Python依赖安装失败
```bash
# 检查pip版本
pip --version

# 手动安装特定包
pip install --no-index --find-links=python-packages package-name
```

### Q3: 容器启动失败
```bash
# 查看详细日志
docker compose logs backend

# 常见原因：
# - 端口被占用
# - 内存不足
# - 磁盘空间不足
```

### Q4: BGE模型未下载
```
首次运行时会自动下载BGE模型（约1.3GB）
如需离线使用，需要额外准备模型文件
```

---

## 六、进阶：完全离线（包含BGE模型）

如果目标机器完全无法连接外网，需要额外准备BGE模型：

### 1. 下载BGE模型

**在有网络的机器上：**
```python
import os
from sentence_transformers import SentenceTransformer

# 设置模型缓存目录
os.environ['TRANSFORMERS_CACHE'] = './bge-model'

# 下载模型
model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

# 打包模型目录
# bge-model/ 目录包含所有模型文件
```

### 2. 添加到部署包

```bash
# 将模型目录添加到部署包
cp -r bge-model offline-package/

# 修改Dockerfile挂载模型
# 在 docker-compose.yml 中添加：
volumes:
  - ./bge-model:/root/.cache/huggingface
```

---

## 七、更新和维护

### 更新部署包

```powershell
# 在有网络的机器
git pull
.\export-offline.bat

# 将新的 offline-package/ 复制到目标机器
```

### 备份和恢复

```bash
# 备份数据
docker compose exec postgres pg_dump -U postgres chip_analysis > backup.sql

# 恢复数据
docker compose exec -T postgres psql -U postgres chip_analysis < backup.sql
```

---

## 八、系统要求

### Windows 目标机器

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows 10/11 | Windows 11 Pro |
| 内存 | 8GB | 16GB |
| 磁盘 | 20GB 可用 | 50GB SSD |
| CPU | 4核心 | 8核心 |

### Linux 目标机器

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 20.04+ | Ubuntu 22.04 LTS |
| 内存 | 8GB | 16GB |
| 磁盘 | 20GB 可用 | 50GB SSD |
| Docker | 20.10+ | 24.0+ |

---

## 九、文件校验

### 生成校验和

```powershell
# 在源机器生成
cd offline-package
certutil -hashfile SHA1 *
```

### 验证校验和

```powershell
# 在目标机器验证
cd offline-package
certutil -hashfile SHA1 * | compare-with-source-checksum.txt
```

---

## 十、技术支持

如遇问题，收集以下信息：

```bash
# 系统信息
docker version
docker compose version
python --version

# 容器状态
docker compose ps
docker compose logs --tail 100

# 网络检查
netstat -ano | findstr "3000 8889 5432"
```
