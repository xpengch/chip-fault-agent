"""
芯片失效分析AI Agent系统 - 认证授权包
提供用户认证、授权和RBAC功能
"""

from .service import AuthService, auth_service
from .decorators import require_auth, require_permission, require_role
from .dependencies import get_current_user, get_current_user_id

__all__ = [
    "AuthService",
    "auth_service",
    "require_auth",
    "require_permission",
    "require_role",
    "get_current_user",
    "get_current_user_id"
]
