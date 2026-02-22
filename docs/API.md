# 芯片失效分析AI Agent系统 - API文档

## 目录

- [概述](#概述)
- [认证](#认证)
- [错误处理](#错误处理)
- [认证接口](#认证接口)
- [分析接口](#分析接口)
- [用户管理接口](#用户管理接口)
- [角色管理接口](#角色管理接口)
- [权限管理接口](#权限管理接口)
- [专家修正接口](#专家修正接口)
- [知识库接口](#知识库接口)
- [系统接口](#系统接口)

## 概述

API基础URL: `http://localhost:8000`

所有API响应遵循统一的响应格式：

```json
{
  "success": true/false,
  "data": { ... },
  "message": "操作成功",
  "error": "错误详情（��错误时）"
}
```

## 认证

系统使用JWT (JSON Web Token) 进行身份认证。

### 认证流程

1. 调用登录接口获取访问令牌（access_token）和刷新令牌（refresh_token）
2. 在请求头中添加访问令牌：`Authorization: Bearer {access_token}`
3. 访问令牌过期后，使用刷新令牌获取新的访问令牌

### 认证头格式

```
Authorization: Bearer <access_token>
```

## 错误处理

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或令牌过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 参数验证失败 |
| 500 | 服务器内部错误 |

错误响应格式：

```json
{
  "detail": "错误描述信息"
}
```

## 认证接口

### 1. 用户登录

**接口**: `POST /api/v1/auth/login`

**描述**: 用户登录获取访问令牌

**请求体**:

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "user_id": "admin",
    "username": "admin",
    "email": "admin@example.com",
    "roles": ["super_admin"]
  }
}
```

### 2. 用户登出

**接口**: `POST /api/v1/auth/logout`

**描述**: 用户登出，使当前会话失效

**请求头**: 需要认证

**响应**:

```json
{
  "success": true,
  "message": "登出成功"
}
```

### 3. 刷新令牌

**接口**: `POST /api/v1/auth/refresh`

**描述**: 使用刷新令牌获取新的访问令牌

**请求体**:

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 4. 获取当前用户信息

**接口**: `GET /api/v1/auth/me`

**描述**: 获取当前登录用户的详细信息

**请求头**: 需要认证

**响应**:

```json
{
  "user_id": "admin",
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "系统管理员",
  "department": "技术部",
  "position": "系统管理员",
  "roles": [
    {
      "name": "super_admin",
      "display_name": "超级管理员"
    }
  ],
  "permissions": [
    "user:create",
    "user:read",
    "analysis:create"
  ],
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 5. 用户注册

**接口**: `POST /api/v1/auth/register`

**描述**: 注册新用户（需要管理员审批或开放注册时可用）

**请求体**:

```json
{
  "username": "newuser",
  "password": "password123",
  "email": "newuser@example.com",
  "full_name": "新用户"
}
```

**响应**:

```json
{
  "success": true,
  "message": "注册成功，请等待管理员审核",
  "user_id": "newuser"
}
```

## 分析接口

### 1. 提交分析

**接口**: `POST /api/v1/analyze`

**描述**: 提交芯片日志进行失效分析

**权限**: `analysis:create`

**请求体**:

```json
{
  "chip_model": "XC9000",
  "raw_log": "ERROR: CPU fault detected - 0X010001 at core 0",
  "session_id": "session_123456"
}
```

**响应**:

```json
{
  "success": true,
  "session_id": "session_123456",
  "analysis_id": "ANALYSIS_20240120_001",
  "status": "completed",
  "final_root_cause": {
    "failure_domain": "compute",
    "module": "cpu",
    "root_cause": "CPU算力逻辑单元异常",
    "root_cause_category": "硬件故障",
    "confidence": 0.85
  },
  "infer_trace": [
    {
      "step": "日志解析",
      "description": "解析原始日志",
      "timestamp": "2024-01-20T10:00:00Z"
    }
  ],
  "need_expert": false
}
```

### 2. 获取分析结果

**接口**: `GET /api/v1/analysis/{analysis_id}`

**描述**: 获取指定分析ID的详细结果

**权限**: `analysis:read`

**路径参数**:
- `analysis_id`: 分析ID

**响应**:

```json
{
  "success": true,
  "data": {
    "analysis_id": "ANALYSIS_20240120_001",
    "chip_model": "XC9000",
    "status": "completed",
    "fault_features": {
      "error_codes": ["0X010001"],
      "modules": ["cpu"]
    },
    "final_root_cause": {
      "failure_domain": "compute",
      "module": "cpu",
      "root_cause": "CPU算力逻辑单元异常",
      "confidence": 0.85
    },
    "created_at": "2024-01-20T10:00:00Z"
  }
}
```

### 3. 生成分析报告

**接口**: `GET /api/v1/analysis/{analysis_id}/report`

**描述**: 生成HTML格式的分析报告

**权限**: `analysis:read`

**路径参数**:
- `analysis_id`: 分析ID

**查询参数**:
- `format`: 报告格式，支持 `html`、`json`、`pdf`（默认：html）

**响应**: 返回HTML报告内容或文件

### 4. 获取支持的模块列表

**接口**: `GET /api/v1/modules`

**描述**: 获取系统支持的所有芯片模块类型

**权限**: `analysis:read`

**响应**:

```json
{
  "success": true,
  "data": [
    {
      "module_type": "cpu",
      "display_name": "CPU核心",
      "description": "中央处理器核心"
    },
    {
      "module_type": "l3_cache",
      "display_name": "L3缓存",
      "description": "三级共享缓存"
    }
  ]
}
```

## 用户管理接口

### 1. 获取用户列表

**接口**: `GET /api/v1/admin/users`

**描述**: 获取系统中所有用户列表

**权限**: `user:read`

**查询参数**:
- `skip`: 跳过的记录数（默认：0）
- `limit`: 返回的记录数（默认：50，最大：100）
- `role`: 按角色筛选（可选）
- `is_active`: 按状态筛选（可选）

**响应**:

```json
{
  "success": true,
  "data": [
    {
      "user_id": "admin",
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "系统管理员",
      "department": "技术部",
      "is_active": true,
      "roles": ["super_admin"]
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

### 2. 创建用户

**接口**: `POST /api/v1/admin/users`

**描述**: 创建新用户

**权限**: `user:create`

**请求体**:

```json
{
  "username": "newuser",
  "password": "password123",
  "email": "newuser@example.com",
  "full_name": "新用户",
  "department": "分析部",
  "position": "分析师",
  "roles": ["analyst"]
}
```

**响应**:

```json
{
  "success": true,
  "message": "用户创建成功",
  "data": {
    "user_id": "newuser",
    "username": "newuser"
  }
}
```

### 3. 更新用户

**接口**: `PUT /api/v1/admin/users/{user_id}`

**描述**: 更新用户信息

**权限**: `user:update`

**路径参数**:
- `user_id`: 用户ID

**请求体**:

```json
{
  "email": "updated@example.com",
  "full_name": "更新姓名",
  "department": "新部门",
  "is_active": true
}
```

### 4. 删除用户

**接口**: `DELETE /api/v1/admin/users/{user_id}`

**描述**: 删除指定用户

**权限**: `user:delete`

**路径参数**:
- `user_id`: 用户ID

**响应**:

```json
{
  "success": true,
  "message": "用户删除成功"
}
```

### 5. 分配角色

**接口**: `POST /api/v1/admin/users/{user_id}/roles`

**描述**: 为用户分配角色

**权限**: `user:update`

**路径参数**:
- `user_id`: 用户ID

**请求体**:

```json
{
  "roles": ["expert", "analyst"]
}
```

## 角色管理接口

### 1. 获取角色列表

**接口**: `GET /api/v1/admin/roles`

**描述**: 获取系统中所有角色

**权限**: `role:read`

**响应**:

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "super_admin",
      "display_name": "超级管理员",
      "description": "系统最高权限",
      "is_system_role": true,
      "level": 100
    }
  ]
}
```

### 2. 创建角色

**接口**: `POST /api/v1/admin/roles`

**描述**: 创建新角色

**权限**: `role:create`

**请求体**:

```json
{
  "name": "custom_role",
  "display_name": "自定义角色",
  "description": "角色描述",
  "permissions": ["analysis:read", "case:read"]
}
```

### 3. 为角色分配权限

**接口**: `POST /api/v1/admin/roles/{role_id}/permissions`

**描述**: 为角色分配权限

**权限**: `role:update`

**路径参数**:
- `role_id`: 角色ID

**请求体**:

```json
{
  "permissions": ["analysis:create", "analysis:read", "case:read"]
}
```

## 专家修正接口

### 1. 提交专家修正

**接口**: `POST /api/v1/expert/corrections/{analysis_id}`

**描述**: 对AI分析结果提交专家修正

**权限**: `expert_correction:create`

**路径参数**:
- `analysis_id`: 分析ID

**请求体**:

```json
{
  "failure_domain": "cache",
  "module": "l3_cache",
  "root_cause": "L3缓存控制器固件BUG",
  "root_cause_category": "软件故障",
  "confidence": 0.95,
  "correction_reason": "根据实际测试结果验证，L3缓存在特定访问模式下会出现异常"
}
```

**响应**:

```json
{
  "success": true,
  "correction_id": "CORRECTION_20240120_001",
  "analysis_id": "ANALYSIS_20240120_001",
  "status": "pending",
  "message": "修正提交成功，等待审核"
}
```

### 2. 获取修正列表

**接口**: `GET /api/v1/expert/corrections`

**描述**: 获取专家修正列表

**权限**: `expert_correction:create`

**查询参数**:
- `skip`: 跳过的记录数（默认：0）
- `limit`: 返回的记录数（默认：50）
- `status`: 按状态筛选（pending/approved/rejected）

**响应**:

```json
{
  "success": true,
  "data": [
    {
      "correction_id": "CORRECTION_20240120_001",
      "analysis_id": "ANALYSIS_20240120_001",
      "expert_name": "张专家",
      "status": "pending",
      "submitted_at": "2024-01-20T10:00:00Z"
    }
  ],
  "total": 1
}
```

### 3. 批准修正

**接口**: `POST /api/v1/expert/corrections/{correction_id}/approve`

**描述**: 批准专家修正，将修正应用到知识库

**权限**: `expert_correction:approve`

**路径参数**:
- `correction_id`: 修正ID

**请求体**:

```json
{
  "comments": "修正准确，已批准"
}
```

**响应**:

```json
{
  "success": true,
  "message": "修正已批准，知识库已更新"
}
```

### 4. 拒绝修正

**接口**: `POST /api/v1/expert/corrections/{correction_id}/reject`

**描述**: 拒绝专家修正

**权限**: `expert_correction:reject`

**路径参数**:
- `correction_id`: 修正ID

**请求体**:

```json
{
  "reason": "修正依据不足，需要更多测试数据支持"
}
```

### 5. 分配专家

**接口**: `POST /api/v1/expert/assign/{analysis_id}`

**描述**: 为分析任务分配专家

**权限**: `analysis:update`

**路径参数**:
- `analysis_id`: 分析ID

**请求体**:

```json
{
  "expert_id": "expert_001",
  "department": "CPU设计部"
}
```

### 6. 获取专家列表

**接口**: `GET /api/v1/expert/experts`

**描述**: 获取可用专家列表

**权限**: `user:read`

**查询参数**:
- `department`: 按部门筛选（可选）
- `failure_domain`: 按失效域筛选（可选）

**响应**:

```json
{
  "success": true,
  "data": [
    {
      "expert_id": "expert_001",
      "expert_name": "张专家",
      "department": "CPU设计部",
      "specialties": ["compute", "cpu"],
      "workload": 5
    }
  ]
}
```

### 7. 获取知识统计

**接口**: `GET /api/v1/expert/knowledge/statistics`

**描述**: 获取知识学习统计信息

**权限**: `audit_log:read`

**响应**:

```json
{
  "success": true,
  "data": {
    "total_corrections": 100,
    "approved_corrections": 85,
    "rejected_corrections": 15,
    "cases_learned": 85,
    "rules_updated": 42
  }
}
```

## 知识库接口

### 1. 获取案例列表

**接口**: `GET /api/v1/cases`

**描述**: 获取失效案例库

**权限**: `case:read`

**查询参数**:
- `chip_model`: 按芯片型号筛选（可选）
- `failure_domain`: 按失效域筛选（可选）
- `skip`: 跳过的记录数（默认：0）
- `limit`: 返回的记录数（默认：50）

**响应**:

```json
{
  "success": true,
  "data": [
    {
      "case_id": "CASE_001",
      "chip_model": "XC9000",
      "failure_domain": "compute",
      "module_type": "cpu",
      "symptoms": "CPU算力逻辑单元异常",
      "root_cause": "硬件故障",
      "verified": true
    }
  ],
  "total": 1
}
```

### 2. 创建案例

**接口**: `POST /api/v1/cases`

**描述**: 创建新的失效案例

**权限**: `case:create`

### 3. 获取推理规则

**接口**: `GET /api/v1/rules`

**描述**: 获取推理规则库

**权限**: `rule:read`

**查询参数**:
- `chip_model`: 按芯片型号筛选（可选）
- `is_active`: 只返回激活的规则（默认：true）

**响应**:

```json
{
  "success": true,
  "data": [
    {
      "rule_id": "RULE_001",
      "rule_name": "CPU故障定位规则",
      "chip_model": "XC9000",
      "conditions": {
        "error_codes": ["0X010001"],
        "modules": ["cpu"]
      },
      "conclusion": {
        "failure_domain": "compute",
        "root_cause": "CPU算力逻辑单元异常"
      },
      "confidence": 0.9,
      "is_active": true
    }
  ]
}
```

## 系统接口

### 1. 健康检查

**接口**: `GET /api/v1/health`

**描述**: 检查系统健康状态

**权限**: 公开

**响应**:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "neo4j": "connected",
    "redis": "connected"
  }
}
```

### 2. 获取系统统计

**接口**: `GET /api/v1/stats`

**描述**: 获取系统运行统计信息

**权限**: `analysis:read`

**响应**:

```json
{
  "success": true,
  "data": {
    "total_analyses": 1000,
    "today_analyses": 50,
    "avg_confidence": 0.82,
    "expert_intervention_rate": 0.15
  }
}
```

## WebSocket接口

### 实时分析推送

**接口**: `WS /api/v1/ws/analyze/{session_id}`

**描述**: 订阅分析过程的实时更新

**权限**: 已认证

**消息格式**:

```json
{
  "type": "progress",
  "step": "日志解析",
  "progress": 50,
  "message": "正在解析日志..."
}
```

## SDK使用示例

### Python SDK

```python
from chip_fault_agent import ChipFaultClient

# 初始化客户端
client = ChipFaultClient(
    base_url="http://localhost:8000",
    username="admin",
    password="admin123"
)

# 提交分析
result = client.analyze(
    chip_model="XC9000",
    raw_log="ERROR: CPU fault detected - 0X010001"
)

print(f"失效域: {result['failure_domain']}")
print(f"根因: {result['root_cause']}")
```

### JavaScript SDK

```javascript
import { ChipFaultClient } from '@chip-fault/sdk';

const client = new ChipFaultClient({
  baseUrl: 'http://localhost:8000',
  username: 'admin',
  password: 'admin123'
});

const result = await client.analyze({
  chipModel: 'XC9000',
  rawLog: 'ERROR: CPU fault detected - 0X010001'
});

console.log(`失效域: ${result.failureDomain}`);
console.log(`根因: ${result.rootCause}`);
```

## 速率限制

API调用有以下速率限制：

- 普通用户: 100次/分钟
- 专家用户: 200次/分钟
- 管理员: 无限制

超过限制将返回429状态码。

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2024-01-20 | 初始版本，包含Phase 1和Phase 2所有功能 |
