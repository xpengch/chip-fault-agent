"""
芯片失效分析AI Agent系统 - 开发工具函数
提供常用的辅助函数
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


def parse_error_codes(log_text: str) -> List[str]:
    """
    从日志文本中解析错误码

    Args:
        log_text: 日志文本

    Returns:
        错误码列表
    """
    error_codes = []

    # 常见错误码格式
    patterns = [
        r'0X[0-9A-F]{4}',  # 0X followed by 4 hex digits
        r'ERROR\s+Code:\s*0X[0-9A-F]{4}',  # ERROR Code: 0X...
        r'\[0X[0-9A-F]{4}\]',  # [0X...] in brackets
        r'0x[0-9a-f]{4}',  # lowercase 0x...
        r'CPU.*0x[0-9a-f]{4}',
        r'L3.*0x[0-9a-f]{4}',
        r'DDR.*0x[0-9a-f]{4}',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, log_text, re.IGNORECASE)
        error_codes.extend(matches)

    # 去重并排序
    error_codes = sorted(list(set(error_codes)), key=lambda x: x.upper())

    return error_codes


def parse_modules(log_text: str) -> List[str]:
    """
    从日志文本中解析涉及的模块

    Args:
        log_text: 日志文本

    Returns:
        模块列表
    """
    modules = []

    # 常见模块模式
    patterns = [
        r'\bcpu\b',
        r'\bcore\b',
        r'\bl3_cache\b|\bl3\b',
        r'\bl2_cache\b|\bl2\b',
        r'\bha\b|\bhome\s+agent\b',
        r'\bhome\s+agent\b',
        r'\bnoc\b',
        r'\bddr\b',
        r'\bhbm\b',
        r'\bmemory\b',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, log_text, re.IGNORECASE)
        modules.extend(matches)

    # 标准化模块名称
    normalized_modules = []
    for module in modules:
        module_lower = module.lower()
        if 'cpu' in module_lower or 'core' in module_lower:
            normalized_modules.append('cpu')
        elif 'l3' in module_lower or 'cache' in module_lower:
            if 'l3' in module_lower:
                normalized_modules.append('l3_cache')
            else:
                normalized_modules.append('l2_cache')
        elif 'ha' in module_lower or 'home' in module_lower:
            normalized_modules.append('ha')
        elif 'noc' in module_lower:
            normalized_modules.append('noc_router')
        elif 'ddr' in module_lower or 'memory' in module_lower:
            if 'ddr' in module_lower:
                normalized_modules.append('ddr_controller')
            else:
                normalized_modules.append('hbm_controller')

    # 去重
    normalized_modules = sorted(list(set(normalized_modules)))

    return normalized_modules


def infer_failure_domain(error_codes: List[str], modules: List[str]) -> Optional[str]:
    """
    基于错误码和模块推断失效域

    Args:
        error_codes: 错误码列表
        modules: 模块列表

    Returns:
        推断的失效域
    """
    # 基于错误码推断
    for code in error_codes:
        code_upper = code.upper()
        if code_upper.startswith('0XCO') or 'CPU' in code_upper:
            return 'compute'
        elif code_upper.startswith('0XLA') or 'L3' in code_upper:
            return 'cache'
        elif code_upper.startswith('0XHA') or 'HA' in code_upper:
            return 'interconnect'
        elif code_upper.startswith('0XME') or 'DDR' in code_upper:
            return 'memory'
        elif code_upper.startswith('0XIO') or 'IO' in code_upper:
            return 'io'

    # 基于模块推断
    for module in modules:
        module_lower = module.lower()
        if 'cpu' in module_lower or 'core' in module_lower:
            return 'compute'
        elif 'l3' in module_lower or 'cache' in module_lower:
            return 'cache'
        elif 'ha' in module_lower or 'home' in module_lower or 'noc' in module_lower:
            return 'interconnect'
        elif 'ddr' in module_lower or 'hbm' in module_lower:
            return 'memory'

    return 'unknown'


def format_timestamp(dt: datetime) -> str:
    """
    格式化时间戳

    Args:
        dt: datetime对象

    Returns:
        格式化的时间字符串
    """
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def truncate_log(log_text: str, max_length: int = 10000) -> str:
    """
    截断日志文本（用于显示预览）

    Args:
        log_text: 原始日志
        max_length: 最大长度

    Returns:
        截断后的日志
    """
    if len(log_text) <= max_length:
        return log_text

    return log_text[:max_length] + '...'


def validate_chip_model(chip_model: str) -> bool:
    """
    验证芯片型号

    Args:
        chip_model: 芯片型号

    Returns:
        是否有效
    """
    # 简单验证：非空且长度合理
    if not chip_model or len(chip_model) < 2:
        return False

    # 芯片型号通常包含XC和数字
    if not re.match(r'^XC\d+', chip_model):
        logger.warning(f"可能的无效芯片型号: {chip_model}")

    return True


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除或替换不安全字符
    unsafe_chars = r'[<>:"/\\|?*]'
    filename = re.sub(unsafe_chars, '_', filename)

    # 移除连续的下划线
    filename = re.sub(r'_+', '_', filename)

    # 确保不以点开头
    if filename.startswith('.'):
        filename = '_' + filename[1:]

    return filename


def calculate_confidence(
    sources: Dict[str, float],
    weights: Dict[str, float]
) -> float:
    """
    计算加权置信度

    Args:
        sources: 各源的置信度
        weights: 各源的权重

    Returns:
        加权置信度
    """
    weighted_sum = 0.0
    weight_sum = 0.0

    for source, confidence in sources.items():
        weight = weights.get(source, 1.0)
        weighted_sum += confidence * weight
        weight_sum += weight

    if weight_sum == 0:
        return 0.0

    return round(weighted_sum / weight_sum, 4)


def format_confidence_percentage(confidence: float) -> str:
    """
    格式化置信度为百分比字符串

    Args:
        confidence: 置信度值

    Returns:
        百分比字符串
    """
    return f"{confidence * 100:.1f}%"


def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    将列表分批

    Args:
        items: 项目列表
        batch_size: 每批大小

    Returns:
        批次列表
    """
    batches = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batches.append(batch)

    return batches
