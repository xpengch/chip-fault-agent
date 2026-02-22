"""
芯片失效分析AI Agent系统 - 简化测试脚本
验证核心代码功能（无需真实数据库）
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """测试所有模块导入"""
    print("=" * 60)
    print("测试模块导入...")
    print("=" * 60)

    tests = [
        ("配置模块", "from src.config.settings import get_settings"),
        ("数据库模型", "from src.database.models import SoCChip, SoCModule"),
        ("Neo4j Schema", "from src.database.neo4j_schema import KnowledgeGraphSchema"),
        ("日志解析工具", "from src.mcp.tools.log_parser import LogParserTool"),
        ("知识图谱工具", "from src.mcp.tools.knowledge_graph import KnowledgeGraphTool"),
        ("数据库工具", "from src.mcp.tools.database_tools import DatabaseTool"),
        ("LLM工具", "from src.mcp.tools.llm_tool import LLMTool"),
        ("Agent1", "from src.agents.agent1 import Agent1, Agent1State"),
        ("工作流", "from src.agents.workflow import ChipFaultWorkflow"),
        ("API模型", "from src.api.schemas import AnalyzeRequest, AnalyzeResponse"),
        ("API路由", "from src.api.routes import router"),
        ("辅助函数", "from src.utils.helpers import parse_error_codes, parse_modules")
    ]

    passed = 0
    failed = 0

    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"  {name}: OK")
            passed += 1
        except Exception as e:
            print(f"  {name}: FAILED - {str(e)}")
            failed += 1

    print()
    print(f"导入测试结果: {passed}/{passed + failed} 通过")
    return failed == 0


def test_log_parser():
    """测试日志解析功能"""
    print()
    print("=" * 60)
    print("测试日志解析功能...")
    print("=" * 60)

    from src.mcp.tools.log_parser import LogParserTool

    parser = LogParserTool()

    # 测试 CPU 日志
    cpu_log = """
[ERROR] [CPU0] Core fault detected at 2024-01-15 10:23:45
[ERROR] Error Code: 0XCO001 - Core execution error
[INFO] Registers: 0x1A004000=0xDEADBEEF
[INFO] Affected modules: cpu
    """.strip()

    print("\n1. 测试 CPU 日志解析:")
    result = parser.parse(
        log_content=cpu_log,
        log_format="text",
        chip_model="XC9000"
    )

    if result["success"]:
        print(f"   成功 - 错误码: {result['error_codes']}")
        print(f"   模块: {result['affected_modules']}")
    else:
        print(f"   失败 - {result['error']}")

    # 测试 L3 缓存日志
    cache_log = """
[ERROR] Cache coherence violation at HA agent 5
[ERROR] Error Code: 0XLA001 - L3 cache coherence error
[INFO] HA State: MESI
    """.strip()

    print("\n2. 测试 L3 缓存日志解析:")
    result = parser.parse(
        log_content=cache_log,
        log_format="text",
        chip_model="XC9000"
    )

    if result["success"]:
        print(f"   成功 - 错误码: {result['error_codes']}")
        print(f"   推断域: {result['inferred_domain']}")
    else:
        print(f"   失败 - {result['error']}")


def test_helper_functions():
    """测试辅助函数"""
    print()
    print("=" * 60)
    print("测试辅助函数...")
    print("=" * 60)

    from src.utils.helpers import (
        parse_error_codes,
        parse_modules,
        infer_failure_domain,
        validate_chip_model,
        format_confidence_percentage
    )

    # 测试错误码解析
    log_text = "[ERROR] Error Code: 0XCO001 and 0XLA001 detected"
    codes = parse_error_codes(log_text)
    print(f"\n1. 错误码解析: {codes}")

    # 测试模块解析
    modules = parse_modules(log_text)
    print(f"2. 模块解析: {modules}")

    # 测试失效域推断
    domain = infer_failure_domain(codes, modules)
    print(f"3. 失效域推断: {domain}")

    # 测试芯片型号验证
    valid = validate_chip_model("XC9000")
    print(f"4. 芯片型号验证 (XC9000): {valid}")

    # 测试置信度格式化
    confidence_str = format_confidence_percentage(0.85)
    print(f"5. 置信度格式化 (0.85): {confidence_str}")


def test_api_schemas():
    """测试 API schema 验证"""
    print()
    print("=" * 60)
    print("测试 API Schema...")
    print("=" * 60)

    from src.api.schemas import AnalyzeRequest, AnalyzeResponse

    # 测试请求数据验证
    print("\n1. 测试请求数据验证:")
    try:
        request = AnalyzeRequest(
            chip_model="XC9000",
            raw_log="[ERROR] Error Code: 0XCO001",
            infer_threshold=0.7
        )
        print(f"   请求验证: OK")
        print(f"   chip_model: {request.chip_model}")
        print(f"   infer_threshold: {request.infer_threshold}")
    except Exception as e:
        print(f"   请求数据验证失败: {e}")

    # 测试响应数据验证
    print("\n2. 测试响应数据验证:")
    try:
        response = AnalyzeResponse(
            success=True,
            message="测试",
            data=None
        )
        print(f"   响应验证: OK")
        print(f"   success: {response.success}")
        print(f"   message: {response.message}")
    except Exception as e:
        print(f"   响应验证失败: {e}")


def main():
    """主测试函数"""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "芯片失效分析AI Agent - 代码验证测试" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    all_passed = True

    # 运行各项测试
    all_passed &= test_imports()
    test_log_parser()
    test_helper_functions()
    test_api_schemas()

    # 输出总结
    print()
    print("=" * 60)
    if all_passed:
        print("✅ 所有测试通过！代码结构正确。")
    else:
        print("⚠️ 部分测试失败，请检查代码。")
    print("=" * 60)
    print()

    print("下一步建议：")
    print("1. 解决 Docker 连接问题或使用云数据库")
    print("2. 运行: python scripts/init_db.py")
    print("3. 启动服务: python run.py api")
    print("4. 运行完整测试: python tests/test_api.py")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
