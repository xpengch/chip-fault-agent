"""
对话历史管理器 - 压缩和管理多轮对话历史
"""

import re
from typing import Dict, List, Any, Set
from datetime import datetime
from loguru import logger


class ConversationHistory:
    """
    对话历史管理器

    策略：
    1. 保留最近 N 条完整消息
    2. 历史消息摘要为关键信息
    3. 去除重复和噪音
    4. 滚动窗口管理
    """

    def __init__(
        self,
        max_size_kb: int = 10,
        max_recent_messages: int = 3,
        summary_max_messages: int = 20
    ):
        """
        初始化对话历史管理器

        Args:
            max_size_kb: 最大大小（KB）
            max_recent_messages: 保留的最近完整消息数
            summary_max_messages: 参与摘要的最大消息数
        """
        self.max_size_kb = max_size_kb
        self.max_size_bytes = max_size_kb * 1024
        self.max_recent_messages = max_recent_messages
        self.summary_max_messages = summary_max_messages

    def summarize(self, messages: List[Dict]) -> Dict[str, Any]:
        """
        摘要对话历史

        Args:
            messages: 对话消息列表

        Returns:
            {
                "summary": str,
                "recent_messages": List[Dict],
                "metadata": Dict
            }
        """
        if not messages:
            return {
                "summary": "",
                "recent_messages": [],
                "metadata": {"total_messages": 0}
            }

        total_count = len(messages)

        # 如果消息数量不多，全部保留
        if total_count <= self.max_recent_messages:
            return {
                "summary": "",
                "recent_messages": self._normalize_messages(messages),
                "metadata": {"total_messages": total_count, "all_preserved": True}
            }

        # 分离历史消息和最近消息
        recent_messages = messages[-self.max_recent_messages:]
        history_messages = messages[:-self.max_recent_messages]

        # 生成摘要
        summary = self._generate_summary(history_messages)

        logger.debug(
            f"[ConversationHistory] 摘要完成: "
            f"{len(history_messages)} 条历史 -> {len(summary)} 字符, "
            f"保留 {len(recent_messages)} 条最近消息"
        )

        return {
            "summary": summary,
            "recent_messages": self._normalize_messages(recent_messages),
            "metadata": {
                "total_messages": total_count,
                "summarized_count": len(history_messages),
                "preserved_count": len(recent_messages)
            }
        }

    def _normalize_messages(self, messages: List[Dict]) -> List[Dict]:
        """标准化消息格式"""
        normalized = []

        for msg in messages:
            # 处理字典格式的消息
            if isinstance(msg, dict):
                normalized.append({
                    "message_id": msg.get("message_id"),
                    "message_type": msg.get("message_type", "user_input"),
                    "sequence_number": msg.get("sequence_number"),
                    "content": self._compress_message_content(msg.get("content", "")),
                    "is_correction": msg.get("is_correction", False)
                })

        return normalized

    def _compress_message_content(self, content: str, max_chars: int = 300) -> str:
        """压缩消息内容"""
        if len(content) <= max_chars:
            return content

        # 保留开头和结尾
        head = content[:max_chars//2 - 20]
        tail = content[-(max_chars - len(head) - 20):]

        return f"{head}\n...[省略]...\n{tail}"

    def _generate_summary(self, messages: List[Dict]) -> str:
        """生成历史对话摘要"""
        summary_parts = []

        # 提取关键信息
        error_codes: Set[str] = set()
        modules: Set[str] = set()
        failure_domains: Set[str] = set()
        user_input_count = 0
        correction_count = 0

        # 限制处理的消息数量
        process_messages = messages[-self.summary_max_messages:]

        for msg in process_messages:
            msg_type = msg.get("message_type", "")
            content = msg.get("content", "")

            if msg_type in ["user_input", "correction"]:
                if msg_type == "user_input":
                    user_input_count += 1
                else:
                    correction_count += 1

                # 提取错误码
                codes = re.findall(r'0X[0-9A-F]+', content, re.IGNORECASE)
                error_codes.update(codes)

                # 提取模块（简化）
                if "cpu" in content.lower():
                    modules.add("CPU")
                if "cache" in content.lower() or "l3" in content.lower():
                    modules.add("L3_Cache")
                if "ddr" in content.lower() or "memory" in content.lower():
                    modules.add("DDR")
                if "ha" in content.lower():
                    modules.add("HA")

        # 构建摘要
        if error_codes:
            codes_str = ", ".join(sorted(list(error_codes))[:10])  # 最多10个
            summary_parts.append(f"历史错误码: {codes_str}")

        if modules:
            modules_str = ", ".join(sorted(list(modules)))
            summary_parts.append(f"涉及模块: {modules_str}")

        if user_input_count > 0:
            summary_parts.append(f"用户输入次数: {user_input_count}")

        if correction_count > 0:
            summary_parts.append(f"纠正次数: {correction_count}")

        if not summary_parts:
            return f"[历史对话: {len(messages)} 条消息已压缩]"

        return "\n".join(summary_parts)

    def add_message(
        self,
        messages: List[Dict],
        new_message: Dict,
        max_total_messages: int = 100
    ) -> List[Dict]:
        """
        添加新消息到对话历史

        Args:
            messages: 现有消息列表
            new_message: 新消息
            max_total_messages: 最大总消息数

        Returns:
            更新后的消息列表
        """
        updated = messages.copy()

        # 添加新消息
        updated.append(new_message)

        # 如果超过最大数量，移除最旧的
        if len(updated) > max_total_messages:
            # 保留最近的消息
            updated = updated[-max_total_messages:]
            logger.debug(f"[ConversationHistory] 消息数量超限，保留最近 {max_total_messages} 条")

        return updated

    def get_conversation_for_llm(
        self,
        messages: List[Dict],
        include_summary: bool = True
    ) -> str:
        """
        获取用于 LLM 的对话历史文本

        Args:
            messages: 消息列表
            include_summary: 是否包含摘要

        Returns:
            格式化的对话历史文本
        """
        if not messages:
            return ""

        result = self.summarize(messages)

        parts = []
        if include_summary and result["summary"]:
            parts.append(f"对话历史摘要:\n{result['summary']}")

        if result["recent_messages"]:
            parts.append("\n最近对话:")
            for msg in result["recent_messages"]:
                msg_type = msg.get("message_type", "")
                content = msg.get("content", "")

                if msg_type == "user_input":
                    parts.append(f"用户: {content}")
                elif msg_type == "system_response":
                    parts.append(f"系统: {content[:200]}")  # 限制系统响应长度
                elif msg_type == "correction":
                    parts.append(f"纠正: {content}")

        return "\n\n".join(parts)

    def estimate_size(self, messages: List[Dict]) -> int:
        """估算对话历史的大小（字节）"""
        total = 0

        for msg in messages:
            content = msg.get("content", "")
            total += len(content.encode('utf-8'))

        return total

    def is_within_limit(self, messages: List[Dict]) -> bool:
        """检查对话历史是否在限制内"""
        size = self.estimate_size(messages)
        return size < self.max_size_bytes
