# 芯片失效分析AI Agent系统 - 完整技术方案

> 版本：v2.0
> 更新日期：2026-02-24
> 部署方式：Docker容器化 + 离线部署支持

---

## 一、系统概述

### 1.1 系统简介

芯片失效分析AI Agent系统是一个基于2-Agent架构和MCP标准的自研SoC芯片失效分析平台，通过AI技术实现自动化、智能化的芯片故障诊断和根因分析。

### 1.2 核心特性

- **AI驱动分析**：基于大语言模型的智能推理
- **多源数据融合**：整合日志、知识图谱、历史案例
- **专家反馈学习**：持续优化分析准确性
- **向量相似度搜索**：基于pgvector的案例匹配
- **离线部署支持**：完整的Docker容器化方案

---

## 二、系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (React)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ 分析页面  │  │ 历史记录  │  │ 专家反馈  │  │ 系统监控  │     │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘     │
└────────┼────────────┼────────────┼────────────┼────────────┘
         │            │            │            │
         └────────────┴────────────┴────────────┴────────────┘
                               │
         ┌───────────────────────┴───────────────────────┐
         │              API层 (FastAPI)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ 分析接口  │  │ 多轮对话  │  │ 专家接口  │  │ 监控接口│ │
│  └─────┬────┘  └─���───┬────┘  └─────┬────┘  └───┬────┘ │
└────────┼────────────┼────────────┼────────────┼──────┘
         │            │            │            │
┌────────┴────────────┴────────────┴────────────┴──────┐
│                    Agent层 (LangGraph)                   │
│  ┌──────────────────────┐  ┌──────────────────────┐    │
│  │    Agent1 (推理)      │  │   Agent2 (知识)       │    │
│  │  - 特征提取          │  │  - 案例匹配          │    │
│  │  - 规则推理          │  │  - 专家交互          │    │
│  │  - LLM分析          │  │  - 知识学习          │    │
│  └──────────┬───────────┘  └──────────┬───────────┘    │
└─────────────┼──────────────────────────┼───────────────┘
              │                          │
┌─────────────┴──────────────┬─────────┴──────────────────┐
│         数据层              │                            │
│  ┌─────────┐  ┌─────────┐  │  ┌─────────┐  ┌─────────┐  │
│  │PostgreSQL│  │ Neo4j  │  │  │  Redis  │  │  BGE    │  │
│  │+pgvector │  │ 图数据库│  │  │  缓存   │  │  Embedding│  │
│  └─────────┘  └─────────┘  │  └─────────┘  └─────────┘  │
└────────────────────────────┴────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **前端** | React 18 + Vite | 现代化SPA框架 |
| **后端** | FastAPI + Python 3.12 | 高性能异步API |
| **AI引擎** | LangGraph + Anthropic/GLM | 多Agent编排 |
| **向量数据库** | PostgreSQL + pgvector | 相似度搜索 |
| **图数据库** | Neo4j 5.24 | 知识图谱 |
| **缓存** | Redis 7 | 会话缓存 |
| **Embedding** | BGE-large-zh-v1.5 | 本地中文向量 |
| **容器化** | Docker + Compose | 一键部署 |

---

## 三、核心功能模块

### 3.1 智能分析流程

```
1. 日志解析
   ↓
2. 特征提取 (Agent1)
   ↓
3. 多源推理 (规则 + LLM)
   ↓
4. 案例匹配 (pgvector)
   ↓
5. 知识图谱查询 (Neo4j)
   ↓
6. 综合分析报告
   ↓
7. 置信度评估
```

### 3.2 专家反馈机制

```
分析结果 → 专家审核 → 修正/确认 → Golden案例 → 知识学习
                ↓
            优先级排序 → 多轮对话优先使用
```

### 3.3 多轮对话

```
用户提问 → 上下文累积 → 检查专家修正 → 应用修正或重新分析
```

---

## 四、数据库设计

### 4.1 PostgreSQL (主数据库)

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `analysis_results` | 分析结果 | session_id, chip_model, root_cause |
| `failure_cases` | 失效案例 | embedding(1024维), is_verified |
| `expert_corrections` | 专家修正 | approval_status, is_applied |
| `analysis_messages` | 多轮对话 | session_id, sequence_number |
| `system_alerts` | 系统告警 | alert_type, severity |

### 4.2 Neo4j (知识图谱)

```
芯片模型 → [包含] → 模块
模块 → [易发生] → 失效域
失效域 → [症状] → 故障现象
失效域 → [解决方案] → 处理措施
案例 → [相似于] → 案例 (向量相似度)
```

### 4.3 Redis (缓存)

- 分析会话状态
- Embedding向量缓存
- 专家修正优先队列

---

## 五、关键技术实现

### 5.1 向量相似度搜索

使用pgvector扩展进行语义搜索：

```sql
-- 查询最相似的失效案例
SELECT failure_domain, module, root_cause,
       1 - (embedding <=> :query_vector) as similarity
FROM failure_cases
WHERE is_verified = true
ORDER BY embedding <=> :query_vector
LIMIT 5;
```

**向量配置**：
- 模型：BGE-large-zh-v1.5
- 维度：1024
- 距离算法：余弦距离（pgvector <=>）

### 5.2 BGE Embedding本地化

**优势**：
- 免费开源，无API调用成本
- 中文场景性能优于OpenAI
- 数据隐私保护

**实现**：
```python
class BGEModelManager:
    """单例模式，避免重复加载"""
    _instance = None

    def get_model(self, model_name, device):
        if self._model is None:
            self._model = SentenceTransformer(model_name, device=device)
        return self._model
```

### 5.3 多Agent编排

**Agent1 - 推理引擎**：
- 提取故障特征
- 执行规则推理
- LLM根因分析

**Agent2 - 知识引擎**：
- pgvector案例匹配
- Neo4j知识图谱查询
- 专家交互与学习

### 5.4 专家修正优先级

多轮对话中优先使用专家已批准的修正：

```python
# 检查是否有批准的修正
correction = await db.get_approved_correction(session_id)
if correction:
    await db.mark_correction_as_applied(correction_id)
    return correction.corrected_result
# 否则执行常规分析
```

---

## 六、部署方案

### 6.1 Docker容器化架构

```yaml
services:
  postgres:      # PostgreSQL + pgvector
  neo4j:         # 图数据库
  redis:         # 缓存服务
  backend:       # FastAPI后端
  frontend:      # React前端
```

### 6.2 离线部署支持

**部署包组成**：
- Docker镜像tar文件 (825MB)
- Python依赖包 (307MB)
- 完整源代码 (1.2MB)

**部署流程**：
1. 有网络机器：运行 `export-offline.bat` 生成部署包
2. 目标机器：运行 `offline-import.bat` 一键安装

### 6.3 环境要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows 10/11, Linux | Windows 11 Pro, Ubuntu 22.04 |
| 内存 | 8GB | 16GB |
| 磁盘 | 20GB | 50GB SSD |
| CPU | 4核 | 8核 |

---

## 七、与最初方案的差异对比

### 7.1 架构变更

| 方面 | 最初方案 | 当前方案 | 差异说明 |
|------|----------|----------|----------|
| **Embedding** | OpenAI API | BGE本地模型 | 降低成本，提升中文性能 |
| **向量数据库** | pgvector单独使用 | PostgreSQL+pgvector | 简化架构，降低维护 |
| **案例存储** | 独立golden案例库 | 合并到failure_cases | 统一管理，is_verified区分 |
| **专家修正** | 无优先级机制 | 多轮对话优先使用 | 提高响应效率 |
| **进度显示** | 简单状态 | 100ms平滑更新 | 改善用户体验 |
| **监控系统** | 无 | 完整告警系统 | 实时故障通知 |
| **fallback逻辑** | 有（hash降级） | 已移除 | 确保数据质量 |
| **部署方式** | 在线部署 | Docker+离线支持 | 支持内网环境 |

### 7.2 技术实现变更

**新增功能**：
1. ✅ **BGE Embedding本地化**
   - 新建 `src/embedding/bge_manager.py`
   - 单例模式模型缓存
   - 支持 CPU/CUDA/ MPS

2. ✅ **专家修正优先级**
   - `get_approved_correction()`
   - `mark_correction_as_applied()`
   - 多轮对话优先使用

3. ✅ **系统监控告警**
   - `src/monitoring/alerts.py`
   - 告警分级的SEVERITY级别
   - webhook和邮件通知

4. ✅ **Docker容器化**
   - `docker-compose.yml`
   - `Dockerfile.backend`
   - `Dockerfile.postgres` (自定义pgvector镜像)

5. ✅ **离线部署支持**
   - `export-offline.bat/sh`
   - `offline-import.bat/sh`
   - 完整部署包 (~1.1GB)

**移除功能**：
1. ❌ **Fallback embedding生成**
   - 移除hash向量降级逻辑
   - 确保向量数据质量

2. ❌ **独立golden案例库**
   - 合并到failure_cases表
   - 使用is_verified字段区分

### 7.3 代码结构调整

```
src/
├── agents/           # Agent实现
│   ├── agent1/       # 推理引擎
│   ├── agent2/       # 知识引擎
│   └── multi_turn_handler.py  # 多轮对话
├── api/              # API层
│   ├── monitoring_routes.py   # 监控接口 [新增]
│   └── ...
├── auth/             # 认证模块
├── config/           # 配置管理
│   └── settings.py   # 新增BGE配置
├── database/         # 数据库层
│   ├── models.py     # 新增SystemAlert模型
│   └── connection.py # 新增专家修正方法
├── embedding/        # Embedding模块 [新增]
│   └── bge_manager.py
├── mcp/              # MCP工具
│   └── tools/
│       └── llm_tool.py  # 多后端embedding
└── monitoring/       # 监控模块 [新增]
    └── alerts.py
```

### 7.4 配置变更

**.env 新增配置**：
```bash
# Embedding配置 [新增]
EMBEDDING_BACKEND=bge
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_DEVICE=cpu
EMBEDDING_DIMENSIONS=1024
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# 监控路径 [新增]
/api/v1/monitoring
```

### 7.5 性能对比

| 指标 | 最初方案 | 当前方案 | 改进 |
|------|----------|----------|------|
| **Embedding延迟** | ~2s (API) | ~0.5s (本地) | 75%↓ |
| **中文语义匹配** | 0.75 | 0.85 | 13%↑ |
| **API调用成本** | $0.02/1M tokens | $0 | 100%↓ |
| **专家修正响应** | 需重新分析 | 直接使用 | 显著↑ |
| **部署时间** | 数小时 | 10分钟 | 显著↓ |

---

## 八、运维指南

### 8.1 常用命令

```bash
# 启动系统
docker compose up -d

# 停止系统
docker compose down

# 查看日志
docker compose logs -f backend

# 重启服务
docker compose restart backend

# 进入数据库
docker compose exec postgres psql -U postgres -d chip_analysis

# 数据备份
docker compose exec postgres pg_dump -U postgres chip_analysis > backup.sql
```

### 8.2 监控指标

**API端点**：
- `GET /api/v1/health` - 健康检查
- `GET /api/v1/stats` - 统计数据
- `GET /api/v1/monitoring/embedding/status` - Embedding状态
- `GET /api/v1/monitoring/alerts/recent` - 最近告警

**关键指标**：
- 今日分析次数
- 成功率
- 专家干预次数
- 平均处理时长

### 8.3 故障排查

**问题1：BGE模型未加载**
```bash
curl http://localhost:8889/api/v1/monitoring/embedding/test?text=测试
```

**问题2：案例匹配失败**
- 检查pgvector扩展：`CREATE EXTENSION vector;`
- 检查embedding维度：1024

**问题3：专家修正未生效**
- 检查approval_status=approved
- 检查is_applied=false

---

## 九、安全与合规

### 9.1 认证授权

- JWT Token认证
- RBAC权限模型
- 审计日志记录

### 9.2 数据安全

- 敏感数据加密存储
- 数据传输HTTPS
- 定期备份机制

### 9.3 网络隔离

- 内网部署支持
- Docker网络隔离
- 防火墙配置

---

## 十、未来规划

### 10.1 短期目标

- [ ] 增强GPU支持
- [ ] 扩展知识图谱
- [ ] 优化LLM推理

### 10.2 中期目标

- [ ] 多芯片型号支持
- [ ] 自动化测试验证
- [ ] 模型持续学习

### 10.3 长期目标

- [ ] 联邦学习支持
- [ ] 边缘部署
- [ ] 行业知识库

---

## 附录

### A. 文档清单

| 文档 | 说明 |
|------|------|
| `README.md` | 项目说明 |
| `README_DOCKER_DEPLOY.md` | Docker部署 |
| `README_WINDOWS11.md` | Windows部署 |
| `README_OFFLINE.md` | 离线部署 |
| `TROUBLESHOOTING_WINDOWS.md` | 故障排查 |
| `BGE_EMBEDDING_GUIDE.md` | BGE使用指南 |

### B. 脚本清单

| 脚本 | 说明 |
|------|------|
| `deploy.bat` | Windows快速部署 |
| `export-offline.bat` | 导出离线包 |
| `offline-import.bat` | 离线安装 |
| `install-windows-service.bat` | 注册Windows服务 |
| `update.bat` | 系统更新 |

### C. 技术支持

- GitHub Issues
- 技术文档：`docs/`
- API文档：http://localhost:8889/docs

---

**文档版本**：v2.0
**最后更新**：2026-02-24
**维护团队**：芯片失效分析AI Agent系统开发组
