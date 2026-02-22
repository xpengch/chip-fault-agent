"""
芯片失效分析AI Agent系统 - 管理员API路由
提供用户管理、角色管理、权限管理等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from loguru import logger
from sqlalchemy import select, or_

from ..auth.dependencies import get_current_user_required, get_current_superuser
from ..auth.service import auth_service
from ..database.rbac_models import (
    User, Role, Permission, SystemRoles, SystemPermissions
)
from ..database.connection import get_db_manager


# ============================================
# 路由器
# ============================================
router = APIRouter(prefix="/api/v1/admin", tags=["管理员"])


# ============================================
# 请求/响应模型
# ============================================

class CreateUserRequest(BaseModel):
    """创建用户请求"""
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    password: str = Field(..., description="密码", min_length=6)
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="全名")
    department: Optional[str] = Field(None, description="部门")
    position: Optional[str] = Field(None, description="职位")
    roles: Optional[List[str]] = Field(None, description="角色列表")
    is_active: Optional[bool] = Field(True, description="是否激活")


class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None


class AssignRolesRequest(BaseModel):
    """分配角色请求"""
    roles: List[str] = Field(..., description="角色列表")


class CreateRoleRequest(BaseModel):
    """创建角色请求"""
    name: str = Field(..., description="角色名称", min_length=3, max_length=50)
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    permissions: Optional[List[str]] = Field(None, description="权限列表")


class UpdateRoleRequest(BaseModel):
    """更新角色请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AssignPermissionsRequest(BaseModel):
    """分配权限请求"""
    permissions: List[str] = Field(..., description="权限列表")


class UserListItem(BaseModel):
    """用户列表项"""
    user_id: str
    username: str
    email: Optional[str]
    full_name: Optional[str]
    department: Optional[str]
    position: Optional[str]
    is_active: bool
    is_verified: bool
    roles: List[str]
    created_at: datetime


class RoleListItem(BaseModel):
    """角色列表项"""
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    is_active: bool
    is_system_role: bool
    level: int
    user_count: int


class PermissionListItem(BaseModel):
    """权限列表项"""
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    resource: str
    action: str
    scope: Optional[str]
    is_active: bool


# ============================================
# 用户管理端点
# ============================================

@router.get("/users", response_model=List[UserListItem], tags=["管理员"])
async def list_users(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_user_required)
):
    """
    获取用户列表

    需要权限: user:read
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.USER_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: user:read"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        # 构建查询
        stmt = select(User)

        if search:
            stmt = stmt.where(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )

        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        users = result.scalars().all()

        # 构建响应
        user_list = []
        for user in users:
            user_list.append(UserListItem(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                department=user.department,
                position=user.position,
                is_active=user.is_active,
                is_verified=user.is_verified,
                roles=[role.name for role in user.roles if role.is_active],
                created_at=user.created_at
            ))

        return user_list


@router.get("/users/{user_id}", response_model=UserListItem, tags=["管理员"])
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user_required)
):
    """
    获取用户详情

    需要权限: user:read
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.USER_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: user:read"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return UserListItem(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            position=user.position,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=[role.name for role in user.roles if role.is_active],
            created_at=user.created_at
        )


@router.post("/users", response_model=UserListItem, tags=["管理员"])
async def create_user(
    user_data: CreateUserRequest,
    current_user: User = Depends(get_current_user_required)
):
    """
    创建用户

    需要权限: user:create
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.USER_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: user:create"
        )

    # 创建用户
    user = await auth_service.create_user(
        username=user_data.username,
        password=user_data.password,
        email=user_data.email,
        full_name=user_data.full_name,
        department=user_data.department,
        position=user_data.position,
        role_names=user_data.roles or [SystemRoles.VIEWER],
        created_by=current_user.user_id
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )

    logger.info(f"[Admin] 用户创建成功: {user.username} by {current_user.username}")

    return UserListItem(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        department=user.department,
        position=user.position,
        is_active=user.is_active,
        is_verified=user.is_verified,
        roles=[role.name for role in user.roles if role.is_active],
        created_at=user.created_at
    )


@router.put("/users/{user_id}", response_model=UserListItem, tags=["管理员"])
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user_required)
):
    """
    更新用户信息

    需要权限: user:update
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.USER_UPDATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: user:update"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 更新字段
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.department is not None:
            user.department = user_data.department
        if user_data.position is not None:
            user.position = user_data.position
        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        await session.commit()
        await session.refresh(user)

        logger.info(f"[Admin] 用户更新成功: {user.username} by {current_user.username}")

        return UserListItem(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            department=user.department,
            position=user.position,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=[role.name for role in user.roles if role.is_active],
            created_at=user.created_at
        )


@router.delete("/users/{user_id}", tags=["管理员"])
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user_required)
):
    """
    删除用户（软删除，仅禁用）

    需要权限: user:delete
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.USER_DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: user:delete"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 软删除：禁用用户
        user.is_active = False
        await session.commit()

        logger.info(f"[Admin] 用户删除成功: {user.username} by {current_user.username}")

        return {"message": "用户删除成功"}


@router.post("/users/{user_id}/roles", tags=["管理员"])
async def assign_user_roles(
    user_id: str,
    role_data: AssignRolesRequest,
    current_user: User = Depends(get_current_user_required)
):
    """
    分配用户角色

    需要权限: user:update
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.USER_UPDATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: user:update"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        # 查询用户
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 清除现有角色
        user.roles.clear()

        # 分配新角色
        for role_name in role_data.roles:
            stmt = select(Role).where(Role.name == role_name)
            result = await session.execute(stmt)
            role = result.scalar_one_or_none()
            if role:
                user.roles.append(role)

        await session.commit()

        logger.info(f"[Admin] 用户角色分配成功: {user.username} -> {role_data.roles} by {current_user.username}")

        return {"message": "角色分配成功", "roles": role_data.roles}


# ============================================
# 角色管理端点
# ============================================

@router.get("/roles", response_model=List[RoleListItem], tags=["管理员"])
async def list_roles(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    current_user: User = Depends(get_current_user_required)
):
    """
    获取角色列表

    需要权限: role:read
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.ROLE_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: role:read"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        stmt = select(Role).offset(skip).limit(limit)
        result = await session.execute(stmt)
        roles = result.scalars().all()

        # 构建响应
        role_list = []
        for role in roles:
            # 计算用户数量
            user_count = len([u for u in role.users if u.is_active])

            role_list.append(RoleListItem(
                id=role.id,
                name=role.name,
                display_name=role.display_name,
                description=role.description,
                is_active=role.is_active,
                is_system_role=role.is_system_role,
                level=role.level,
                user_count=user_count
            ))

        return role_list


@router.get("/roles/{role_id}", response_model=RoleListItem, tags=["管理员"])
async def get_role(
    role_id: UUID,
    current_user: User = Depends(get_current_user_required)
):
    """
    获取角色详情

    需要权限: role:read
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.ROLE_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: role:read"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )

        # 计算用户数量
        user_count = len([u for u in role.users if u.is_active])

        return RoleListItem(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            is_active=role.is_active,
            is_system_role=role.is_system_role,
            level=role.level,
            user_count=user_count
        )


@router.post("/roles", response_model=RoleListItem, tags=["管理员"])
async def create_role(
    role_data: CreateRoleRequest,
    current_user: User = Depends(get_current_user_required)
):
    """
    创建角色

    需要权限: role:create
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.ROLE_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: role:create"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        # 检查角色名是否已存在
        stmt = select(Role).where(Role.name == role_data.name)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色名已存在"
            )

        # 创建角色
        role = Role(
            name=role_data.name,
            display_name=role_data.display_name,
            description=role_data.description,
            role_type="custom",
            created_by=current_user.user_id
        )

        session.add(role)
        await session.flush()

        # 分配权限
        if role_data.permissions:
            for perm_name in role_data.permissions:
                stmt = select(Permission).where(Permission.name == perm_name)
                result = await session.execute(stmt)
                perm = result.scalar_one_or_none()
                if perm:
                    role.permissions.append(perm)

        await session.commit()
        await session.refresh(role)

        logger.info(f"[Admin] 角色创建成功: {role.name} by {current_user.username}")

        return RoleListItem(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            is_active=role.is_active,
            is_system_role=role.is_system_role,
            level=role.level,
            user_count=0
        )


@router.put("/roles/{role_id}", response_model=RoleListItem, tags=["管理员"])
async def update_role(
    role_id: UUID,
    role_data: UpdateRoleRequest,
    current_user: User = Depends(get_current_user_required)
):
    """
    更新角色

    需要权限: role:update
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.ROLE_UPDATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: role:update"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )

        # 系统角色不能修改
        if role.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统角色不能修改"
            )

        # 更新字段
        if role_data.display_name is not None:
            role.display_name = role_data.display_name
        if role_data.description is not None:
            role.description = role_data.description
        if role_data.is_active is not None:
            role.is_active = role_data.is_active

        await session.commit()
        await session.refresh(role)

        logger.info(f"[Admin] 角色更新成功: {role.name} by {current_user.username}")

        # 计算用户数量
        user_count = len([u for u in role.users if u.is_active])

        return RoleListItem(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            is_active=role.is_active,
            is_system_role=role.is_system_role,
            level=role.level,
            user_count=user_count
        )


@router.delete("/roles/{role_id}", tags=["管理员"])
async def delete_role(
    role_id: UUID,
    current_user: User = Depends(get_current_user_required)
):
    """
    删除角色

    需要权限: role:delete
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.ROLE_DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: role:delete"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )

        # 系统角色不能删除
        if role.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统角色不能删除"
            )

        await session.delete(role)
        await session.commit()

        logger.info(f"[Admin] 角色删除成功: {role.name} by {current_user.username}")

        return {"message": "角色删除成功"}


@router.post("/roles/{role_id}/permissions", tags=["管理员"])
async def assign_role_permissions(
    role_id: UUID,
    perm_data: AssignPermissionsRequest,
    current_user: User = Depends(get_current_user_required)
):
    """
    分配角色权限

    需要权限: role:update
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.ROLE_UPDATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: role:update"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        # 查询角色
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )

        # 系统角色不能修改权限
        if role.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统角色权限不能修改"
            )

        # 清除现有权限
        role.permissions.clear()

        # 分配新权限
        for perm_name in perm_data.permissions:
            stmt = select(Permission).where(Permission.name == perm_name)
            result = await session.execute(stmt)
            perm = result.scalar_one_or_none()
            if perm:
                role.permissions.append(perm)

        await session.commit()

        logger.info(f"[Admin] 角色权限分配成功: {role.name} -> {perm_data.permissions} by {current_user.username}")

        return {"message": "权限分配成功", "permissions": perm_data.permissions}


# ============================================
# 权限管理端点
# ============================================

@router.get("/permissions", response_model=List[PermissionListItem], tags=["管理员"])
async def list_permissions(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=200, description="返回记录数"),
    resource: Optional[str] = Query(None, description="按资源筛选"),
    current_user: User = Depends(get_current_user_required)
):
    """
    获取权限列表

    需要权限: permission:read
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.PERMISSION_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: permission:read"
        )

    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        stmt = select(Role).offset(skip).limit(limit)

        if resource:
            stmt = stmt.where(Permission.resource == resource)

        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        permissions = result.scalars().all()

        return [
            PermissionListItem(
                id=perm.id,
                name=perm.name,
                display_name=perm.display_name,
                description=perm.description,
                resource=perm.resource,
                action=perm.action,
                scope=perm.scope,
                is_active=perm.is_active
            )
            for perm in permissions
        ]
