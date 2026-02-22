"""
芯片失效分析AI Agent系统 - RBAC权限模型
实现基于角色的访问控制（RBAC）
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Index, Text, Table, UniqueConstraint, UUID
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from .models import Base


# ============================================
# 用户-角色关联表（多对多）
# ============================================
user_role_association = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String(50), ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', UUID, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', String(50)),  # 分配者用户ID
    Column('expires_at', DateTime, nullable=True),  # 角色过期时间
    Index('idx_user_role_user', 'user_id'),
    Index('idx_user_role_role', 'role_id'),
    extend_existing=True
)


# ============================================
# 角色-权限关联表（多对多）
# ============================================
role_permission_association = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', UUID, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_role_perm_role', 'role_id'),
    Index('idx_role_perm_perm', 'permission_id'),
    extend_existing=True
)


# ============================================
# 用户表
# ============================================
class User(Base):
    """
    用户表 - 支持多种认证方式
    """
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    # 认证信息
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))  # 哈希密码
    auth_provider: Mapped[str] = mapped_column(String(20), default="local")  # local/ldap/sso
    auth_provider_id: Mapped[Optional[str]] = mapped_column(String(100))  # 第三方认证ID
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 用户信息
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    position: Mapped[Optional[str]] = mapped_column(String(100))
    employee_id: Mapped[Optional[str]] = mapped_column(String(50))

    # 扩展属性
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # 登录信息
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # 密码策略
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(50))

    # 关系
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_role_association,
        back_populates="users"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user"
    )

    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
        Index('idx_users_is_active', 'is_active'),
    )

    def has_permission(self, permission_name: str) -> bool:
        """检查用户是否拥有指定权限"""
        for role in self.roles:
            if not role.is_active:
                continue
            for permission in role.permissions:
                if permission.name == permission_name and permission.is_active:
                    return True
        return False

    def has_role(self, role_name: str) -> bool:
        """检查用户是否拥有指定角色"""
        for role in self.roles:
            if role.name == role_name and role.is_active:
                return True
        return False

    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False


# ============================================
# 角色表
# ============================================
class Role(Base):
    """
    角色表 - 定义用户角色
    """
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # 角色层级和继承
    parent_role_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('roles.id'))
    level: Mapped[int] = mapped_column(Integer, default=0)  # 角色层级

    # 角色类型
    role_type: Mapped[str] = mapped_column(String(20), default="custom")  # system/custom
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False)

    # 扩展属性
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(50))

    # 关系
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_role_association,
        back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permission_association,
        back_populates="roles"
    )
    parent_role: Mapped[Optional["Role"]] = relationship(
        "Role",
        remote_side=[id],
        backref="child_roles"
    )

    __table_args__ = (
        Index('idx_roles_name', 'name'),
        Index('idx_roles_is_active', 'is_active'),
        Index('idx_roles_level', 'level'),
    )


# ============================================
# 权限表
# ============================================
class Permission(Base):
    """
    权限表 - 定义系统权限
    """
    __tablename__ = "permissions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # 权限结构：resource:action
    # 例如: analysis:create, analysis:read, analysis:update, analysis:delete
    resource: Mapped[str] = mapped_column(String(50), nullable=False)  # 资源类型
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # 操作类型
    scope: Mapped[Optional[str]] = mapped_column(String(50))  # 权限范围：global/department/team/personal

    # 权限类型
    permission_type: Mapped[str] = mapped_column(String(20), default="api")  # api/ui/data
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # API端点映射（用于API权限检查）
    api_endpoints: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permission_association,
        back_populates="permissions"
    )

    __table_args__ = (
        Index('idx_permissions_name', 'name'),
        Index('idx_permissions_resource', 'resource'),
        Index('idx_permissions_action', 'action'),
        Index('idx_permissions_is_active', 'is_active'),
        UniqueConstraint('resource', 'action', 'scope', name='uq_permission_scope'),
    )


# ============================================
# 用户会话表
# ============================================
class UserSession(Base):
    """
    用户会话表 - 管理用户登录会话
    """
    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)

    # 会话信息
    token: Mapped[str] = mapped_column(String(500), nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500))
    token_type: Mapped[str] = mapped_column(String(20), default="Bearer")

    # 设备信息
    device_type: Mapped[Optional[str]] = mapped_column(String(50))  # desktop/mobile/tablet
    device_id: Mapped[Optional[str]] = mapped_column(String(100))
    browser: Mapped[Optional[str]] = mapped_column(String(100))
    os: Mapped[Optional[str]] = mapped_column(String(50))

    # 网络信息
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)

    # 会话状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # 登出信息
    logged_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    logout_reason: Mapped[Optional[str]] = mapped_column(String(50))

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index('idx_sessions_user_id', 'user_id'),
        Index('idx_sessions_token', 'token'),
        Index('idx_sessions_is_active', 'is_active'),
        Index('idx_sessions_expires_at', 'expires_at'),
    )

    def is_valid(self) -> bool:
        """检查会话是否有效"""
        if not self.is_active:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        return True


# ============================================
# 审计日志表（扩展原AuditLog模型）
# ============================================
class AuditLog(Base):
    """
    审计日志表 - 记录所有用户操作
    """
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey('users.user_id', ondelete='SET NULL'))

    # 操作信息
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # login/logout/create/update/delete
    resource_type: Mapped[Optional[str]] = mapped_column(String(50))  # analysis/case/rule/user等
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))

    # 结果
    status: Mapped[str] = mapped_column(String(20), default="success")  # success/failure/warning
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # 敏感度级别
    sensitivity_level: Mapped[Optional[int]] = mapped_column(Integer)  # 0=公开, 1=内部, 2=机密, 3=绝密

    # 请求信息
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_method: Mapped[Optional[str]] = mapped_column(String(10))
    request_path: Mapped[Optional[str]] = mapped_column(String(255))

    # 请求数据
    request_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    response_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_resource_type', 'resource_type'),
        Index('idx_audit_status', 'status'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_sensitivity', 'sensitivity_level'),
    )


# ============================================
# 预定义角色和权限常量
# ============================================

class SystemRoles:
    """系统预定义角色"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    EXPERT = "expert"
    ANALYST = "analyst"
    VIEWER = "viewer"

    @classmethod
    def get_default_roles(cls) -> List[Dict[str, Any]]:
        """获取默认角色配置"""
        return [
            {
                "name": cls.SUPER_ADMIN,
                "display_name": "超级管理员",
                "description": "系统最高权限，拥有所有操作权限",
                "role_type": "system",
                "is_system_role": True,
                "level": 100
            },
            {
                "name": cls.ADMIN,
                "display_name": "管理员",
                "description": "系统管理员，可以管理用户、角色和配置",
                "role_type": "system",
                "is_system_role": True,
                "level": 80
            },
            {
                "name": cls.EXPERT,
                "display_name": "专家",
                "description": "领域专家，可以进行专家修正和知识库更新",
                "role_type": "system",
                "is_system_role": True,
                "level": 60
            },
            {
                "name": cls.ANALYST,
                "display_name": "分析师",
                "description": "普通分析师，可以提交分析请求和查看结果",
                "role_type": "system",
                "is_system_role": True,
                "level": 40
            },
            {
                "name": cls.VIEWER,
                "display_name": "查看者",
                "description": "只读权限，只能查看分析结果",
                "role_type": "system",
                "is_system_role": True,
                "level": 20
            }
        ]


class SystemPermissions:
    """系统预定义权限"""
    # 用户管理权限
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # 角色管理权限
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"

    # 权限管理权限
    PERMISSION_CREATE = "permission:create"
    PERMISSION_READ = "permission:read"
    PERMISSION_UPDATE = "permission:update"
    PERMISSION_DELETE = "permission:delete"

    # 分析权限
    ANALYSIS_CREATE = "analysis:create"
    ANALYSIS_READ = "analysis:read"
    ANALYSIS_UPDATE = "analysis:update"
    ANALYSIS_DELETE = "analysis:delete"
    ANALYSIS_EXPORT = "analysis:export"

    # 案例管理权限
    CASE_CREATE = "case:create"
    CASE_READ = "case:read"
    CASE_UPDATE = "case:update"
    CASE_DELETE = "case:delete"

    # 规则管理权限
    RULE_CREATE = "rule:create"
    RULE_READ = "rule:read"
    RULE_UPDATE = "rule:update"
    RULE_DELETE = "rule:delete"

    # 专家修正权限
    EXPERT_CORRECTION_CREATE = "expert_correction:create"
    EXPERT_CORRECTION_APPROVE = "expert_correction:approve"
    EXPERT_CORRECTION_REJECT = "expert_correction:reject"

    # 系统管理权限
    SYSTEM_CONFIG_READ = "system_config:read"
    SYSTEM_CONFIG_UPDATE = "system_config:update"

    # 审计日志权限
    AUDIT_LOG_READ = "audit_log:read"
    AUDIT_LOG_EXPORT = "audit_log:export"

    # 报告权限
    REPORT_GENERATE = "report:generate"
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"

    @classmethod
    def get_default_permissions(cls) -> List[Dict[str, Any]]:
        """获取默认权限配置"""
        return [
            # 用户管理
            {"name": cls.USER_CREATE, "display_name": "创建用户", "resource": "user", "action": "create", "scope": "global"},
            {"name": cls.USER_READ, "display_name": "查看用户", "resource": "user", "action": "read", "scope": "global"},
            {"name": cls.USER_UPDATE, "display_name": "更新用户", "resource": "user", "action": "update", "scope": "global"},
            {"name": cls.USER_DELETE, "display_name": "删除用户", "resource": "user", "action": "delete", "scope": "global"},
            # 角色管理
            {"name": cls.ROLE_CREATE, "display_name": "创建角色", "resource": "role", "action": "create", "scope": "global"},
            {"name": cls.ROLE_READ, "display_name": "查看角色", "resource": "role", "action": "read", "scope": "global"},
            {"name": cls.ROLE_UPDATE, "display_name": "更新角色", "resource": "role", "action": "update", "scope": "global"},
            {"name": cls.ROLE_DELETE, "display_name": "删除角色", "resource": "role", "action": "delete", "scope": "global"},
            # 分析权限
            {"name": cls.ANALYSIS_CREATE, "display_name": "提交分析", "resource": "analysis", "action": "create", "scope": "personal"},
            {"name": cls.ANALYSIS_READ, "display_name": "查看分析", "resource": "analysis", "action": "read", "scope": "department"},
            {"name": cls.ANALYSIS_UPDATE, "display_name": "更新分析", "resource": "analysis", "action": "update", "scope": "personal"},
            {"name": cls.ANALYSIS_DELETE, "display_name": "删除分析", "resource": "analysis", "action": "delete", "scope": "personal"},
            {"name": cls.ANALYSIS_EXPORT, "display_name": "导出分析", "resource": "analysis", "action": "export", "scope": "department"},
            # 案例管理
            {"name": cls.CASE_CREATE, "display_name": "创建案例", "resource": "case", "action": "create", "scope": "global"},
            {"name": cls.CASE_READ, "display_name": "查看案例", "resource": "case", "action": "read", "scope": "global"},
            {"name": cls.CASE_UPDATE, "display_name": "更新案例", "resource": "case", "action": "update", "scope": "global"},
            {"name": cls.CASE_DELETE, "display_name": "删除案例", "resource": "case", "action": "delete", "scope": "global"},
            # 规则管理
            {"name": cls.RULE_CREATE, "display_name": "创建规则", "resource": "rule", "action": "create", "scope": "global"},
            {"name": cls.RULE_READ, "display_name": "查看规则", "resource": "rule", "action": "read", "scope": "global"},
            {"name": cls.RULE_UPDATE, "display_name": "更新规则", "resource": "rule", "action": "update", "scope": "global"},
            {"name": cls.RULE_DELETE, "display_name": "删除规则", "resource": "rule", "action": "delete", "scope": "global"},
            # 专家修正
            {"name": cls.EXPERT_CORRECTION_CREATE, "display_name": "提交专家修正", "resource": "expert_correction", "action": "create", "scope": "department"},
            {"name": cls.EXPERT_CORRECTION_APPROVE, "display_name": "批准专家修正", "resource": "expert_correction", "action": "approve", "scope": "global"},
            {"name": cls.EXPERT_CORRECTION_REJECT, "display_name": "拒绝专家修正", "resource": "expert_correction", "action": "reject", "scope": "global"},
            # 系统管理
            {"name": cls.SYSTEM_CONFIG_READ, "display_name": "查看系统配置", "resource": "system_config", "action": "read", "scope": "global"},
            {"name": cls.SYSTEM_CONFIG_UPDATE, "display_name": "更新系统配置", "resource": "system_config", "action": "update", "scope": "global"},
            # 审计日志
            {"name": cls.AUDIT_LOG_READ, "display_name": "查看审计日志", "resource": "audit_log", "action": "read", "scope": "global"},
            {"name": cls.AUDIT_LOG_EXPORT, "display_name": "导出审计日志", "resource": "audit_log", "action": "export", "scope": "global"},
            # 报告
            {"name": cls.REPORT_GENERATE, "display_name": "生成报告", "resource": "report", "action": "generate", "scope": "personal"},
            {"name": cls.REPORT_READ, "display_name": "查看报告", "resource": "report", "action": "read", "scope": "department"},
            {"name": cls.REPORT_EXPORT, "display_name": "导出报告", "resource": "report", "action": "export", "scope": "department"},
        ]

    @classmethod
    def get_role_permissions(cls) -> Dict[str, List[str]]:
        """获取角色-权限映射"""
        return {
            SystemRoles.SUPER_ADMIN: [
                # 所有权限
                cls.USER_CREATE, cls.USER_READ, cls.USER_UPDATE, cls.USER_DELETE,
                cls.ROLE_CREATE, cls.ROLE_READ, cls.ROLE_UPDATE, cls.ROLE_DELETE,
                cls.PERMISSION_CREATE, cls.PERMISSION_READ, cls.PERMISSION_UPDATE, cls.PERMISSION_DELETE,
                cls.ANALYSIS_CREATE, cls.ANALYSIS_READ, cls.ANALYSIS_UPDATE, cls.ANALYSIS_DELETE, cls.ANALYSIS_EXPORT,
                cls.CASE_CREATE, cls.CASE_READ, cls.CASE_UPDATE, cls.CASE_DELETE,
                cls.RULE_CREATE, cls.RULE_READ, cls.RULE_UPDATE, cls.RULE_DELETE,
                cls.EXPERT_CORRECTION_CREATE, cls.EXPERT_CORRECTION_APPROVE, cls.EXPERT_CORRECTION_REJECT,
                cls.SYSTEM_CONFIG_READ, cls.SYSTEM_CONFIG_UPDATE,
                cls.AUDIT_LOG_READ, cls.AUDIT_LOG_EXPORT,
                cls.REPORT_GENERATE, cls.REPORT_READ, cls.REPORT_EXPORT,
            ],
            SystemRoles.ADMIN: [
                cls.USER_READ, cls.USER_UPDATE,
                cls.ROLE_READ,
                cls.PERMISSION_READ,
                cls.ANALYSIS_CREATE, cls.ANALYSIS_READ, cls.ANALYSIS_EXPORT,
                cls.CASE_CREATE, cls.CASE_READ, cls.CASE_UPDATE,
                cls.RULE_READ, cls.RULE_UPDATE,
                cls.SYSTEM_CONFIG_READ,
                cls.AUDIT_LOG_READ,
                cls.REPORT_GENERATE, cls.REPORT_READ, cls.REPORT_EXPORT,
            ],
            SystemRoles.EXPERT: [
                cls.ANALYSIS_CREATE, cls.ANALYSIS_READ, cls.ANALYSIS_EXPORT,
                cls.CASE_READ, cls.CASE_CREATE,
                cls.RULE_READ,
                cls.EXPERT_CORRECTION_CREATE,
                cls.REPORT_GENERATE, cls.REPORT_READ, cls.REPORT_EXPORT,
            ],
            SystemRoles.ANALYST: [
                cls.ANALYSIS_CREATE, cls.ANALYSIS_READ,
                cls.CASE_READ,
                cls.REPORT_GENERATE, cls.REPORT_READ,
            ],
            SystemRoles.VIEWER: [
                cls.ANALYSIS_READ,
                cls.CASE_READ,
                cls.REPORT_READ,
            ],
        }
