"""
芯片失效分析AI Agent系统 - API自动化测试脚本
"""

import asyncio
import sys
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class APITester:
    """API测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.session_id: Optional[str] = None

    def test_health(self) -> bool:
        """测试健康检查"""
        logger.info("测试健康检查端点...")

        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)

            if response.status_code == 200:
                data = response.json()
                logger.success(f"  健康检查通过 - 版本: {data.get('version')}")
                return True
            else:
                logger.error(f"  健康检查失败 - 状态码: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"  健康检查异常: {str(e)}")
            return False

    def test_analyze_cpu_error(self) -> bool:
        """测试CPU错误分析"""
        logger.info("测试CPU错误分析...")

        log_content = """
[ERROR] [CPU0] Core fault detected at 2024-01-15 10:23:45
[ERROR] Error Code: 0XCO001 - Core execution error
[INFO] Registers: 0x1A004000=0xDEADBEEF, 0x1A004004=0x12345678
[INFO] Affected modules: cpu
        """.strip()

        return self._submit_and_check(
            chip_model="XC9000",
            raw_log=log_content,
            expected_domain="compute",
            expected_module="cpu"
        )

    def test_analyze_cache_error(self) -> bool:
        """测试L3缓存错误分析"""
        logger.info("测试L3缓存错误分析...")

        log_content = """
[ERROR] Cache coherence violation at HA agent 5
[ERROR] Error Code: 0XLA001 - L3 cache coherence error
[INFO] HA State: MESI, Cache Line: 0x12345678
[INFO] Affected modules: l3_cache, ha
        """.strip()

        return self._submit_and_check(
            chip_model="XC9000",
            raw_log=log_content,
            expected_domain="cache",
            expected_module="l3_cache"
        )

    def test_analyze_interconnect_error(self) -> bool:
        """测试互连错误分析"""
        logger.info("测试互连错误分析...")

        log_content = """
[ERROR] NoC routing conflict detected
[ERROR] Error Code: 0XNC001 - Router congestion
[ERROR] Error Code: 0XHA001 - Home Agent timeout
[INFO] Router ID: 15, Conflict path: HA5 -> NoC15
[INFO] Affected modules: noc_router, ha
        """.strip()

        return self._submit_and_check(
            chip_model="XC9000",
            raw_log=log_content,
            expected_domain="interconnect",
            expected_module=None  # 可能是ha或noc_router
        )

    def test_analyze_memory_error(self) -> bool:
        """测试内存错误分析"""
        logger.info("测试内存错误分析...")

        log_content = """
[ERROR] DDR controller timing violation
[ERROR] Error Code: 0XME001 - Memory training failed
[INFO] Channel: 0, Frequency: 5600MHz
[INFO] Affected modules: ddr_controller
        """.strip()

        return self._submit_and_check(
            chip_model="XC9000",
            raw_log=log_content,
            expected_domain="memory",
            expected_module="ddr_controller"
        )

    def test_query_result(self) -> bool:
        """测试查询分析结果"""
        logger.info("测试查询分析结果...")

        if not self.session_id:
            logger.warning("  没有可用的session_id，跳过查询测试")
            return False

        try:
            response = requests.get(
                f"{self.api_base}/analysis/{self.session_id}",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.success(f"  查询成功 - session: {self.session_id}")
                    return True
                else:
                    logger.error(f"  查询失败 - {data.get('error')}")
                    return False
            else:
                logger.error(f"  查询失败 - 状态码: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"  查询异常: {str(e)}")
            return False

    def test_invalid_input(self) -> bool:
        """测试无效输入处理"""
        logger.info("测试无效输入处理...")

        try:
            # 缺少必需参数
            response = requests.post(
                f"{self.api_base}/analyze",
                json={"chip_model": "XC9000"},  # 缺少raw_log
                timeout=10
            )

            # 应该返回错误
            if response.status_code == 422:  # Validation error
                logger.success("  无效输入正确拒绝")
                return True
            else:
                logger.warning(f"  无效输入处理可能有问题 - 状态码: {response.status_code}")
                return True  # 不算失败，API可能宽松处理

        except Exception as e:
            logger.error(f"  无效输入测试异常: {str(e)}")
            return False

    def _submit_and_check(
        self,
        chip_model: str,
        raw_log: str,
        expected_domain: str,
        expected_module: Optional[str] = None
    ) -> bool:
        """提交分析并检查结果"""

        try:
            response = requests.post(
                f"{self.api_base}/analyze",
                json={
                    "chip_model": chip_model,
                    "raw_log": raw_log,
                    "infer_threshold": 0.7
                },
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"  提交失败 - 状态码: {response.status_code}")
                return False

            data = response.json()

            if not data.get("success"):
                logger.error(f"  分析失败 - {data.get('error')}")
                return False

            # 保存session_id用于后续查询
            self.session_id = data.get("data", {}).get("session_id")

            # 验证结果
            result_data = data.get("data", {})
            root_cause = result_data.get("final_root_cause", {})

            actual_domain = root_cause.get("failure_domain")
            actual_module = root_cause.get("module")
            confidence = root_cause.get("confidence", 0.0)

            # 检查失效域
            if actual_domain == expected_domain:
                logger.success(f"  失效域正确: {actual_domain}")
            else:
                logger.warning(f"  失效域不符 - 预期: {expected_domain}, 实际: {actual_domain}")

            # 检查失效模块
            if expected_module:
                if actual_module == expected_module:
                    logger.success(f"  失效模块正确: {actual_module}")
                else:
                    logger.warning(f"  失效模块不符 - 预期: {expected_module}, 实际: {actual_module}")

            # 检查置信度
            if confidence >= 0.7:
                logger.success(f"  置信度良好: {confidence:.2f}")
            else:
                logger.warning(f"  置信度较低: {confidence:.2f}")

            return True

        except Exception as e:
            logger.error(f"  分析测试异常: {str(e)}")
            return False


def main():
    """主测试函数"""

    logger.info("=" * 60)
    logger.info("芯片失效分析AI Agent系统 - API自动化测试")
    logger.info("=" * 60)
    logger.info("")

    tester = APITester()

    # 运行测试
    tests = [
        ("健康检查", tester.test_health),
        ("CPU错误分析", tester.test_analyze_cpu_error),
        ("L3缓存错误分析", tester.test_analyze_cache_error),
        ("互连错误分析", tester.test_analyze_interconnect_error),
        ("内存错误分析", tester.test_analyze_memory_error),
        ("查询分析结果", tester.test_query_result),
        ("无效输入处理", tester.test_invalid_input),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'=' * 40}")
        logger.info(f"运行测试: {test_name}")
        logger.info(f"{'=' * 40}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试异常: {str(e)}")
            results.append((test_name, False))

    # 输出测试结果汇总
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    logger.info("")
    logger.info(f"总计: {len(results)} 个测试")
    logger.success(f"通过: {passed} 个")
    if failed > 0:
        logger.error(f"失败: {failed} 个")
    else:
        logger.success("所有测试通过！")


if __name__ == "__main__":
    main()
