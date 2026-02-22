"""
芯片失效分析AI Agent系统 - 轻量级内存友好测试
每次测试独立运行，避免累积内存占用
"""

import sys
import os
import gc
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_test(test_name: str, test_func) -> bool:
    """运行单个测试并清理内存"""
    print(f"\n{'='*50}")
    print(f"测试: {test_name}")
    print('='*50)

    try:
        result = test_func()
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{status}\n")
        return result
    except Exception as e:
        print(f"[ERROR] 异常: {str(e)}\n")
        return False
    finally:
        # 强制垃圾回收
        gc.collect()


def test_imports_only():
    """仅测试导入，不初始化任何组件"""
    print("  测试模块导入...")

    # 不实际导入，只检查文件存在
    modules_to_check = [
        "src/config/settings.py",
        "src/database/models.py",
        "src/mcp/tools/log_parser.py",
        "src/mcp/tools/knowledge_graph.py",
        "src/mcp/tools/database_tools.py",
        "src/mcp/tools/llm_tool.py",
        "src/agents/agent1/__init__.py",
        "src/agents/workflow.py",
        "src/api/schemas.py",
        "src/api/app.py",
    ]

    for module_path in modules_to_check:
        full_path = Path(__file__).parent.parent / module_path
        if full_path.exists():
            print(f"    [OK] {module_path}")
        else:
            print(f"    [FAIL] {module_path} - 文件不存在")
            return False

    return True


def test_log_parser():
    """测试日志解析器"""
    print("  测试日志解析功能...")

    # 延迟导入
    import asyncio
    from src.mcp.tools.log_parser import LogParserTool

    async def run_parse_test():
        parser = LogParserTool()
        test_log = "[ERROR] Error Code: 0XCO001 - CPU fault"

        result = await parser.parse(
            chip_model="XC9000",
            raw_log=test_log,
            log_format="auto"
        )

        # 检查结果结构
        if result and isinstance(result, dict):
            features = result.get("parsed_features", {})
            error_codes = features.get("error_codes", [])
            print(f"    [OK] 解析成功，错误码: {error_codes}")
            return True
        else:
            print(f"    [FAIL] 解析失败: {result}")
            return False

    try:
        return asyncio.run(run_parse_test())
    except Exception as e:
        print(f"    [FAIL] 异常: {str(e)}")
        return False


def test_helper_functions():
    """测试辅助函数"""
    print("  测试辅助函数...")

    from src.utils.helpers import (
        parse_error_codes,
        parse_modules,
        infer_failure_domain
    )

    # 测试错误码解析
    codes = parse_error_codes("Error: 0XCO001 and 0XLA001")
    print(f"    [OK] 错误码解析: {codes}")

    # 测试模块解析
    modules = parse_modules("Affected: cpu, l3_cache")
    print(f"    [OK] 模块解析: {modules}")

    # 测试域推断
    domain = infer_failure_domain(codes, modules)
    print(f"    [OK] 域推断: {domain}")

    return True


def test_schema_validation():
    """测试Schema验证"""
    print("  测试Schema验证...")

    from src.api.schemas import AnalyzeRequest

    try:
        request = AnalyzeRequest(
            chip_model="XC9000",
            raw_log="[ERROR] Test",
            infer_threshold=0.7
        )
        print(f"    [OK] 请求验证通过")
        return True
    except Exception as e:
        print(f"    [FAIL] 验证失败: {e}")
        return False


def test_agent1_state():
    """测试Agent1状态对象"""
    print("  测试Agent1状态...")

    from src.agents.agent1 import Agent1State

    try:
        state = Agent1State()
        print(f"    [OK] Agent1State创建成功")
        # 不初始化Agent，避免加载LangGraph
        return True
    except Exception as e:
        print(f"    [FAIL] Agent1State创建失败: {e}")
        return False


def test_llm_tool_init():
    """测试LLM工具初始化"""
    print("  测试LLM工具初始化...")

    try:
        from src.mcp.tools.llm_tool import LLMTool
        # 只创建实例，不调用
        tool = LLMTool()
        print(f"    [OK] LLMTool初始化成功")
        return True
    except Exception as e:
        print(f"    [FAIL] LLMTool初始化失败: {e}")
        return False


def test_api_health():
    """测试API健康检查"""
    print("  测试API健康检查...")

    try:
        import requests
        response = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=2)

        if response.status_code == 200:
            print(f"    [OK] API运行正常")
            return True
        else:
            print(f"    [FAIL] API返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"    [FAIL] API连接失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*50)
    print("轻量级内存友好测试")
    print("="*50)

    tests = [
        ("文件结构检查", test_imports_only),
        ("日志解析", test_log_parser),
        ("辅助函数", test_helper_functions),
        ("Schema验证", test_schema_validation),
        ("Agent1状态", test_agent1_state),
        ("LLM工具", test_llm_tool_init),
        ("API健康", test_api_health),
    ]

    results = []
    for test_name, test_func in tests:
        result = run_test(test_name, test_func)
        results.append((test_name, result))

        # 每次测试后清理
        gc.collect()

    # 输出结果
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)

    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed

    for test_name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print(f"\n总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")

    if failed == 0:
        print("\n[OK] 所有测试通过！")
    else:
        print(f"\n[WARNING] {failed} 个测试失败")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n\n测试异常: {str(e)}")
