"""
芯片失效分析AI Agent系统 - 认证API路由
提供登录、登出、Token刷新等认证相关端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from loguru import logger

from ..auth.dependencies import get_current_user, get_current_user_required
from ..auth.service import auth_service
from ..database.rbac_models import User, SystemRoles, SystemPermissions
from ..database.connection import get_db_manager


# ============================================
# 路由器
# ============================================
router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


# ============================================
# 请求/响应模型
# ============================================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码", min_length=6)


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新Token")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    password: str = Field(..., description="密码", min_length=6)
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    department: Optional[str] = Field(None, description="部门")
    position: Optional[str] = Field(None, description="职位")


class UserResponse(BaseModel):
    """用户信息响应"""
    user_id: str
    username: str
    email: Optional[str]
    full_name: Optional[str]
    department: Optional[str]
    position: Optional[str]
    is_active: bool
    roles: List[str]
    permissions: List[str]


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse


# ============================================
# API端点
# ============================================

@router.post("/login", response_model=LoginResponse, tags=["认证"])
async def login(
    request: Request,
    login_data: LoginRequest
):
    """
    用户登录

    Args:
        request: FastAPI请求对象
        login_data: 登录数据

    Returns:
        登录成功返回访问Token和用户信息
    """
    # 获取客户端信息
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    # 认证用户
    result = await auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"}
        )

    logger.info(f"[Auth] 用户登录成功: {result['user']['username']}")

    return LoginResponse(**result)


@router.post("/logout", tags=["认证"])
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user_required)
):
    """
    用户登出

    Args:
        request: FastAPI请求对象
        current_user: 当前用户

    Returns:
        登出成功消息
    """
    # 从请求头获取session_id
    session_id = request.headers.get("X-Session-ID")

    if session_id:
        await auth_service.logout_user(session_id)
        logger.info(f"[Auth] 用户登出成功: {current_user.username}")
    else:
        logger.warning(f"[Auth] 用户登出时未提供session_id: {current_user.username}")

    return {"message": "登出成功"}


@router.post("/refresh", response_model=TokenResponse, tags=["认证"])
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    刷新访问Token

    Args:
        refresh_data: 刷新Token数据

    Returns:
        新的访问Token
    """
    result = await auth_service.refresh_access_token(refresh_data.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新Token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    logger.info(f"[Auth] Token刷新成功: {result['user']['username']}")

    return TokenResponse(**result)


@router.get("/me", response_model=UserResponse, tags=["认证"])
async def get_current_user_info(
    current_user: User = Depends(get_current_user_required)
):
    """
    获取当前用户信息

    Args:
        current_user: 当前用户

    Returns:
        用户信息
    """
    # 获取用户权限列表
    permissions = []
    for role in current_user.roles:
        if role.is_active:
            for permission in role.permissions:
                if permission.is_active:
                    permissions.append(permission.name)

    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        department=current_user.department,
        position=current_user.position,
        is_active=current_user.is_active,
        roles=[role.name for role in current_user.roles if role.is_active],
        permissions=permissions
    )


@router.post("/register", response_model=UserResponse, tags=["认证"])
async def register(
    register_data: RegisterRequest,
    request: Request
):
    """
    用户注册（仅限开发环境，生产环境应禁用）

    Args:
        register_data: 注册数据
        request: FastAPI请求对象

    Returns:
        注册成功的用户信息
    """
    # TODO: 生产环境应禁用注册功能或需要管理员审批

    ip_address = request.client.host if request.client else "unknown"

    # 创建用户（默认分配viewer角色）
    user = await auth_service.create_user(
        username=register_data.username,
        password=register_data.password,
        email=register_data.email,
        full_name=register_data.full_name,
        department=register_data.department,
        position=register_data.position,
        role_names=[SystemRoles.VIEWER],  # 默认分配viewer角色
        created_by="system"
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )

    logger.info(f"[Auth] 用户注册成功: {user.username} from {ip_address}")

    # 获取用户权限列表
    permissions = []
    for role in user.roles:
        if role.is_active:
            for permission in role.permissions:
                if permission.is_active:
                    permissions.append(permission.name)

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        department=user.department,
        position=user.position,
        is_active=user.is_active,
        roles=[role.name for role in user.roles if role.is_active],
        permissions=permissions
    )


@router.post("/change-password", tags=["认证"])
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user_required)
):
    """
    修改密码

    Args:
        old_password: 旧密码
        new_password: 新密码
        current_user: 当前用户

    Returns:
        修改成功消息
    """
    # 验证旧密码
    if not auth_service.verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    # 更新密码
    from ..auth.service import AuthService
    current_user.password_hash = AuthService.hash_password(new_password)
    current_user.password_changed_at = datetime.utcnow()
    current_user.must_change_password = False

    # 保存到数据库
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        session.add(current_user)
        await session.commit()

    logger.info(f"[Auth] 用户修改密码成功: {current_user.username}")

    return {"message": "密码修改成功"}


# ============================================
# OAuth2兼容端点（用于Swagger UI）
# ============================================

@router.post("/token", response_model=LoginResponse, tags=["认证"])
async def login_oauth2(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2兼容登录端点（用于Swagger UI）

    Args:
        request: FastAPI请求对象
        form_data: OAuth2表单数据

    Returns:
        登录成功返回访问Token和用户信息
    """
    # 获取客户端信息
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    # 认证用户
    result = await auth_service.authenticate_user(
        username=form_data.username,
        password=form_data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"}
        )

    logger.info(f"[Auth] 用户登录成功 (OAuth2): {result['user']['username']}")

    return LoginResponse(**result)
