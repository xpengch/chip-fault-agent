"""
上下文管理模块
自动管理 LLM 上下文大小，确保不超过模型限制
"""

from .manager import ContextManager, get_context_manager
from .compressor import LogCompressor
from .conversation import ConversationHistory

__all__ = [
    'ContextManager',
    'get_context_manager',
    'LogCompressor',
    'ConversationHistory'
]
