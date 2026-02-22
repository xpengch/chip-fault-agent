"""
芯片失效分析AI Agent系统 - 认证依赖注入
提供FastAPI依赖注入函数
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from loguru import logger

from ..database.connection import get_db_manager
from ..database.rbac_models import User
from .service import auth_service


# ============================================
# FastAPI安全方案
# ============================================
security = HTTPBearer(auto_error=False)


# ============================================
# 依赖注入函数
# ============================================

async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    从Token中获取当前用户ID

    Args:
        credentials: HTTP Bearer凭证

    Returns:
        用户ID，未认证或Token无效返回None
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = auth_service.decode_token(token)

    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # 验证用户是否存在且激活
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        stmt = select(User).where(
            User.user_id == user_id,
            User.is_active == True
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            return user_id

    return None


async def get_current_user(
    current_user_id: Optional[str] = Depends(get_current_user_id)
) -> Optional[User]:
    """
    获取当前用户对象

    Args:
        current_user_id: 当前用户ID

    Returns:
        用户对象，未认证返回None
    """
    if not current_user_id:
        return None

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        stmt = select(User).where(User.user_id == current_user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_current_user_required(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    获取当前用户对象（必需认证）

    Args:
        current_user: 当前用户

    Returns:
        用户对象

    Raises:
        HTTPException: 未认证时抛出401错误
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证，请先登录",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user_required)
) -> User:
    """
    获取当前超级管理员用户

    Args:
        current_user: 当前用户

    Returns:
        超级管理员用户对象

    Raises:
        HTTPException: 不是超级管理员时抛出403错误
    """
    from ..database.rbac_models import SystemRoles

    if not current_user.has_role(SystemRoles.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要超级管理员权限"
        )
    return current_user
