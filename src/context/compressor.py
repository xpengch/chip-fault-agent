"""
日志压缩器 - 智能压缩日志，保留关键信息
"""

import re
from typing import Dict, List, Any, Set
from loguru import logger


class LogCompressor:
    """
    日志压缩器

    策略：
    1. 提取关键行（错误码、异常、寄存器等）
    2. 时间窗口聚焦（故障前后）
    3. 去重相似日志
    4. 智能截断
    """

    # 关键词模式（优先保留）
    KEYWORD_PATTERNS = [
        r'\bERROR\b', r'\bFAIL\b', r'\bException\b',
        r'\bfault\b', r'\berror\b', r'\bpanic\b',
        r'\b0X[0-9A-F]{4,}\b',  # 错误码如 0XCO01
        r'\bregister\b', r'\breg\b',  # 寄存器
        r'\baddr\b', r'\b0x[0-9a-f]{8,}\b',  # 地址
        r'\bstack\b', r'\btrace\b',  # 栈信息
        r'\btimeout\b', r'\bdeadlock\b',
        r'\bcrash\b', r'\babort\b',
    ]

    # 噪音模式（可丢弃）
    NOISE_PATTERNS = [
        r'^\s*$',  # 空行
        r'^=\s*$',  # 只包含等号
        r'^-\s*$',  # 只包含连字符
        r'^\s*\*\s*$',  # 只包含星号
    ]

    def __init__(
        self,
        target_size_kb: int = 35,
        keep_header_lines: int = 5,
        keep_footer_lines: int = 5
    ):
        """
        初始化日志压缩器

        Args:
            target_size_kb: 目标大小（KB）
            keep_header_lines: 保留头部行数
            keep_footer_lines: 保留尾部行数
        """
        self.target_size_kb = target_size_kb
        self.target_size_bytes = target_size_kb * 1024
        self.keep_header_lines = keep_header_lines
        self.keep_footer_lines = keep_footer_lines

        # 编译正则表达式
        self.keyword_regex = [re.compile(p, re.IGNORECASE) for p in self.KEYWORD_PATTERNS]
        self.noise_regex = [re.compile(p) for p in self.NOISE_PATTERNS]

    def compress(self, raw_log: str, fault_features: Dict = None) -> Dict[str, Any]:
        """
        压缩日志

        Args:
            raw_log: 原始日志
            fault_features: 故障特征（用于指导压缩）

        Returns:
            {
                "compressed_log": str,
                "compression_ratio": float,
                "original_size_kb": float,
                "compressed_size_kb": float,
                "preserved_elements": Dict[str, int]
            }
        """
        if not raw_log:
            return {
                "compressed_log": "",
                "compression_ratio": 0.0,
                "original_size_kb": 0.0,
                "compressed_size_kb": 0.0,
                "preserved_elements": {}
            }

        original_size = len(raw_log.encode('utf-8'))
        original_size_kb = original_size / 1024

        logger.debug(f"[LogCompressor] 开始压缩 - 原始大小: {original_size_kb:.1f} KB")

        # 提取已知错误码
        error_codes = set()
        if fault_features:
            error_codes = set(fault_features.get('error_codes', []))

        # 解析日志
        lines = raw_log.split('\n')
        line_info = self._analyze_lines(lines, error_codes)

        # 分层处理
        key_lines = self._extract_key_lines(lines, line_info)
        context_lines = self._extract_context_lines(lines, line_info)

        # 合并并去重
        combined = self._merge_lines(key_lines, context_lines)

        # 如果仍超限，截断
        compressed = self._truncate_if_needed(combined)

        compressed_size = len(compressed.encode('utf-8'))
        compressed_size_kb = compressed_size / 1024
        compression_ratio = compressed_size / original_size if original_size > 0 else 0

        # 统计保留的元素
        preserved = {
            "error_codes": sum(1 for c in error_codes if c in compressed),
            "error_lines": sum(1 for li in line_info if li.get('is_error') and lines[li['index']] in compressed),
            "register_lines": sum(1 for li in line_info if li.get('has_register') and lines[li['index']] in compressed),
            "total_lines": len(compressed.split('\n'))
        }

        logger.info(
            f"[LogCompressor] 压缩完成: "
            f"{original_size_kb:.1f} KB -> {compressed_size_kb:.1f} KB "
            f"({compression_ratio:.1%})"
        )

        return {
            "compressed_log": compressed,
            "compression_ratio": compression_ratio,
            "original_size_kb": original_size_kb,
            "compressed_size_kb": compressed_size_kb,
            "preserved_elements": preserved
        }

    def _analyze_lines(self, lines: List[str], error_codes: Set[str]) -> List[Dict]:
        """分析每一行的特征"""
        line_info = []

        for idx, line in enumerate(lines):
            info = {
                "index": idx,
                "content": line,
                "is_empty": not line.strip(),
                "is_noise": any(r.search(line) for r in self.noise_regex),
                "has_keyword": any(r.search(line) for r in self.keyword_regex),
                "has_error_code": any(code in line for code in error_codes),
                "is_short": len(line.strip()) < 100,
                "length": len(line),
                "has_timestamp": bool(re.search(r'\d{2}:\d{2}:\d{2}', line)),
                "has_register": bool(re.search(r'register|reg\s*[:=]|0x[0-9a-f]{8,}', line, re.IGNORECASE))
            }
            info["is_error"] = info["has_keyword"] or info["has_error_code"]
            info["priority"] = self._calculate_priority(info)
            line_info.append(info)

        return line_info

    def _calculate_priority(self, info: Dict) -> int:
        """计算行的优先级（越高越重要）"""
        priority = 0

        if info["is_error"]:
            priority += 100
        if info["has_error_code"]:
            priority += 80
        if info["has_register"]:
            priority += 60
        if info["has_keyword"]:
            priority += 40
        if info["has_timestamp"]:
            priority += 20
        if info["is_short"]:
            priority += 10

        # 噪音行降低优先级
        if info["is_noise"]:
            priority -= 50

        return max(0, priority)

    def _extract_key_lines(self, lines: List[str], line_info: List[Dict]) -> List[str]:
        """提取关键行"""
        key_lines = []

        for info in line_info:
            if info["priority"] >= 50:  # 高优先级阈值
                key_lines.append(lines[info["index"]])

        return key_lines

    def _extract_context_lines(self, lines: List[str], line_info: List[Dict]) -> List[str]:
        """提取上下文行（关键行周围的内容）"""
        context_lines = []
        context_window = 2  # 前后各2行

        # 找到高优先级行的索引
        key_indices = [i["index"] for i in line_info if i["priority"] >= 80]

        for idx in key_indices:
            # 添加上下文窗口
            for offset in range(-context_window, context_window + 1):
                target_idx = idx + offset
                if 0 <= target_idx < len(lines):
                    context_lines.append(lines[target_idx])

        return context_lines

    def _merge_lines(self, *line_lists: List[str]) -> List[str]:
        """合并多组行并去重"""
        seen = set()
        merged = []

        for lines in line_lists:
            for line in lines:
                line_hash = hash(line.strip())
                if line_hash not in seen and line.strip():
                    seen.add(line_hash)
                    merged.append(line)

        return merged

    def _truncate_if_needed(self, lines: List[str]) -> str:
        """如果超限则智能截断"""
        if not lines:
            return ""

        result = '\n'.join(lines)
        current_size = len(result.encode('utf-8'))

        if current_size <= self.target_size_bytes:
            return result

        # 计算需要保留的行数
        ratio = self.target_size_bytes / current_size
        total_lines = len(lines)

        # 保留头部和尾部
        header_size = self.keep_header_lines
        footer_size = self.keep_footer_lines
        middle_size = int(total_lines * ratio) - header_size - footer_size

        if middle_size < 0:
            # 太小了，只保留头部
            return '\n'.join(lines[:self.keep_header_lines])

        header = lines[:header_size]
        middle_start = header_size
        middle_end = total_lines - footer_size

        # 从中间均匀采样
        if middle_size < (middle_end - middle_start):
            step = max(1, (middle_end - middle_start) // middle_size)
            middle = lines[middle_start:middle_end:step]
        else:
            middle = lines[middle_start:middle_end]

        footer = lines[-footer_size:] if footer_size > 0 else []

        # 添加省略标记
        truncation_marker = [
            '',
            f'... [省略 {total_lines - len(header) - len(middle) - len(footer)} 行] ...',
            ''
        ]

        return '\n'.join(header + truncation_marker + middle + truncation_marker + footer)

    def compress_conversation_message(self, message: str, max_chars: int = 500) -> str:
        """压缩单条对话消息"""
        if len(message) <= max_chars:
            return message

        # 保留开头和结尾
        head_size = max_chars // 2 - 50
        tail_size = max_chars - head_size - 20

        head = message[:head_size]
        tail = message[-tail_size:]

        return f"{head}\n...[省略]...\n{tail}"
