# 芯片失效分析AI Agent系统 - Windows 11 部署指南

## 系统要求

- Windows 11 专业版/家庭版（64位）
- 至少 8GB RAM（推荐 16GB）
- 至少 20GB 可用磁盘空间
- 启用虚拟化（BIOS中开启 VT-x/AMD-V）

## 方案选择

### 方案A：Docker Desktop（推荐）

适合大多数用户，提供图形界面和易于管理。

### 方案B：WSL2 + Docker

适合开发者，提供更好的性能和Linux兼容性。

---

## 方案A：Docker Desktop 部署

### 步骤1：安装 Docker Desktop

1. **下载 Docker Desktop**
   - 访问：https://www.docker.com/products/docker-desktop/
   - 下载 Windows 版本

2. **安装**
   ```
   双击 Docker Desktop Installer.exe
   按照安装向导完成安装
   ```

3. **配置 Docker Desktop**
   - 打开 Docker Desktop
   - 进入 Settings → General
   - 确保以下选���已勾选：
     - ☑ Use the WSL 2 based engine
     - ☑ Open Docker Dashboard at startup

4. **资源配置**
   - Settings → Resources → Advanced
   - 设置内存：至少 4GB（推荐 8GB）
   - 设置磁盘：至少 50GB

### 步骤2：准备项目文件

1. **解压项目文件**
   ```
   将项目文件解压到: C:\chip-fault-agent\
   确保路径中没有中文和特殊字符
   ```

2. **配置环境变量**
   ```powershell
   cd C:\chip-fault-agent
   copy .env.docker.template .env
   notepad .env
   ```

3. **设置 API 密钥**
   编辑 `.env` 文件，设置：
   ```
   ANTHROPIC_API_KEY=你的API密钥
   ```

### 步骤3：一键部署

**方法1：使用 PowerShell 脚本**
```powershell
# 右键点击开始菜单，选择 "Windows PowerShell (管理员)"
cd C:\chip-fault-agent
.\deploy.ps1
```

**方法2：手动��行命令**
```powershell
# 拉取镜像
docker compose pull

# 构建镜像
docker compose build

# 启动服务
docker compose up -d

# 查看状态
docker compose ps
```

### 步骤4：验证部署

```powershell
# 检查后端健康
curl http://localhost:8889/api/v1/health

# 预期输出：
# {"status":"healthy","version":"1.0.0","timestamp":"..."}
```

---

## 方案B：WSL2 + Docker 部署

### 步骤1：启用 WSL2

1. **以管理员身份打开 PowerShell**
   ```powershell
   # 启用 WSL
   wsl --install

   # 重启计算机
   ```

2. **安装完成后，设置 Ubuntu**
   ```
   打开 Ubuntu
   设置用户名和密码
   ```

### 步骤2：在 WSL2 中安装 Docker

```bash
# 在 Ubuntu 终端执行
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动 Docker
sudo service docker start

# 添加用户到 docker 组
sudo usermod -aG docker $USER
```

### 步骤3：部署应用

```bash
# 进入项目目录（Windows路径挂载在 /mnt/c/）
cd /mnt/c/chip-fault-agent

# 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

---

## 常见问题

### Q1: Docker Desktop 无法启动
**解决方案:**
1. 确保 WSL2 已安装：`wsl --list --verbose`
2. 更新 WSL2：`wsl --update`
3. 重启 WSL：`wsl --shutdown`
4. 重新启动 Docker Desktop

### Q2: 端口被占用
**解决方案:**
```powershell
# 查看端口占用
netstat -ano | findstr "3000"
netstat -ano | findstr "8889"
netstat -ano | findstr "5432"

# 结束进程
taskkill /PID <进程ID> /F
```

### Q3: 镜像构建失败
**解决方案:**
```powershell
# 清理缓存
docker system prune -a

# 重新构建
docker compose build --no-cache
```

### Q4: BGE 模型下载慢
**解决方案:**
1. 使用国内镜像，在 `Dockerfile.backend` 添加：
   ```dockerfile
   ENV HF_ENDPOINT=https://hf-mirror.com
   ```
2. 或预下载模型后挂载到容器

### Q5: 中文显示乱码
**解决方案:**
```powershell
# 设置 PowerShell UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:LANG = "zh_CN.UTF-8"
```

---

## 防火墙配置

Windows 防火墙可能会阻止 Docker 通信，需要添加规则：

```powershell
# 以管理员身份运行 PowerShell
New-NetFirewallRule -DisplayName "Docker Backend" -Direction Inbound -LocalPort 8889 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Docker Frontend" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "PostgreSQL" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
```

---

## 启动脚本快捷方式

创建桌面快捷方式快速启动系统：

1. **创建启动脚本**
   ```powershell
   # 文件: start-chip-fault.ps1
   $projectPath = "C:\chip-fault-agent"
   cd $projectPath
   docker compose up -d
   Start-Process "http://localhost:3000"
   ```

2. **创建快捷方式**
   - 右键桌面 → 新建 → 快捷方式
   - 位置：`powershell.exe -ExecutionPolicy Bypass -File "C:\chip-fault-agent\start-chip-fault.ps1"`
   - 命名：芯片故障分析系统

---

## 访问地址

部署完成后，可通过以下地址访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3000 | 主界面 |
| 后端API | http://localhost:8889 | API服务 |
| API文档 | http://localhost:8889/docs | Swagger文档 |
| Neo4j控制台 | http://localhost:7474 | 图数据库管理 |

---

## 常用命令

```powershell
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend

# 查看服务状态
docker compose ps

# 进入容器
docker compose exec backend bash
docker compose exec postgres psql -U postgres

# 清理所有数据（谨慎）
docker compose down -v
```

---

## 性能优化

### 1. 启用 GPU 加速（如有 NVIDIA 显卡）

编辑 `docker-compose.yml`，在 backend 服务添加：
```yaml
services:
  backend:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 2. 增加内存

Docker Desktop → Settings → Resources → Memory
设置为 8GB 或更高

### 3. 使用 SSD

确保 Docker 数据目录在 SSD 上：
Docker Desktop → Settings → Resources → Disk image location

---

## 卸载

```powershell
# 停止并删除容器
docker compose down

# 删除所有数据
docker compose down -v

# 删除镜像
docker rmi (docker images 'chip-fault*' -q)

# 删除项目文件夹
Remove-Item -Recurse -Force C:\chip-fault-agent
```

---

## 技术支持

如遇到问题，请查看日志：
```powershell
docker compose logs -f > debug.log
```

并查看：
- Docker Desktop 日志：Troubleshoot → Diagnose & Export
- Windows 事件查看器：Windows 日志 → 应用程序
