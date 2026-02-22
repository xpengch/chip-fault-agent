# 快速启动检查清单

## 前置条件检查

- [ ] Python 3.11+ 已安装
- [ ] 项目依赖已安装 (`pip install -r requirements.txt`)
- [ ] .env 文件已配置
- [ ] Docker Desktop 已安装（���果使用Docker方式）
- [ ] 或 PostgreSQL/Neo4j/Redis 已安装（本地方式）

## 启动步骤

### 方式一：使用Docker（推荐）

```bash
# 1. 复制环境变量
cp .env.example .env

# 2. 启动数据库服务
docker compose up -d postgres redis neo4j

# 3. 等待服务启动
docker compose ps

# 4. 初始化数据库
python scripts/init_db.py

# 5. 启动所有服务
python scripts/start_all.py
```

### 方式二：本地数据库

```bash
# 1. 确保数据库服务运行
# PostgreSQL: 服务已启动，端口5432可访问
# Neo4j: 服务已启动，端口7687可访问
# Redis: 服务已启动，端口6379可访问

# 2. 复制并编辑 .env
cp .env.example .env
# 修改数据库连接信息以匹配你的本地配置

# 3. 初始化数据库
python scripts/init_db.py

# 4. 启动API服务
python run.py api

# 5. 新终端启动前端
python run.py frontend
```

### 方式三：测试数据库连接

```bash
# 运行数据库连接测试
python scripts/test_db.py
```

## 服务地址

启动后可访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| API文档 | http://localhost:8000/docs | Swagger UI |
| API根路径 | http://localhost:8000/api/v1 | API endpoint |
| 前端界面 | http://localhost:8501 | Streamlit App |
| 健康检查 | http://localhost:8000/api/v1/health | 服务状态 |

## 验证步骤

### 1. 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

预期输出：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "..."
}
```

### 2. 测试分析端点

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "chip_model": "XC9000",
    "raw_log": "[ERROR] Error Code: 0XCO001\n[INFO] CPU fault",
    "infer_threshold": 0.7
  }'
```

### 3. 测试额外端点

```bash
# 获取支持的模块
curl http://localhost:8000/api/v1/modules

# 获取支持的芯片
curl http://localhost:8000/api/v1/chips

# 获取案例列表
curl http://localhost:8000/api/v1/cases

# 获取系统统计
curl http://localhost:8000/api/v1/stats

# 详细健康状态
curl http://localhost:8000/api/v1/health/detailed
```

### 4. 前端测试

1. 访问 http://localhost:8501
2. 在侧边栏选择芯片型号（XC9000）
3. 设置推理阈值（0.7）
4. 粘贴测试日志（见下方）
5. 点击"开始分析"
6. 查看分析结果

### 测试日志示例

**CPU错误：**
```
[ERROR] [CPU0] Core fault detected at 2024-01-15 10:23:45
[ERROR] Error Code: 0XCO001 - Core execution error
[INFO] Registers: 0x1A004000=0xDEADBEEF
[INFO] Affected modules: cpu
```

**缓存错误：**
```
[ERROR] Cache coherence violation at HA agent 5
[ERROR] Error Code: 0XLA001 - L3 cache coherence error
[INFO] HA State: MESI
[INFO] Affected modules: l3_cache, ha
```

**内存错误：**
```
[ERROR] DDR controller timing violation
[ERROR] Error Code: 0XME001 - Memory training failed
[INFO] Channel: 0, Frequency: 5600MHz
[INFO] Affected modules: ddr_controller
```

## 故障排查

### API无法启动

1. 检查端口占用：`netstat -an | grep 8000`
2. 检查配置文件：`cat .env`
3. 查看详细错误：`python run.py api --log-level debug`

### 前端无法连接API

1. 检查API是否启动：访问 http://localhost:8000/api/v1/health
2. 检查前端侧边栏API地址
3. 查看浏览器控制台错误信息

### 数据库连接失败

```bash
# 检查Docker服务
docker compose ps

# 查看PostgreSQL日志
docker compose logs postgres

# 查看Neo4j日志
docker compose logs neo4j

# 本地PostgreSQL测试
psql postgresql://postgres:postgres@localhost:5432/chip_analysis
```

## 开发命令速查

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 测试数据库连接
python scripts/test_db.py

# 启动API
python run.py api

# 启动前端
python run.py frontend

# 同时启动所有服务
python scripts/start_all.py

# 运行API测试
python tests/test_api.py

# 快速系统测试
python scripts/quick_test.py
```
