"""
单元测试 - 内存优化版
只测试单个函数，不加载完整系统
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelperFunctions:
    """测试辅助函数 - 无依赖"""

    def test_parse_error_codes(self):
        """测试错误码解析"""
        from src.utils.helpers import parse_error_codes

        result = parse_error_codes("Error: 0XCO001 and 0XLA001")
        assert result == ["0XCO001", "0XLA001"]

    def test_parse_error_codes_empty(self):
        """测试空输入"""
        from src.utils.helpers import parse_error_codes

        result = parse_error_codes("")
        assert result == []

    def test_parse_modules(self):
        """测试模块解析"""
        from src.utils.helpers import parse_modules

        result = parse_modules("Affected: cpu, l3_cache")
        assert "cpu" in result or "l3_cache" in result

    def test_infer_failure_domain_cpu(self):
        """测试CPU域推断"""
        from src.utils.helpers import infer_failure_domain

        codes = ["0XCO001"]
        modules = ["cpu"]
        result = infer_failure_domain(codes, modules)
        assert result in ["compute", "cpu", "unknown"]

    def test_infer_failure_domain_cache(self):
        """测试缓存域推断"""
        from src.utils.helpers import infer_failure_domain

        codes = ["0XLA001"]
        modules = ["l3_cache"]
        result = infer_failure_domain(codes, modules)
        assert result in ["cache", "l3_cache", "unknown"]

    def test_validate_chip_model_valid(self):
        """测试有效芯片型号"""
        from src.utils.helpers import validate_chip_model

        assert validate_chip_model("XC9000") == True
        assert validate_chip_model("XC8000") == True
        assert validate_chip_model("XC7000") == True

    def test_validate_chip_model_invalid(self):
        """测试无效芯片型号"""
        from src.utils.helpers import validate_chip_model

        assert validate_chip_model("INVALID") == False
        assert validate_chip_model("") == False


class TestLogParser:
    """测试日志解析器"""

    def test_parse_cpu_log(self):
        """测试CPU日志解析"""
        from src.mcp.tools.log_parser import LogParserTool

        parser = LogParserTool()
        result = parser.parse(
            log_content="[ERROR] Error Code: 0XCO001 - CPU fault",
            log_format="text",
            chip_model="XC9000"
        )

        assert result["success"] == True
        assert len(result.get("error_codes", [])) > 0

    def test_parse_empty_log(self):
        """测试空日志"""
        from src.mcp.tools.log_parser import LogParserTool

        parser = LogParserTool()
        result = parser.parse(
            log_content="",
            log_format="text",
            chip_model="XC9000"
        )

        # 空日志应该返回成功但无数据
        assert result["success"] == True


class TestSchemaValidation:
    """测试Schema验证"""

    def test_valid_request(self):
        """测试有效请求"""
        from src.api.schemas import AnalyzeRequest

        request = AnalyzeRequest(
            chip_model="XC9000",
            raw_log="[ERROR] Test",
            infer_threshold=0.7
        )

        assert request.chip_model == "XC9000"
        assert request.infer_threshold == 0.7

    def test_invalid_threshold_low(self):
        """测试无效阈值（太低）"""
        from src.api.schemas import AnalyzeRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AnalyzeRequest(
                chip_model="XC9000",
                raw_log="[ERROR] Test",
                infer_threshold=-0.1
            )

    def test_invalid_threshold_high(self):
        """测试无效阈值（太高）"""
        from src.api.schemas import AnalyzeRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AnalyzeRequest(
                chip_model="XC9000",
                raw_log="[ERROR] Test",
                infer_threshold=1.5
            )

    def test_missing_chip_model(self):
        """测试缺少芯片型号"""
        from src.api.schemas import AnalyzeRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AnalyzeRequest(
                raw_log="[ERROR] Test",
                infer_threshold=0.7
            )


class TestAgentState:
    """测试Agent状态对象"""

    def test_agent1_state_creation(self):
        """测试Agent1状态创建"""
        from src.agents.agent1 import Agent1State

        state = Agent1State()

        assert state.session_id is None
        assert state.chip_model is None
        assert state.raw_log is None

    def test_agent1_state_set(self):
        """测试Agent1状态设置"""
        from src.agents.agent1 import Agent1State

        state = Agent1State()
        state.session_id = "test_123"
        state.chip_model = "XC9000"

        assert state.session_id == "test_123"
        assert state.chip_model == "XC9000"

    def test_agent2_state_creation(self):
        """测试Agent2状态创建"""
        from src.agents.agent2 import Agent2State

        state = Agent2State()

        assert state.session_id is None
        assert state.expert_inputs is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
