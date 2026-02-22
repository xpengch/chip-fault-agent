# 芯片失效分析AI Agent系统

基于自研SoC芯片的AI驱��失效分析系统，支持多模块故障定位、根因推理和知识闭环。

## 系统架构

- **2-Agent方案**: Agent1（推理核心） + Agent2（专家交互与知识循环）
- **MCP标准能力层**: 统一的工具调用接口
- **RBAC权限控制**: 基于角色的访问控制与JWT认证
- **混合数据存储**: PostgreSQL + pgvector + Neo4j + Redis
- **支持模块**: CPU、L3缓存、HA（一致性代理）、NoC、DDR、HBM

## 系统特性

### Phase 1 - 核心功能 ✅
- 多源推理（知识图谱、案例匹配、规则库）
- 日志解析与特征提取
- 智能报告生成
- LangGraph工作流编排
- FastAPI后端 + Streamlit前端

### Phase 2 - 扩展功能 ✅
- **RBAC权限系统**: 用户、角色、权限三层权限控制
- **JWT认证**: 访问令牌 + 刷新令牌机制
- **Agent2专家交互**: 智能专家分配与工作负载管理
- **知识循环学习**: 从专家修正中学习，更新案例和规则
- **审计日志**: 完整的操作审计追踪
- **专家修正流程**: 提交、审批、拒绝的知识闭环

## 项目结构

```
chip_fault_agent/
├── src/
│   ├── agents/           # Agent实现
│   │   ├── agent1/      # Agent1推理核心
│   │   ├── agent2/      # Agent2专家交互与知识循环
│   │   └── workflow.py   # LangGraph工作流编排
│   ├── mcp/              # MCP工具集
│   │   ├── tools/        # 工具实现
│   │   └── server.py     # MCP服务器
│   ├── database/         # 数据库模型和Repository
│   │   ├── models.py     # 核心数据模型
│   │   ├── rbac_models.py # RBAC权限模型
│   │   └── connection.py # 数据库连接管理
│   ├── auth/             # 认证与授权
│   │   ├── service.py    # 认证服务
│   │   ├── decorators.py # 认证装饰器
│   │   ├── dependencies.py # FastAPI依赖注入
│   │   └── middleware.py # 认证中间件
│   ├── api/              # FastAPI接口
│   │   ├── app.py        # FastAPI主应用
│   │   ├── analyze_routes.py # 分析相关路由
│   │   ├── auth_routes.py # 认证相关路由
│   │   ├── admin_routes.py # 管理员路由
│   │   └── expert_routes.py # 专家修正路由
│   ├── config/           # 配置管理
│   └── utils/            # 工具函数
├── frontend/            # Streamlit前端
│   └── app.py          # Streamlit主应用
├── data/                # 数据目录
│   ├── logs/
│   ├── uploads/
│   └── reports/
├── templates/           # HTML报告模板
├── tests/               # 测试代码
├── docs/                # 文档
├── scripts/            # 启动和初始化脚本
├── docker-compose.yml    # Docker编排
├── Dockerfile          # 容器构建
├── run.py             # 启动脚本
└── requirements.txt     # Python依赖
```

## 快速开始

### 1. 环境要求

- Python 3.11+
- PostgreSQL 15+ (with pgvector)
- Neo4j 5+
- Redis 7+
- Docker & Docker Compose (可选）

### 2. 安装依赖

```bash
# 克隆项目
git clone <repo-url>
cd chip_fault_agent

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，配置以下关键项：
# - DATABASE_URL: PostgreSQL连接URL
# - NEO4J_URI: Neo4j连接URI
# - REDIS_URL: Redis连接URL
# - JWT_SECRET_KEY: JWT签名密钥
# - OPENAI_API_KEY: OpenAI API密钥（可选）
```

### 4. 初始化数据库

```bash
# 初始化数据库表结构
python scripts/init_db.py

# 初始化RBAC系统（创建默认角色、权限和管理员账户）
python scripts/init_rbac.py
```

### 5. 启动服务

```bash
# 方式一：一键启动
python scripts/start_all.py

# 方式二：分别启动（需要两个终端）
# 终端1 - API服务（端口8000）
python run.py api

# 终端2 - 前端服务（端口8501）
python run.py frontend
```

### 6. 访问系统

- **API文档**: http://localhost:8000/docs
- **前端界面**: http://localhost:8501
- **默认管理员账户**:
  - 用户名: `admin`
  - 密码: `admin123`

## API文档

### 认证接口

| 接口 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `POST /api/v1/auth/login` | 登录 | 获取访问令牌 | 公开 |
| `POST /api/v1/auth/logout` | 登出 | 注销当前会话 | 已认证 |
| `POST /api/v1/auth/refresh` | 刷新令牌 | 获取新的访问令牌 | 已认证 |
| `GET /api/v1/auth/me` | 获取当前用户 | 获取当前用户信息 | 已认证 |
| `POST /api/v1/auth/register` | 注册 | 创建新用户 | 公开 |

### 分析接口

| 接口 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `POST /api/v1/analyze` | 提交分析 | 提交日志进行分析 | `analysis:create` |
| `GET /api/v1/analysis/{id}` | 获取结果 | 获取分析结果 | `analysis:read` |
| `GET /api/v1/analysis/{id}/report` | 生成报告 | 生成HTML报告 | `analysis:read` |
| `GET /api/v1/health` | 健康检查 | 检查系统状态 | 公开 |
| `GET /api/v1/modules` | 模块列表 | 获取支持的模块 | `analysis:read` |

### 用户管理接口

| 接口 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `GET /api/v1/admin/users` | 用户列表 | 获取所有用户 | `user:read` |
| `POST /api/v1/admin/users` | 创建用户 | 创建新用户 | `user:create` |
| `PUT /api/v1/admin/users/{user_id}` | 更新用户 | 更新用户信息 | `user:update` |
| `DELETE /api/v1/admin/users/{user_id}` | 删除用户 | 删除用户 | `user:delete` |
| `POST /api/v1/admin/users/{user_id}/roles` | 分配角色 | 为用户分配角色 | `user:update` |

### 角色管理接口

| 接口 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `GET /api/v1/admin/roles` | 角色列表 | 获取所有角色 | `role:read` |
| `POST /api/v1/admin/roles` | 创建角色 | 创建新角色 | `role:create` |
| `PUT /api/v1/admin/roles/{role_id}` | 更新角色 | 更新角色信息 | `role:update` |
| `POST /api/v1/admin/roles/{role_id}/permissions` | 分配权限 | 为角色分配权限 | `role:update` |

### 专家修正接口

| 接口 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `POST /api/v1/expert/corrections/{analysis_id}` | 提交修正 | 提交专家修正 | `expert_correction:create` |
| `GET /api/v1/expert/corrections` | 修正列表 | 获取修正列表 | `expert_correction:create` |
| `POST /api/v1/expert/corrections/{id}/approve` | 批准修正 | 批准专家修正 | `expert_correction:approve` |
| `POST /api/v1/expert/corrections/{id}/reject` | 拒绝修正 | 拒绝专家修正 | `expert_correction:reject` |
| `POST /api/v1/expert/assign/{analysis_id}` | 分配专家 | 分配专家处理任务 | `analysis:update` |
| `GET /api/v1/expert/experts` | 专家列表 | 获取可用专家列表 | `user:read` |
| `GET /api/v1/expert/knowledge/statistics` | 知识统计 | 获取知识学习统计 | `audit_log:read` |

### 知识库接口

| 接口 | 方法 | 描述 | 权限 |
|------|------|------|------|
| `GET /api/v1/cases` | 案例列表 | 获取历史案例 | `case:read` |
| `POST /api/v1/cases` | 创建案例 | 创建新案例 | `case:create` |
| `PUT /api/v1/cases/{case_id}` | 更新案例 | 更新案例信息 | `case:update` |
| `GET /api/v1/rules` | 规则列表 | 获取推理规则 | `rule:read` |
| `POST /api/v1/rules` | 创建规则 | 创建新规则 | `rule:create` |

## 系统角色

### 预定义角色

| 角色名称 | 显示名称 | 描述 | 权限级别 |
|----------|----------|------|----------|
| `super_admin` | 超级管理员 | 系统最高权限，拥有所有操作权限 | 100 |
| `admin` | 管理员 | 系统管理员，可以管理用户、角色和配置 | 80 |
| `expert` | 专家 | 领域专家，可以进行专家修正和知识库更新 | 60 |
| `analyst` | 分析师 | 普通分析师，可以提交分析请求和查看结果 | 40 |
| `viewer` | 查看者 | 只读权限，只能查看分析结果 | 20 |

### 权限说明

系统权限格式：`resource:action`

- **资源类型**: user, role, permission, analysis, case, rule, expert_correction, system_config, audit_log, report
- **操作类型**: create, read, update, delete, approve, reject, export

## 配置说明

主要配置项（参见`.env.example`）：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL连接URL | - |
| `NEO4J_URI` | Neo4j连接URI | bolt://localhost:7687 |
| `REDIS_URL` | Redis连接URL | - |
| `JWT_SECRET_KEY` | JWT签名密钥 | - |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌过期时间（分钟） | 30 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 刷新令牌过期时间（天） | 7 |
| `DEFAULT_CONFIDENCE_THRESHOLD` | 专家介入阈值 | 0.7 |
| `OPENAI_API_KEY` | OpenAI API密钥 | - |
| `ANTHROPIC_API_KEY` | Anthropic API密钥 | - |

## 开发指南

### 添加新模块类型

1. 在`src/database/models.py`中添加模块类型定义
2. 在`src/mcp/tools/`中实现对应的MCP工具
3. 更新配置文件中的模块类型列表

### 添加新的MCP工具

参考`src/mcp/tools/log_parser.py`的实现：

```python
from mcp.server import Server
from mcp.types import Tool

app = Server("chip-fault-tools")

@app.tool()
async def your_tool_name(param1: str, param2: int):
    """工具描述"""
    # 实现逻辑
    return {"result": "your_result"}
```

### 添加新的API端点

1. 在`src/api/`下创建新的路由文件
2. 使用认证装饰器保护端点：

```python
from fastapi import APIRouter, Depends
from ..auth.decorators import require_auth, require_permission
from ..auth.dependencies import get_current_user_required

router = APIRouter()

@router.post("/your-endpoint")
@require_auth
@require_permission("your_resource:your_action")
async def your_endpoint(
    current_user: User = Depends(get_current_user_required)
):
    # 实现逻辑
    pass
```

## 模块类型

系统支持以下SoC模块类型：

| 模块类型 | 说明 | 子类型 |
|----------|------|--------|
| `cpu` | CPU核心 | - |
| `l2_cache` | L2缓存（CPU私有） | - |
| `l3_cache` | L3共享缓存 | - |
| `ha` | 一致性代理 | agent / snoop_filter / directory |
| `noc_router` | NoC路由器 | - |
| `noc_endpoint` | NoC端点 | - |
| `ddr_controller` | DDR控制器 | - |
| `hbm_controller` | HBM控制器 | - |

## 测试

```bash
# 运行快速测试脚本
python scripts/quick_test.py

# 运行完整的系统验证
python scripts/test_complete_system.py

# 运行API测试
python tests/test_api.py

# 测试数据库连接
python scripts/test_db.py
```

## Docker部署

```bash
# 构建镜像
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL是否运行
   - 验证DATABASE_URL配置是否正确
   - 确保pgvector扩展已安装

2. **Neo4j连接失败**
   - 检查Neo4j是否运行
   - 验证NEO4J_URI配置是否正确
   - 确认用户名密码正确

3. **JWT令牌过期**
   - 检查JWT_ACCESS_TOKEN_EXPIRE_MINUTES配置
   - 使用refresh端点获取新令牌

4. **权限不足**
   - 确认用户具有所需角色
   - 检查角色是否具有相应权限
   - 联系管理员分配权限

## 许可证

[待添加]

## 贡献指南

[待添加]
