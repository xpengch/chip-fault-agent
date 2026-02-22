# 本地开发指南（不使用Docker）

## 问题说明

Docker Hub 连接失败（网络问题或服务限���）。

## 解决方案

### 选项1：使用本地安装的数据库

如果你本地已安装 PostgreSQL、Neo4j、Redis：

```bash
# 1. 确保 PostgreSQL 服务运行
# Windows: 服务管理器中启动 PostgreSQL 服务
# Linux: sudo systemctl start postgresql

# 2. 确保端口可访问
netstat -an | grep 5432  # PostgreSQL
netstat -an | grep 6379  # Redis
netstat -an | grep 7474  # Neo4j HTTP
netstat -an | grep 7687  # Neo4j Bolt

# 3. 初始化数据库
python scripts/init_db.py

# 4. 启动API和前端
python run.py api      # 新终端
python run.py frontend  # 新终端
```

### 选项2：使用 Docker 镜像加速器

配置 Docker Hub 镜像加速（中国大陆用户）：

1. 打开 Docker Desktop
2. 进入 Settings → Docker Engine
3. 添加镜像加速配置：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://mirror.ccs.tencentyun.com"
  ]
}
```

4. 重启 Docker Desktop

### 选项3：模拟测试（无需数据库）

先进行代码级别测试，数据库连接可以模拟：

```bash
# 运行不依赖数据库的测试
python -c "
import sys
sys.path.insert(0, '.')

# 测试基础模块导入
from src.config.settings import get_settings
print('配置模块: OK')

from src.database.models import SoCChip, SoCModule
print('数据库模型: OK')

from src.mcp.tools.log_parser import LogParserTool
print('日志解析工具: OK')

from src.agents.agent1 import Agent1, Agent1State
print('Agent1: OK')

print('\\n所有核心模块导入成功！')
"
```

### 选项4：使用在线数据库服务

使用云数据库服务（推荐用于开发）：

**PostgreSQL 云服务选项**：
- Supabase (免费层): https://supabase.com
- Neon (免费层): https://neon.tech
- Railway (免费层): https://railway.app

**Redis 云服务选项**：
- Redis Cloud (免费层): https://redis.com
- Upstash Redis: https://upstash.com

**Neo4j 云服务选项**：
- Neo4j Aura (免费层): https://neo4j.com/aura

配置步骤（以 Supabase ���例）：

1. 注册账号并创建项目
2. 获取连接信息：
   - Database URL
   - Port: 5432
   - Username: postgres
   - Password: [your password]
   - Database name: [your database]

3. 更新 `.env` 文件：
   ```bash
   DATABASE_URL=postgresql+asyncpg://postgres:[password]@aws-0-[region]-1.pooler.supabase.com:6543/chip_analysis
   ```

4. 同样配置 Redis 和 Neo4j（如果使用云服务）

### 快速验证

不管使用哪种方案，启动前先验证：

```bash
# 验证配置加载
python -c "from src.config.settings import get_settings; print('DB:', get_settings().DATABASE_URL[:30])"

# 验证模型导入
python -c "from src.database.models import SoCChip; print('Models OK')"

# 验证 API schemas
python -c "from src.api.schemas import AnalyzeRequest; print('Schemas OK')"
```

## 当前状态

✅ Python 3.12.10 已安装
✅ 所有项目依赖已安装
✅ .env 文件已配置
✅ 项目代码完整
❌ Docker 服务暂时无法使用

## 建议

1. **开发阶段**：使用选项2（镜像加速）或选项3（模拟测试）
2. **测试阶段**：使用选项1（本地数据库）或选项4（云数据库）
3. **生产部署**：使用云数据库服务

## 继续开发

可以继续进行以下工作（无需数据库）：
- 完善单元测试
- 优化前端 UI
- 添加更多测试用例
- 完善文档
- 添加性能监控

## 需要帮助？

如果需要配置云数据库或解决 Docker 问题，请告诉我：
- 你使用的操作系统
- 网络环境（是否有代理）
- 是否已有本地数据库安装
- 偏好使用哪种解决方案
