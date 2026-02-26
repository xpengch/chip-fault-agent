"""
Token 预算管理器 - 参考 Claude Code 的上下文管理方式
使用 token 计数而不是字节数来精确管理上下文
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import IntEnum
from loguru import logger


class Priority(IntEnum):
    """内容优先级（参考 Claude Code）"""
    CRITICAL = 100    # 关键内容：错误码、异常、根因分析
    HIGH = 75         # 高优先级：系统响应、分析结果
    MEDIUM = 50       # 中优先级：用户输入、推理过程
    LOW = 25          # 低优先级：普通日志、调试信息
    MINIMAL = 10      # 最低优先级：噪音、分隔符


@dataclass
class ContextToken:
    """上下文 Token 单元"""
    content: str
    token_count: int
    priority: Priority
    source_type: str  # "log", "conversation", "system", "analysis"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """验证 token 计数"""
        if self.token_count <= 0:
            # 自动估算
            self.token_count = self._estimate_tokens()

    def _estimate_tokens(self) -> int:
        """估算 token 数量"""
        # 中文：约 1.5 字符 = 1 token
        # 英文：约 4 字符 = 1 token
        chinese_chars = sum(1 for c in self.content if '\u4e00' <= c <= '\u9fff')
        other_chars = len(self.content) - chinese_chars
        return max(1, int(chinese_chars / 1.5 + other_chars / 4))


@dataclass
class TokenBudget:
    """Token 预算配置"""
    total_limit: int = 32000      # 64KB ≈ 32K tokens (保守估计)
    system_prompt: int = 1500     # 系统提示
    compressed_log: int = 18000   # 压缩后的日志
    conversation: int = 6000      # 对话历史
    analysis_result: int = 4000   # 分析结果
    margin: int = 2500            # 安全余量

    def __post_init__(self):
        """验证预算分配"""
        total = (
            self.system_prompt +
            self.compressed_log +
            self.conversation +
            self.analysis_result +
            self.margin
        )
        if total > self.total_limit:
            logger.warning(f"[TokenBudget] 预算超限: {total} > {self.total_limit}")

    def get_category_limit(self, category: str) -> int:
        """获取特定类别的预算限制"""
        limits = {
            "system": self.system_prompt,
            "log": self.compressed_log,
            "conversation": self.conversation,
            "analysis": self.analysis_result
        }
        return limits.get(category, 1000)


class TokenBudgetManager:
    """
    Token 预算管理器

    参考 Claude Code 的实现方式：
    1. 基于 token 计数而不是字节数
    2. 优先级系统确保重要内容优先
    3. 智能截断保留最大信息密度
    """

    def __init__(self, budget: Optional[TokenBudget] = None):
        """
        初始化 Token 预算管理器

        Args:
            budget: Token 预算配置
        """
        self.budget = budget or TokenBudget()
        self.allocated_tokens: Dict[str, int] = {
            "system": 0,
            "log": 0,
            "conversation": 0,
            "analysis": 0
        }

    def calculate_tokens(self, text: str) -> int:
        """
        计算文本的 token 数量

        Args:
            text: 输入文本

        Returns:
            token 数量
        """
        # 中文：约 1.5 字符 = 1 token
        # 英文：约 4 字符 = 1 token
        # 更精确的估算
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars

        # 中文字符通常每个占 2-3 字节，对应 1-1.5 token
        # 英文字符约 4 个字符对应 1 token
        tokens = chinese_chars / 1.5 + other_chars / 4

        return int(tokens) + 1  # 至少 1 token

    def estimate_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        估算消息列表的 token 总数

        Args:
            messages: 消息列表，格式为 [{"role": "...", "content": "..."}, ...]

        Returns:
            总 token 数
        """
        total = 0
        for msg in messages:
            # 每条消息有一些元数据开销
            total += 4  # role, content 等字段的开销
            total += self.calculate_tokens(msg.get("content", ""))
            total += self.calculate_tokens(msg.get("role", ""))
        return total

    def can_fit(
        self,
        content: str,
        category: str = "log",
        priority: Priority = Priority.MEDIUM
    ) -> bool:
        """
        检查内容是否可以放入预算

        Args:
            content: 要添加的内容
            category: 内容类别 ("log", "conversation", "analysis", "system")
            priority: 优先级

        Returns:
            是否可以放入
        """
        tokens = self.calculate_tokens(content)
        limit = self.budget.get_category_limit(category)

        # 检查当前类别是否有空间
        current_used = self.allocated_tokens.get(category, 0)

        # 高优先级内容可以超出预算
        if priority >= Priority.HIGH:
            # 检查总预算
            total_used = sum(self.allocated_tokens.values())
            return (total_used + tokens) <= (self.budget.total_limit - self.budget.margin)

        # 普通（低优先级）内容严格按类别预算
        return (current_used + tokens) <= limit

    def allocate(
        self,
        content: str,
        category: str = "log",
        priority: Priority = Priority.MEDIUM,
        source_type: str = "",
        metadata: Dict[str, Any] = None
    ) -> ContextToken:
        """
        分配 token 预算

        Args:
            content: 内容
            category: 类别
            priority: 优先级
            source_type: 源类型
            metadata: 元数据

        Returns:
            ContextToken 对象
        """
        tokens = self.calculate_tokens(content)

        return ContextToken(
            content=content,
            token_count=tokens,
            priority=priority,
            source_type=source_type,
            metadata=metadata or {}
        )

    def prioritize_content(
        self,
        contents: List[ContextToken]
    ) -> List[ContextToken]:
        """
        按优先级排序内容，并返回可以放入预算的内容列表

        Args:
            contents: 所有候选内容

        Returns:
            可以放入的内容列表（按优先级排序）
        """
        # 按优先级排序
        sorted_contents = sorted(contents, key=lambda x: x.priority, reverse=True)

        result = []
        total_used = 0
        category_used: Dict[str, int] = {cat: 0 for cat in self.allocated_tokens}

        for content_token in sorted_contents:
            category = content_token.source_type
            tokens = content_token.token_count
            limit = self.budget.get_category_limit(category)

            # 检查是否可以添加
            can_add = False

            if content_token.priority >= Priority.HIGH:
                # 高优先级：检查总预算
                if (total_used + tokens) <= (self.budget.total_limit - self.budget.margin):
                    can_add = True
            else:
                # 普通优先级：检查类别预算
                if (category_used[category] + tokens) <= limit:
                    can_add = True

            if can_add:
                result.append(content_token)
                total_used += tokens
                category_used[category] += tokens

        logger.info(
            f"[TokenBudgetManager] 预算分配完成: "
            f"总使用 {total_used}/{self.budget.total_limit} tokens, "
            f"选择 {len(result)}/{len(contents)} 项内容"
        )

        return result

    def get_remaining_budget(self, category: str = "") -> Dict[str, int]:
        """
        获取剩余预算

        Args:
            category: 特定类别（空字符串表示所有类别）

        Returns:
            剩余预算信息
        """
        if category:
            limit = self.budget.get_category_limit(category)
            used = self.allocated_tokens.get(category, 0)
            return {
                "category": category,
                "limit": limit,
                "used": used,
                "remaining": max(0, limit - used)
            }
        else:
            return {
                cat: self.get_remaining_budget(cat)
                for cat in ["system", "log", "conversation", "analysis"]
            }

    def format_context_size(self, content: str) -> str:
        """
        格式化上下文大小为人类可读形式

        Args:
            content: 内容文本

        Returns:
            格式化的大小字符串
        """
        tokens = self.calculate_tokens(content)
        chars = len(content)
        bytes_size = len(content.encode('utf-8'))
        kb_size = bytes_size / 1024

        return f"{tokens:,} tokens / {chars:,} chars / {kb_size:.1f} KB"


# 全局单例
_token_budget_manager: Optional[TokenBudgetManager] = None


def get_token_budget_manager() -> TokenBudgetManager:
    """获取 Token 预算管理器单例"""
    global _token_budget_manager
    if _token_budget_manager is None:
        _token_budget_manager = TokenBudgetManager()
    return _token_budget_manager


def reset_token_budget_manager():
    """重置 Token 预算管理器（用于测试）"""
    global _token_budget_manager
    _token_budget_manager = None
