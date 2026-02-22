# 内存优化测试说明

本目录包含内存优化的测试套件，适合在低内存环境下运行。

## 测试类型

### 1. 轻量级测试 (test_lightweight.py)

最节省内存的测试方式，每次只测试一个组件：

```bash
# 直接运行
python tests/test_lightweight.py

# 或使用测试运行器
python run_tests.py --type light
```

特点：
- ✅ 每次测试后自动垃圾回收
- ✅ 不初始化数据库连接
- ✅ 不加载LangGraph等大型依赖
- ✅ 内存占用 < 100MB

### 2. 单元测试 (test_unit_simple.py)

独立的单元测试，不依赖外部服务：

```bash
# 使用pytest运行
pytest tests/test_unit_simple.py -v

# 或使用测试运行器
python run_tests.py --type unit
```

特点：
- ✅ 每个测试独立运行
- ✅ 使用Mock避免真实连接
- ✅ 测试完成后自动清理
- ✅ 内存占用 < 150MB

### 3. 完整测试 (test_complete_system.py)

**警告**: 此测试会加载所有组件，需要大量内��：

```bash
python scripts/test_complete_system.py
```

内存需求: > 1GB

## 测试配置

### pytest.ini (内存优化配置)

```ini
[pytest]
# 禁用不需要的插件
-p no:stepwise
-p no:warnings

# 超时设置
--timeout=30

# 简化输出
--tb=short

# 不捕获输出
capture = no
```

### conftest.py (自动清理)

每个测试后自动：
1. 运行垃圾回收
2. 清理大型模块缓存
3. 关闭数据库连接池

## 运行建议

### 低内存环境 (< 512MB)

```bash
# 只运行轻量级测试
python run_tests.py --type light
```

### 中等内存环境 (512MB - 1GB)

```bash
# 运行单元测试
python run_tests.py --type unit
```

### 高内存环境 (> 1GB)

```bash
# 运行所有测试
python run_tests.py --type all
```

## 手动控制内存

如果仍然遇到内存问题，可以逐个运行测试：

```python
# Python交互式环境中
import gc
from tests.test_lightweight import test_log_parser

# 运行单个测试
test_log_parser()

# 手动清理
gc.collect()
```

## 故障排除

### 内存溢出错误

1. 关闭其他应用程序
2. 使用 `--type light` 只运行轻量级测试
3. 分批运行测试，而不是一次性运行全部

### 测试卡住

1. 检查API服务是否在运行
2. 使用超时设置: `pytest --timeout=10`
3. 跳过需要API的测试

### 导入错误

1. 确保在项目根目录运行
2. 检查PYTHONPATH设置
3. 使用 `python -m pytest` 而不是 `pytest`
