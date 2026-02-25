"""
Embedding模块
管理embedding模型和生成
"""

from .bge_manager import (
    BGEModelManager,
    bge_model_manager,
    get_bge_model_manager
)

__all__ = [
    "BGEModelManager",
    "bge_model_manager",
    "get_bge_model_manager"
]
