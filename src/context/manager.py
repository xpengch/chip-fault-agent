"""
上下文管理器 - 核心管理组件
确保发送给 LLM 的内容始终在 64KB 限制内
"""

import re
from typing import Dict, List, Any, Optional
from loguru import logger
from dataclasses import dataclass, field


@dataclass
class ContextBudget:
    """上下文预算配置"""
    # 64KB 限制（中文约能容纳 2 万字符）
    limit_bytes: int = 64 * 1024

    # 预算分配（字节）
    system_prompt: int = 2 * 1024      # 2KB - 系统提示
    compressed_log: int = 35 * 1024    # 35KB - 压缩后的日志
    conversation_history: int = 10 * 1024  # 10KB - 对话历史
    analysis_context: int = 5 * 1024   # 5KB - 分析上下文
    margin: int = 12 * 1024            # 12KB - 安全余量

    def __post_init__(self):
        """验证预算分配"""
        total_allocated = (
            self.system_prompt +
            self.compressed_log +
            self.conversation_history +
            self.analysis_context +
            self.margin
        )
        if total_allocated > self.limit_bytes:
            logger.warning(f"[ContextBudget] 预算超限: {total_allocated} > {self.limit_bytes}")


@dataclass
class ProcessedContext:
    """处理后的上下文"""
    raw_log: str = ""
    compressed_log: str = ""
    conversation_summary: str = ""
    recent_messages: List[Dict] = field(default_factory=list)
    analysis_context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Token 统计
    raw_tokens: int = 0
    compressed_tokens: int = 0
    total_tokens: int = 0

    def to_llm_input(self) -> str:
        """转换为 LLM 输入格式"""
        parts = []

        if self.compressed_log:
            parts.append(f"## 日志信息\n{self.compressed_log}")

        if self.conversation_summary:
            parts.append(f"## 对话历史摘要\n{self.conversation_summary}")

        if self.recent_messages:
            parts.append("## 最近对话")
            for msg in self.recent_messages[-3:]:  # 只保留最近3条
                role = "用户" if msg.get('message_type') in ['user_input', 'correction'] else "系统"
                content = msg.get('content', '')[:200]  # 限制每条消息长度
                parts.append(f"{role}: {content}")

        if self.analysis_context:
            parts.append(f"## 分析上下文\n{self.analysis_context}")

        return "\n\n".join(parts)

    def estimate_size(self) -> int:
        """估算处理后上下文的大小（字节）"""
        content = self.to_llm_input()
        return len(content.encode('utf-8'))

    def estimate_tokens(self) -> int:
        """估算处理后上下文的 token 数量"""
        # 中文：约 1.5 字符 = 1 token
        # 英文：约 4 字符 = 1 token
        content = self.to_llm_input()
        chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        other_chars = len(content) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)


class ContextManager:
    """
    上下文管理器

    职责：
    1. 接收任意大小的输入
    2. 自动压缩到预算范围内
    3. 保证关键信息不丢失
    4. 提供实时大小监控
    """

    def __init__(self, budget: Optional[ContextBudget] = None, settings=None):
        """
        初始化上下文管理器

        Args:
            budget: 上下文预算配置
            settings: 应用配置（用于获取压缩参数）
        """
        self.budget = budget or ContextBudget()
        self._settings = settings

        # 延迟导入子组件
        self._compressor = None
        self._conversation_mgr = None

    @property
    def compressor(self):
        """延迟初始化日志压缩器"""
        if self._compressor is None:
            # 获取配置
            if self._settings is None:
                from src.config.settings import get_settings
                self._settings = get_settings()

            # 根据配置选择压缩器
            if self._settings.CONTEXT_USE_SEMANTIC:
                from .claude_style_compressor import ClaudeStyleCompressor
                self._compressor = ClaudeStyleCompressor(
                    token_budget_manager=self._get_token_manager(),
                    target_tokens=self.budget.compressed_log // 1,  # token 大约是字节的 1/3
                    enable_semantic=True,
                    similarity_threshold=self._settings.CONTEXT_SIMILARITY_THRESHOLD
                )
                logger.info("[ContextManager] 使用 Claude Code 风格语义压缩器")
            else:
                from .compressor import LogCompressor
                self._compressor = LogCompressor(
                    target_size_kb=self.budget.compressed_log // 1024
                )
                logger.info("[ContextManager] 使用规则压缩器")

        return self._compressor

    def _get_token_manager(self):
        """获取 Token 预算管理器"""
        from .token_budget import get_token_budget_manager
        return get_token_budget_manager()

    @property
    def conversation_mgr(self):
        """延迟初始化对话历史管理器"""
        if self._conversation_mgr is None:
            from .conversation import ConversationHistory
            self._conversation_mgr = ConversationHistory(
                max_size_kb=self.budget.conversation_history // 1024,
                max_recent_messages=3
            )
        return self._conversation_mgr

    async def process(
        self,
        raw_log: str = "",
        conversation_messages: List[Dict] = None,
        analysis_result: Dict = None,
        fault_features: Dict = None
    ) -> ProcessedContext:
        """
        处理输入上下文，确保不超出预算

        Args:
            raw_log: 原始日志（可能非常大）
            conversation_messages: 对话消息列表
            analysis_result: 已有的分析结果
            fault_features: 故障特征

        Returns:
            ProcessedContext: 处理后的上下文
        """
        logger.info(f"[ContextManager] 开始处理上下文 - 日志: {len(raw_log)} 字符, 消息: {len(conversation_messages or [])}")

        processed = ProcessedContext()
        processed.raw_log = raw_log

        # 1. 压缩日志
        if raw_log:
            log_result = self.compressor.compress(raw_log, fault_features or {})
            processed.compressed_log = log_result.get("compressed_log", "")
            processed.compressed_tokens = log_result.get("compressed_tokens", 0)
            processed.metadata["log_compression_ratio"] = log_result.get("compression_ratio", 0)
            processed.metadata["log_priority_stats"] = log_result.get("priority_stats", {})
            logger.info(f"[ContextManager] 日志压缩: {len(raw_log)} -> {len(processed.compressed_log)} 字符")

        # 2. 处理对话历史
        if conversation_messages:
            conv_result = self.conversation_mgr.summarize(conversation_messages)
            processed.conversation_summary = conv_result["summary"]
            processed.recent_messages = conv_result["recent_messages"]
            logger.info(f"[ContextManager] 对话摘要: {len(conv_result['summary'])} 字符")

        # 3. 添加分析上下文（如果有）
        if analysis_result:
            processed.analysis_context = self._format_analysis_context(analysis_result)

        # 4. 计算 token 统计
        processed.total_tokens = processed.estimate_tokens()

        # 5. 检查大小并调整
        if processed.total_tokens > (self.budget.limit_bytes // 1):  # 近似 token 比较法
            logger.warning(f"[ContextManager] 仍超限，执行二次压缩")
            processed = self._further_compress(processed)

        logger.info(
            f"[ContextManager] 处理完成 - 总 tokens: {processed.total_tokens}, "
            f"预算: ~{self.budget.limit_bytes // 1} tokens"
        )

        return processed

    def _format_analysis_context(self, analysis_result: Dict) -> str:
        """格式化分析上下文"""
        parts = []

        if "final_root_cause" in analysis_result:
            frc = analysis_result["final_root_cause"]
            parts.append(f"失效域: {frc.get('failure_domain', 'unknown')}")
            parts.append(f"根本原因: {frc.get('root_cause', 'unknown')}")
            parts.append(f"置信度: {frc.get('confidence', 0):.0%}")

        return "\n".join(parts)

    def _further_compress(self, processed: ProcessedContext) -> ProcessedContext:
        """进一步压缩（如果仍超限）"""
        # 使用 token 预算管理器
        token_manager = self._get_token_manager()

        # 计算超出比例
        limit_tokens = self.budget.limit_bytes // 1  # 近似值
        excess_ratio = processed.total_tokens / limit_tokens if processed.total_tokens > 0 else 1

        # 按比例压缩日志（主要占用者）
        if processed.compressed_log and excess_ratio > 1.2:
            lines = processed.compressed_log.split('\n')
            keep_count = int(len(lines) / excess_ratio)
            processed.compressed_log = '\n'.join(lines[:keep_count])
            logger.info(f"[ContextManager] 日志二次压缩: {len(lines)} -> {keep_count} 行")

        # 减少对话消息
        if processed.recent_messages and excess_ratio > 1.1:
            processed.recent_messages = processed.recent_messages[-1:]
            logger.info("[ContextManager] 减少最近消息到 1 条")

        # 重新计算 token
        processed.total_tokens = processed.estimate_tokens()

        # 如果还需要压缩，截断日志
        if processed.total_tokens > limit_tokens:
            max_chars = int(len(processed.compressed_log) / excess_ratio) - 100
            processed.compressed_log = processed.compressed_log[:max_chars]
            processed.total_tokens = processed.estimate_tokens()
            logger.warning(f"[ContextManager] 强制截断到 {max_chars} 字符")

        return processed

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数量

        中文：约 1.5 字符 = 1 token
        英文：约 4 字符 = 1 token
        """
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)

    def check_within_limit(self, text: str) -> Dict[str, Any]:
        """
        检查文本是否在限制内

        Returns:
            {
                "within_limit": bool,
                "size_kb": float,
                "estimated_tokens": int,
                "excess_bytes": int
            }
        """
        size_bytes = len(text.encode('utf-8'))
        size_kb = size_bytes / 1024
        estimated_tokens = self.estimate_tokens(text)

        return {
            "within_limit": size_bytes < self.budget.limit_bytes,
            "size_kb": size_kb,
            "estimated_tokens": estimated_tokens,
            "excess_bytes": max(0, size_bytes - self.budget.limit_bytes)
        }


# 全局单例
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """获取上下文管理器单例"""
    global _context_manager
    if _context_manager is None:
        from src.config.settings import get_settings
        settings = get_settings()

        # 从配置创建预算
        budget = ContextBudget(
            limit_bytes=settings.CONTEXT_LIMIT_KB * 1024,
            compressed_log=settings.CONTEXT_LOG_TARGET_KB * 1024,
            conversation_history=settings.CONTEXT_CONVERSATION_MAX_KB * 1024
        )

        _context_manager = ContextManager(budget, settings=settings)
    return _context_manager


def reset_context_manager():
    """重置上下文管理器（用于测试）"""
    global _context_manager
    _context_manager = None
