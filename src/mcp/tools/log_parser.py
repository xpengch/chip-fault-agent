"""
芯片失效分析AI Agent系统 - 日志解析MCP工具
支持多种日志格式的解析
"""

from typing import Dict, List, Any, Optional
import json
import re
from datetime import datetime


class LogParserTool:
    """日志解析工具类"""

    def __init__(self):
        """初始化日志解析器"""
        # 预编译正则表达式
        self._compile_patterns()

    def _compile_patterns(self):
        """编译常用的日志解析正则表达式"""

        # JSON日志格式
        self.json_pattern = re.compile(r'^\s*\{.*\}\s*$')

        # 错误码格式（支持16进制）
        self.error_code_pattern = re.compile(
            r'0x[0-9A-Fa-f]+|ERR_[A-Z0-9_]+'
        )

        # 寄存器地址格式
        self.register_pattern = re.compile(
            r'(?:register|reg|addr)\s*[:=]\s*(0x[0-9A-Fa-f]+|\w+)',
            re.IGNORECASE
        )

        # 时间戳格式
        self.timestamp_patterns = [
            # ISO格式：2024-01-01 12:00:00
            re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'),
            # 简单格式：01-01 12:00:00
            re.compile(r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'),
            # 时间戳格式：[12:00:00]
            re.compile(r'\[\d{2}:\d{2}:\d{2}\]'),
        ]

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
            解析后的标准化故障特征
        """

        # 自动检测日志格式
        if log_format == "auto":
            log_format = self._detect_format(raw_log)

        # 根据格式进行解析
        if log_format == "json":
            features = self._parse_json_log(raw_log)
        elif log_format == "csv":
            features = self._parse_csv_log(raw_log)
        else:
            features = self._parse_text_log(raw_log)

        # 标准化处理
        features = self._normalize_features(chip_model, features)

        return {
            "chip_model": chip_model,
            "log_format": log_format,
            "parsed_features": features,
            "parse_timestamp": datetime.now().isoformat()
        }

    def _detect_format(self, log_content: str) -> str:
        """自动检测日志格式"""

        # 尝试JSON解析
        if self.json_pattern.match(log_content.strip()):
            return "json"

        # 检测CSV分隔符
        if ',' in log_content and '\t' not in log_content:
            return "csv"

        # 默认为文本格式
        return "text"

    def _parse_json_log(self, log_content: str) -> Dict[str, Any]:
        """解析JSON格式日志"""

        try:
            data = json.loads(log_content)
            return {
                "format": "json",
                "fields": data,
                "error_codes": self._extract_error_codes(json.dumps(data)),
                "registers": self._extract_registers(json.dumps(data)),
                "has_timestamp": any(k in data for k in ['timestamp', 'time', 'datetime'])
            }
        except json.JSONDecodeError:
            # 如果不是完整JSON，尝试提取JSON片段
            return self._parse_text_log(log_content)

    def _parse_csv_log(self, log_content: str) -> Dict[str, Any]:
        """解析CSV格式日志"""

        lines = log_content.strip().split('\n')
        if not lines:
            return {"format": "csv", "fields": {}, "error_codes": []}

        # 解析CSV头部
        headers = [h.strip() for h in lines[0].split(',')]
        rows = []

        for line in lines[1:]:
            values = line.split(',')
            if len(values) == len(headers):
                row = dict(zip(headers, [v.strip() for v in values]))
                rows.append(row)

        return {
            "format": "csv",
            "fields": {"headers": headers, "rows": rows},
            "error_codes": self._extract_error_codes(log_content)
        }

    def _parse_text_log(self, log_content: str) -> Dict[str, Any]:
        """解析纯文本格式日志"""

        lines = log_content.strip().split('\n')

        # 提取关键信息
        error_codes = self._extract_error_codes(log_content)
        registers = self._extract_registers(log_content)
        timestamps = self._extract_timestamps(log_content)

        # 提取故障描述
        fault_description = self._extract_fault_description(lines)

        return {
            "format": "text",
            "lines": lines,
            "line_count": len(lines),
            "error_codes": error_codes,
            "registers": registers,
            "timestamps": timestamps,
            "fault_description": fault_description
        }

    def _extract_error_codes(self, text: str) -> List[str]:
        """提取错误码"""
        matches = self.error_code_pattern.findall(text)
        return list(set(matches))  # 去重

    def _extract_registers(self, text: str) -> List[str]:
        """提取寄存器信息"""
        matches = self.register_pattern.findall(text)
        return [f"{m[0]}={m[1]}" for m in matches]

    def _extract_timestamps(self, text: str) -> List[str]:
        """提取时间戳"""
        timestamps = []
        for pattern in self.timestamp_patterns:
            matches = pattern.findall(text)
            timestamps.extend(matches)
        return list(set(timestamps))

    def _extract_fault_description(self, lines: List[str]) -> str:
        """提取故障描述"""

        # 查找包含关键词的行
        fault_keywords = ['error', 'fail', 'fault', 'exception', 'timeout', 'hang', 'crash']
        description_lines = []

        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in fault_keywords):
                description_lines.append(line.strip())

        return ' | '.join(description_lines[:5])  # 最多5行

    def _normalize_features(
        self,
        chip_model: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """标准化提取的特征"""

        normalized = {
            "chip_model": chip_model,
            "timestamp": datetime.now().isoformat(),
            "error_codes": [],
            "registers": {},
            "modules": [],
            "severity": "unknown",
            "domain": "unknown"
        }

        # 标准化错误码
        if "error_codes" in features:
            normalized["error_codes"] = features["error_codes"]

        # 标准化寄存器
        if "registers" in features:
            normalized["registers"] = features["registers"]

        # 推断失效域
        normalized["domain"] = self._infer_domain(features)

        # 推断严重程度
        normalized["severity"] = self._infer_severity(features)

        return normalized

    def _infer_domain(self, features: Dict[str, Any]) -> str:
        """根据特征推断失效域"""

        error_codes = features.get("error_codes", [])

        # 基于错误码前缀判断
        for code in error_codes:
            if code.startswith('MEM_') or 'DDR' in code or 'HBM' in code:
                return "memory"
            elif code.startswith('CPU_') or 'CORE' in code:
                return "compute"
            elif code.startswith('NOC_') or 'ROUTER' in code:
                return "interconnect"
            elif code.startswith('HA_'):
                return "coherence"
            elif code.startswith('CACHE_') or 'L3' in code:
                return "cache"

        return "unknown"

    def _infer_severity(self, features: Dict[str, Any]) -> str:
        """推断严重程度"""

        error_codes = features.get("error_codes", [])

        # 根据错误码判断严重性
        for code in error_codes:
            if 'FATAL' in code or 'CRIT' in code:
                return "critical"
            elif 'ERR' in code:
                return "error"
            elif 'WARN' in code:
                return "warning"

        return "info"
