"""
Pytest配置 - 内存优化版
每个测试后自动清理内存
"""

import gc
import sys
from pathlib import Path
import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def cleanup(request):
    """
    每个测试后自动清理内存
    """
    # 测试前清理
    gc.collect()

    yield

    # 测试后清理
    gc.collect()

    # 清理大型模块缓存（仅测试环境）
    if 'langgraph' in sys.modules:
        # LangGraph占用大量内存，测试后清理
        del sys.modules['langgraph']
    if 'sqlalchemy' in sys.modules:
        # SQLAlchemy连接池占用内存
        import sqlalchemy.pool
        sqlalchemy.pool.dispose_all()

    gc.collect()


@pytest.fixture
def minimal_db():
    """
    最小化数据库fixture
    不建立真实连接，只使用内存模式
    """
    from unittest.mock import Mock, AsyncMock

    # Mock数据库管理器
    mock_db = Mock()
    mock_db.initialize = AsyncMock()
    mock_db.get_session = AsyncMock()
    mock_db.close = AsyncMock()

    return mock_db


@pytest.fixture
def sample_logs():
    """
    示例日志数据
    避免每次测试都重新创建
    """
    return {
        "cpu_error": "[ERROR] Error Code: 0XCO001 - CPU fault",
        "cache_error": "[ERROR] Error Code: 0XLA001 - Cache error",
        "memory_error": "[ERROR] Error Code: 0XME001 - Memory error",
    }


@pytest.fixture
def mock_workflow():
    """
    Mock工作流，避免加载LangGraph
    """
    from unittest.mock import Mock, AsyncMock

    mock = Mock()
    mock.run = AsyncMock(return_value={
        "success": True,
        "session_id": "test_123",
        "final_root_cause": {
            "failure_domain": "compute",
            "root_cause": "Test cause",
            "confidence": 0.8
        }
    })

    return mock
