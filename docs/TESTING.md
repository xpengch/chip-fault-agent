# 芯片失效分析AI Agent系统 - 测试指南

## 测试前准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置以下关键项：
```

`.env` 文件中必须配置的项目：

```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chip_fault
NEO4J_URI=bolt://localhost:7687
REDIS_URL=redis://localhost:6379/0

# LLM API（可选，用于报告生成）
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# 分析配置
DEFAULT_CONFIDENCE_THRESHOLD=0.7
```

### 3. 启动数据库服务

```bash
# 使用Docker启动数据库
docker-compose up -d postgres redis neo4j

# 检查服务状态
docker-compose ps

# 查看日志（如有问题）
docker-compose logs -f postgres
docker-compose logs -f neo4j
```

### 4. 初始化数据库

```bash
# 运行初始化脚本
python scripts/init_db.py
```

初始化脚本会创建：
- 基础芯片型号（XC9000、XC8000、XC7000）
- 子系统类型（compute、memory、interconnect、io）
- 模块类型定义（cpu、l3_cache、ha、noc_router、ddr_controller、hbm_controller）
- 样本失效案例（4个示例案例）
- 基础推理规则

### 5. 启动服务

```bash
# 方式1：使用run.py脚本
python run.py all

# 方式2：分别启动（需要两个终端）
# 终端1 - API服务
python run.py api --port 8000

# 终端2 - 前端服务
python run.py frontend --frontend-port 8501
```

### 6. 访问服务

- API文档：http://localhost:8000/docs
- 前端界面：http://localhost:8501

---

## 测试用例

### 测试用例1：CPU核心错误

**日志内容：**
```
[ERROR] [CPU0] Core fault detected at 2024-01-15 10:23:45
[ERROR] Error Code: 0XCO001 - Core execution error
[INFO] Registers: 0x1A004000=0xDEADBEEF, 0x1A004004=0x12345678
[INFO] Affected modules: cpu
```

**预期结果：**
- 失效域：compute
- 失效模块：cpu
- 根因：CPU核心运算错误
- 置信度：>0.8

### 测试用例2：L3缓存一致性错误

**日志内容：**
```
[ERROR] Cache coherence violation at HA agent 5
[ERROR] Error Code: 0XLA001 - L3 cache coherence error
[INFO] HA State: MESI, Cache Line: 0x12345678
[INFO] Affected modules: l3_cache, ha
```

**预期结果：**
- 失效域：cache 或 interconnect
- 失效模块：l3_cache
- 根因：L3缓存一致性错误
- 置信度：>0.8

### 测试用例3：NoC路由冲突

**日志内容：**
```
[ERROR] NoC routing conflict detected
[ERROR] Error Code: 0XNC001 - Router congestion
[ERROR] Error Code: 0XHA001 - Home Agent timeout
[INFO] Router ID: 15, Conflict path: HA5 -> NoC15
[INFO] Affected modules: noc_router, ha
```

**预期结果：**
- 失效域：interconnect
- 失效模块：ha 或 noc_router
- 根因：NoC路由冲突 / Home Agent一致性错误
- 置信度：>0.75

### 测试用例4：DDR时序错误

**日志内容：**
```
[ERROR] DDR controller timing violation
[ERROR] Error Code: 0XME001 - Memory training failed
[INFO] Channel: 0, Frequency: 5600MHz
[INFO] Affected modules: ddr_controller
```

**预期结果：**
- 失效域：memory
- 失效模块：ddr_controller
- 根因：DDR控制器时序违例
- 置信度：>0.85

---

## API测试

### 使用curl测试

```bash
# 1. 健康检查
curl http://localhost:8000/api/v1/health

# 2. 提交分析（CPU错误）
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "chip_model": "XC9000",
    "raw_log": "[ERROR] Error Code: 0XCO001 - Core execution error\n[INFO] Affected modules: cpu",
    "infer_threshold": 0.7
  }'

# 3. 查询分析结果（使用返回的session_id）
curl http://localhost:8000/api/v1/analysis/session_20240115123456
```

### 使用Python测试

```python
import requests

# API基础URL
API_BASE = "http://localhost:8000/api/v1"

# 1. 健康检查
response = requests.get(f"{API_BASE}/health")
print(response.json())

# 2. 提交分析
analysis_request = {
    "chip_model": "XC9000",
    "raw_log": "[ERROR] Error Code: 0XCO001 - Core execution error\n[INFO] Affected modules: cpu",
    "infer_threshold": 0.7
}

response = requests.post(f"{API_BASE}/analyze", json=analysis_request)
result = response.json()

if result["success"]:
    session_id = result["data"]["session_id"]
    print(f"分析完成，Session ID: {session_id}")
    print(f"失效域: {result['data']['final_root_cause']['failure_domain']}")
    print(f"置信度: {result['data']['final_root_cause']['confidence']}")
else:
    print(f"分析失败: {result['error']}")
```

---

## 前端测试流程

1. **访问前端**: 打开浏览器访问 http://localhost:8501

2. **配置参数**（侧边栏）:
   - 选择芯片型号：XC9000
   - 设置推理阈值：0.7（默认）

3. **输入日志**:
   - 选择"直接粘贴文本"
   - 粘贴测试用例中的日志内容

4. **提交分析**:
   - 点击"🔍 开始分析"按钮
   - 等待分析完成（通常几秒）

5. **查看结果**:
   - 检查"基本信息"卡片
   - 检查"根因分析"部分
   - 查看"推理链路"详情
   - 检查是否需要专家介入

---

## 故障排查

### 数据库连接失败

```bash
# 检查PostgreSQL是否运行
docker-compose ps postgres

# 手动测试连接
psql postgresql://user:password@localhost:5432/chip_fault

# 查看日志
docker-compose logs postgres
```

### API启动失败

```bash
# 检查端口是否被占用
netstat -an | grep 8000

# 检查环境变量
cat .env | grep DATABASE_URL

# 查看详细日志
python run.py api --log-level debug
```

### 前端连接API失败

1. 检查API是否正常启动：访问 http://localhost:8000/api/v1/health
2. 检查前端侧边栏中的API地址配置
3. 查看浏览器控制台是否有错误信息

---

## 自动化测试脚本

运行 `tests/test_api.py` 进行自动化测试：

```bash
python tests/test_api.py
```

测试脚本会验证：
- ✅ 健康检查端点
- ✅ 分析提交端点
- ✅ 结果查询端点
- ✅ 多种故障类型的分析准确性
