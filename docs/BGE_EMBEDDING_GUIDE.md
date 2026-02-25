# BGE Embedding 切换指南

## 已完成的改动

### 1. 配置更新 (`src/config/settings.py`)

```python
# 新增配置项
EMBEDDING_BACKEND = "bge"  # 可选: bge, openai
EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"  # BGE模型
EMBEDDING_DEVICE = "cpu"  # 设备: cpu, cuda, mps
EMBEDDING_DIMENSIONS = 1024  # 向量维度
```

### 2. BGE模型管理器 (`src/embedding/bge_manager.py`)

- 单例模式，自动缓存模型
- 避免重复加载
- 线程安全

### 3. LLMTool多后端支持 (`src/mcp/tools/llm_tool.py`)

- `generate_embedding()` 自动选择后端
- BGE: 本地计算，免费，快速
- OpenAI: API调用，付费，慢

### 4. 新增API端点

| 端点 | 说明 |
|------|------|
| `GET /api/v1/monitoring/embedding/status` | 查看embedding状态 |
| `POST /api/v1/monitoring/embedding/test?text=xxx` | 测试embedding生成 |

---

## 首次使用步骤

### 1. 安装依赖

```bash
pip install sentence-transformers torch
```

### 2. 初始化BGE模型（推荐）

```bash
python scripts/init_bge_model.py
```

首次运行会下载模型（约400MB），之后使用缓存。

### 3. 测试embedding

```bash
# 方式1：直接测试API
curl -X POST "http://localhost:8889/api/v1/monitoring/embedding/test?text=DDR错误"

# 方式2：查看状态
curl http://localhost:8889/api/v1/monitoring/embedding/status
```

### 4. 重启服务

```bash
# 重启后端
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8889 --reload
```

---

## 模型对比

| 模型 | 维度 | 中文性能 | 速度 | 成本 |
|------|------|---------|------|------|
| **BAAI/bge-large-zh-v1.5** | 1024 | ⭐⭐⭐⭐⭐ | 100ms | 免费 |
| BAAI/bge-base-zh-v1.5 | 768 | ⭐⭐⭐⭐ | 60ms | 免费 |
| OpenAI text-embedding-3-large | 3072 | ⭐⭐⭐ | 500ms | $0.13/M |
| OpenAI text-embedding-3-small | 1536 | ⭐⭐ | 300ms | $0.02/M |

---

## 切换后端

### 环境变量

```bash
# .env 文件
EMBEDDING_BACKEND=bge  # 或 openai
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_DEVICE=cpu  # 或 cuda (需要GPU)
```

### 运行时切换

```python
# src/config/settings.py 默认配置已改为BGE
# 如需切换回OpenAI，只需修改:
EMBEDDING_BACKEND = "openai"
```

---

## 常见问题

### Q: 首次调用很慢？
A: 首次需要下载模型（约400MB），之后会使用缓存。

### Q: 内存占用高？
A: 可以使用 `bge-base-zh-v1.5`（更小）或部署到GPU服务器。

### Q: 如何切换到GPU？
A: 设置 `EMBEDDING_DEVICE=cuda`，确保安装了CUDA版本的PyTorch。

### Q: 中文场景推荐哪个模型？
A: **BAAI/bge-large-zh-v1.5** 是中文场景最优选择。

---

## 监控告警

当embedding服务异常时，系统会自动发送告警：

| 场景 | 告警级别 | 处理方式 |
|------|---------|---------|
| BGE模型加载失败 | CRITICAL | 检查模型名称/网络 |
| OpenAI API失败 | CRITICAL | 检查API密钥/切换BGE |
| 首次下载模型 | INFO | 正常，等待完成 |

查看告警：
```bash
curl http://localhost:8889/api/v1/monitoring/alerts/recent
```
