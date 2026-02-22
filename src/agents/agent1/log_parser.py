"""
Agent1 - 日志解析Agent
负责：
1. 调用MCP日志解析工具
2. 验证和标准化提取的特征
3. 存储特征到全局状态
"""

from typing import Dict, List, Any, Optional
from langchain.tools import tool
from loguru import logger


class LogParserAgent:
    """日志解析Agent类"""

    def __init__(self):
        """初始化Agent"""
        self.name = "LogParserAgent"
        self.description = "解析芯片故障日志，提取标准化特征"

    async def parse(
        self,
        chip_model: str,
        raw_log: str,
        log_format: str = "auto"
    ) -> Dict[str, Any]:
        """
        解析芯片故障日志

        Args:
            chip_model: 芯片型号
            raw_log: 原始日志内容
            log_format: 日志格式（json/csv/text/auto）

        Returns:
            标准化故障特征字典
        """
        logger.info(f"[{self.name}] 开始解析日志 - 芯片型号: {chip_model}, 格式: {log_format}")

        try:
            # 简化版日志解析（不依赖MCP）
            features = self._parse_log_direct(chip_model, raw_log)

            # 标准化处理
            normalized = self._normalize_features(chip_model, features)

            logger.info(f"[{self.name}] 日志解析完成 - 提取到 {len(features.get('error_codes', []))} 个错误码")

            return {
                "success": True,
                "agent": self.name,
                "chip_model": chip_model,
                "log_format": log_format,
                "raw_log": raw_log,
                "parsed_features": features,
                "normalized_features": normalized,
                "parse_timestamp": None
            }

        except Exception as e:
            logger.error(f"[{self.name}] 日志解析失败: {str(e)}")
            return {
                "success": False,
                "agent": self.name,
                "error": str(e),
                "chip_model": chip_model,
                "raw_log": raw_log[:100] + "..." if len(raw_log) > 100 else raw_log
            }

    def _parse_log_direct(self, chip_model: str, raw_log: str) -> Dict[str, Any]:
        """直接解析日志（简化实现）"""
        import re
        from datetime import datetime

        # 提取错误码（0X开头的十六进制）
        error_codes = re.findall(r'0X[0-9A-F]{6}', raw_log, re.IGNORECASE)

        # 提取模块信息
        modules = []
        module_keywords = {
            'CPU': 'cpu', 'CORE': 'cpu',
            'L3_CACHE': 'l3_cache', 'L3': 'l3_cache', 'L3CACHE': 'l3_cache',
            'HA': 'ha', 'HOMEAGENT': 'ha',
            'NOC': 'noc_router', 'ROUTER': 'noc_router',
            'DDR': 'ddr_controller', 'HBM': 'hbm_controller'
        }

        log_upper = raw_log.upper()
        for keyword, module_type in module_keywords.items():
            if keyword in log_upper:
                if module_type not in modules:
                    modules.append(module_type)

        # 提取时间戳
        timestamp = datetime.now().isoformat()

        # 提取故障描述
        fault_description = raw_log[:200] if len(raw_log) > 200 else raw_log

        return {
            "error_codes": error_codes,
            "timestamp": timestamp,
            "modules": modules,
            "fault_description": fault_description,
            "registers": {},
            "metadata": {"chip_model": chip_model}
        }

    def _normalize_features(
        self,
        chip_model: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        标准化提取的特征

        Args:
            chip_model: 芯片型号
            features: 原始特征字典

        Returns:
            标准化后的特征字典
        """

        normalized = {
            "chip_model": chip_model,
            "timestamp": features.get("timestamp"),
            "error_codes": self._normalize_error_codes(features.get("error_codes", [])),
            "registers": self._normalize_registers(features.get("registers", {})),
            "modules": self._normalize_modules(features.get("modules", [])),
            "fault_description": features.get("fault_description", ""),
            "metadata": {}
        }

        # 推断失效域（基于错误码）
        normalized["failure_domain"] = self._infer_failure_domain(features)

        # 推断严重程度
        normalized["severity"] = self._infer_severity(features)

        return normalized

    def _normalize_error_codes(self, error_codes: List[str]) -> List[str]:
        """标准化错误码列表"""
        if not error_codes:
            return []

        # 转换为大写并去重
        normalized = list(set([code.upper().strip() for code in error_codes if code]))
        return sorted(normalized)

    def _normalize_registers(self, registers: Dict) -> Dict:
        """标准化寄存器信息"""
        if not registers:
            return {}

        normalized = {}
        for addr, value in registers.items():
            # 标准化地址格式
            norm_addr = addr.upper().strip()
            if not norm_addr.startswith("0X"):
                norm_addr = "0X" + norm_addr
            normalized[norm_addr] = {
                "address": norm_addr,
                "value": value,
                "type": self._infer_register_type(norm_addr),
                "domain": self._get_register_domain(norm_addr)
            }

        return normalized

    def _normalize_modules(self, modules: List[str]) -> List[str]:
        """标准化模块列表"""
        if not modules:
            return []

        # 统一模块名称格式
        module_mapping = {
            "CPU": "cpu",
            "CORE": "cpu",
            "L3": "l3_cache",
            "L3CACHE": "l3_cache",
            "HA": "ha",
            "HOMEAGENT": "ha",
            "NOC": "noc_router",
            "DDR": "ddr_controller",
            "HBM": "hbm_controller"
        }

        normalized = []
        for module in modules:
            mod_upper = module.upper().strip()
            # 映射到标准类型
            for key, value in module_mapping.items():
                if key in mod_upper:
                    normalized.append(value)
                    break
            else:
                normalized.append(module.lower())

        return sorted(list(set(normalized)))

    def _infer_failure_domain(self, features: Dict) -> str:
        """基于特征推断失效域"""
        error_codes = features.get("error_codes", [])
        modules = features.get("modules", [])

        # 基于错误码前缀判断
        for code in error_codes:
            if code.startswith("0XCO") or "CPU" in code:
                return "compute"
            elif code.startswith("0XLA") or "L3" in code:
                return "cache"
            elif code.startswith("0XHA") or "HA" in code:
                return "interconnect"
            elif code.startswith("0XME") or "DDR" in code.upper():
                return "memory"
            elif code.startswith("0XIO") or "IO" in code.upper():
                return "io"

        # 基于模块判断
        for module in modules:
            if "cpu" in module.lower():
                return "compute"
            elif "cache" in module.lower():
                return "cache"
            elif "ha" in module.lower():
                return "interconnect"
            elif "noc" in module.lower():
                return "interconnect"
            elif "ddr" in module.lower() or "hbm" in module.lower():
                return "memory"

        return "unknown"

    def _infer_severity(self, features: Dict) -> str:
        """推断严重程度"""
        error_codes = features.get("error_codes", [])

        # 基于错误码判断严重程度
        for code in error_codes:
            if code.endswith("FATAL") or "FATAL" in code:
                return "fatal"
            elif code.endswith("ERR") or "ERR" in code:
                return "error"
            elif code.endswith("WARN") or "WARN" in code:
                return "warning"
            elif code.startswith("0X"):
                # 检查错误码高位
                try:
                    code_val = int(code, 16)
                    if code_val >= 0xE0:  # 严重错误
                        return "fatal"
                    elif code_val >= 0xC0:
                        return "error"
                    else:
                        return "warning"
                except ValueError:
                    pass

        return "info"

    def _infer_register_type(self, address: str) -> str:
        """推断寄存器类型"""
        # 根据地址范围推断
        try:
            addr_int = int(address, 16)
        except ValueError:
            return "unknown"

        # SoC地址映射（简化示例）
        if 0x0 <= addr_int < 0x1000:
            return "register"
        elif 0x1000 <= addr_int < 0x2000:
            return "mmio"
        elif 0x1A000000 <= addr_int < 0x1B000000:
            return "ha"
        elif 0x20000000 <= addr_int < 0x30000000:
            return "noc"
        elif 0x40000000 <= addr_int < 0x50000000:
            return "ddr"
        elif 0x80000000 <= addr_int < 0x90000000:
            return "hbm"

        return "unknown"

    def _get_register_domain(self, address: str) -> str:
        """获取寄存器所属域"""
        addr_upper = address.upper()

        # DDR/HBM控制器地址域
        if 0x20000000 <= int(address, 16) < 0x30000000:
            return "memory_controller_ddr"
        elif 0x80000000 <= int(address, 16) < 0x90000000:
            return "memory_controller_hbm"

        # HA地址域
        if 0x1A000000 <= int(address, 16) < 0x1B000000:
            return "ha_agent"

        # NoC地址域
        if 0x20000000 <= int(address, 16) < 0x30000000:
            return "noc_interconnect"

        return "unknown"
