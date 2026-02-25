# Windows 11 故障排查指南

## 问题诊断流程

```
问题发生
    ↓
Docker是否运行? → 否 → 启动Docker Desktop
    ↓ 是
端口是否冲突? → 是 → 修改端口/结束占用进程
    ↓ 否
配置是否正确? → 否 → 检查.env文件
    ↓ 是
镜像是否存在? → 否 → 重新构建
    ↓ 是
容器状态如何? → 异常 → 查看日志
    ↓ 正常
问题解决
```

---

## 常见问题

### 1. Docker相关问题

#### Docker Desktop无法启动
```
症状：双击Docker Desktop无反应或启动失败
```

**解决方案:**
```powershell
# 1. 重置WSL
wsl --shutdown
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Docker"
Remove-Item -Recurse -Force "$env:APPDATA\Docker"

# 2. 重新启动Docker Desktop

# 3. 如果仍失败，重置WSL2
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data
```

#### Docker命令无响应
```
症状：docker命令一直卡住
```

**解决方案:**
```powershell
# 重启Docker服务
Restart-Service Docker

# 或完全重启Docker Desktop
Stop-Process -Name "Docker Desktop" -Force
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### 2. 端口冲突问题

#### 检测端口占用
```powershell
# 检查所有服务端口
netstat -ano | findstr "3000 8889 5432 7687 6379"

# 检查单个端口
netstat -ano | findstr ":3000"
```

#### 结束占用进程
```powershell
# 查找进程ID
netstat -ano | findstr ":3000"
# 输出示例: TCP 0.0.0.0:3000 0.0.0.0:0 LISTENING 12345

# 结束进程
taskkill /PID 12345 /F
```

#### 修改端口配置
编辑 `docker-compose.yml`:
```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # 改用3001
```

### 3. 内存不足问题

#### 检测内存使用
```powershell
# 查看Docker资源使用
docker stats

# 查看系统内存
Get-ComputerMemory
```

#### 解决方案
```
1. 增加Docker内存限制:
   Docker Desktop → Settings → Resources → Memory
   设置为 8GB 或更高

2. 减少服务:
   docker-compose.yml中注释掉不需要的服务

3. 优化BGE模型:
   改用 bge-base (768维) 替代 bge-large (1024维)
```

### 4. 网络连接问题

#### 容器无法访问外网
```powershell
# 检查Docker网络
docker network ls
docker network inspect bridge

# 重置Docker网络
docker network prune
```

#### 代理设置
```
Docker Desktop → Settings → Resources → Proxies
启用手动代理配置
```

### 5. 中文乱码问题

#### PowerShell乱码
```powershell
# 设置UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001

# 或设置系统区域
# 设置 → 时间和语言 → 语言 → 管理语言设置
# 更改系统区域设置 → 勾选"Beta: 使用Unicode UTF-8"
```

#### 日志文件乱码
```powershell
# 使用UTF-8编码查看日志
Get-Content backend.log -Encoding UTF8
```

---

## 日志诊断

### 收集日志
```powershell
# 创建诊断脚本
@'
# 保存为 collect-logs.ps1
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$dir = "logs-$timestamp"
New-Item -ItemType Directory -Path $dir

# Docker日志
docker compose logs > "$dir\docker-compose.log"
docker compose logs backend > "$dir\backend.log"
docker compose logs postgres > "$dir\postgres.log"

# 系统信息
docker version > "$dir\docker-version.txt"
docker compose ps > "$dir\services.txt"
docker network inspect bridge > "$dir\network.json"

Write-Host "日志已收集到: $dir"
'@ | Out-File -FilePath collect-logs.ps1 -Encoding UTF8

# 运行收集
.\collect-logs.ps1
```

### 查看实时日志
```powershell
# 后端日志
docker compose logs -f backend

# 所有日志
docker compose logs -f

# 带时间戳
docker compose logs -f --tail 100
```

---

## 性能问题

### 容器响应慢
```
可能原因：
1. CPU资源不足
2. 磁盘I/O慢
3. 网络延迟
```

**诊断:**
```powershell
# 查看容器资源使用
docker stats

# 检查磁盘性能
WinSAT disk

# 检查网络延迟
Test-NetConnection -ComputerName localhost -Port 8889
```

### BGE模型加载慢
```
解决方案：
1. 预下载模型
2. 使用本地镜像
3. 启用模型缓存
```

```powershell
# 设置HF镜像加速
# 在 Dockerfile.backend 添加:
ENV HF_ENDPOINT=https://hf-mirror.com
```

---

## 数据问题

### 数据库连接失败
```powershell
# 检查PostgreSQL容器
docker compose ps postgres
docker compose logs postgres

# 进入数据库
docker compose exec postgres psql -U postgres -d chip_analysis

# 检查连接
\conninfo
```

### 数据恢复
```powershell
# 备份当前数据
docker compose exec postgres pg_dump -U postgres chip_analysis > backup.sql

# 恢复数据
docker compose exec -T postgres psql -U postgres chip_analysis < backup.sql
```

---

## 完全重置

### 重置所有Docker数据
```powershell
# 警告：这将删除所有数据！
docker compose down -v
docker system prune -a --volumes

# 重新开始
.\deploy.bat
```

### 完全卸载
```powershell
# 1. 停止并删除容器
docker compose down -v

# 2. 删除项目文件夹
Remove-Item -Recurse -Force C:\chip-fault-agent

# 3. 卸载Docker Desktop
# 控制面板 → 程序和功能 → Docker Desktop → 卸载

# 4. 删除Docker数据
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Docker"
Remove-Item -Recurse -Force "$env:APPDATA\Docker"

# 5. 删除WSL分发版
wsl --list --verbose
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data
```

---

## 获取帮助

### 系统信息收集
```powershell
# 运行此命令并将输出提供给技术支持
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, CsName, OsHardwareAbstractionLayer
docker version
docker compose version
docker compose ps
```

### 联系方式
- GitHub Issues: https://github.com/your-repo/issues
- Email: support@example.com
