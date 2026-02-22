"""
芯片失效分析AI Agent系统 - 认证装饰器
提供API端点的认证和授权装饰器
"""

from functools import wraps
from typing import Callable, List, Optional

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database.connection import get_db_manager
from ..database.rbac_models import User
from .service import auth_service


# ============================================
# FastAPI安全方���
# ============================================
security = HTTPBearer(auto_error=False)


# ============================================
# FastAPI依赖注入
# ============================================

async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    从请求中获取当前用户ID

    Args:
        request: FastAPI请求对象
        credentials: HTTP Bearer凭证

    Returns:
        用户ID，未认证返回None
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
            # 存储用户信息到request state
            request.state.user_id = user_id
            request.state.user = user
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


# ============================================
# 认证装饰器（用于FastAPI路由）
# ============================================

def require_auth(func: Callable) -> Callable:
    """
    要求用户认证的装饰器

    Usage:
        @app.get("/api/v1/protected")
        @require_auth
        async def protected_endpoint(current_user: User = Depends(get_current_user)):
            return {"message": "Hello, {}".format(current_user.username)}
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 检查kwargs中是否有current_user
        current_user = kwargs.get('current_user')
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证，请先登录",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return await func(*args, **kwargs)
    return wrapper


def require_permission(permission: str):
    """
    要求特定权限的装饰器

    Args:
        permission: 权限名称，如 "analysis:create"

    Usage:
        @app.post("/api/v1/analysis")
        @require_permission("analysis:create")
        async def create_analysis(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证，请先登录",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # 检查权限
            if not current_user.has_permission(permission):
                logger.warning(f"[Auth] 用户 {current_user.user_id} 尝试访问需要权限 {permission} 的资源")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要权限: {permission}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role: str):
    """
    要求特定角色的装饰器

    Args:
        role: 角色名称，如 "admin", "expert"

    Usage:
        @app.post("/api/v1/admin/users")
        @require_role("admin")
        async def create_user(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证，请先登录",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # 检查角色
            if not current_user.has_role(role):
                logger.warning(f"[Auth] 用户 {current_user.user_id} 尝试访问需要角色 {role} 的资源")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要角色: {role}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """
    要求拥有任一权限的装饰器

    Args:
        *permissions: 权限名称列表

    Usage:
        @app.get("/api/v1/resource")
        @require_any_permission("analysis:read", "analysis:update")
        async def get_resource(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证，请先登录",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # 检查是否拥有任一权限
            has_permission = any(current_user.has_permission(p) for p in permissions)
            if not has_permission:
                logger.warning(f"[Auth] 用户 {current_user.user_id} 尝试访问需要权限之一 {permissions} 的资源")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要以下任一权限: {', '.join(permissions)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_role(*roles: str):
    """
    要求拥有任一角色的装饰器

    Args:
        *roles: 角色名称列表

    Usage:
        @app.get("/api/v1/resource")
        @require_any_role("admin", "expert")
        async def get_resource(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证，请先登录",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # 检查是否拥有任一角色
            has_role = any(current_user.has_role(r) for r in roles)
            if not has_role:
                logger.warning(f"[Auth] 用户 {current_user.user_id} 尝试访问需要角色之一 {roles} 的资源")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要以下任一角色: {', '.join(roles)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_superuser(func: Callable) -> Callable:
    """
    要求超级管理员权限的装饰器

    Usage:
        @app.delete("/api/v1/users/{user_id}")
        @require_superuser
        async def delete_user(current_user: User = Depends(get_current_user)):
            ...
    """
    return require_role("super_admin")(func)


# ============================================
# 可选认证装饰器
# ============================================

def optional_auth(func: Callable) -> Callable:
    """
    可选认证的装饰器
    如果提供了Token则验证，没有提供也不报错

    Usage:
        @app.get("/api/v1/resource")
        @optional_auth
        async def get_resource(current_user: Optional[User] = Depends(get_current_user)):
            if current_user:
                return {"message": "Hello, {}".format(current_user.username)}
            else:
                return {"message": "Hello, anonymous"}
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 不检查认证，直接执行
        return await func(*args, **kwargs)
    return wrapper
