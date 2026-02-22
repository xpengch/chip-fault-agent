"""
芯片失效分析AI Agent系统 - 认证服务
提供用户认证、授权和会话管理功能
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
import hashlib
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..database.connection import get_db_manager
from ..database.rbac_models import (
    User, Role, Permission, UserSession, AuditLog,
    SystemRoles, SystemPermissions
)
from ..config.settings import get_settings

settings = get_settings()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务类"""

    def __init__(self):
        """初始化认证服务"""
        self.name = "AuthService"
        self.algorithm = settings.JWT_ALGORITHM
        self.secret_key = settings.JWT_SECRET_KEY
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    # ============================================
    # 密码处理
    # ============================================

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_user_id(username: str) -> str:
        """生成用户ID"""
        # 使用用户名和时间戳生成唯一ID
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        hash_part = hashlib.md5(f"{username}{timestamp}".encode()).hexdigest()[:8]
        return f"USR_{timestamp}_{hash_part}".upper()

    @staticmethod
    def generate_session_id() -> str:
        """生成会话ID"""
        return f"SES_{secrets.token_hex(16)}".upper()

    # ============================================
    # Token处理
    # ============================================

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问Token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "type": "access"
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建刷新Token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码Token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"[{self.name}] Token解码失败: {str(e)}")
            return None

    # ============================================
    # 用户认证
    # ============================================

    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: str,
        user_agent: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        用户认证

        Args:
            username: 用户名
            password: 密码
            ip_address: IP地址
            user_agent: 用户代理

        Returns:
            认证成功返回用户信息和Token，失败返回None
        """
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 查询用户
            stmt = select(User).where(
                or_(
                    User.username == username,
                    User.email == username
                )
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"[{self.name}] 用户不存在: {username}")
                await self._record_login_attempt(session, None, username, False, ip_address, user_agent, "用户不存在")
                return None

            # 检查账户是否激活
            if not user.is_active:
                logger.warning(f"[{self.name}] 账户已禁用: {username}")
                await self._record_login_attempt(session, user.user_id, username, False, ip_address, user_agent, "账户已禁用")
                return None

            # 检查账户是否被锁定
            if user.is_locked():
                logger.warning(f"[{self.name}] 账户已锁定: {username}")
                await self._record_login_attempt(session, user.user_id, username, False, ip_address, user_agent, "账户已锁定")
                return None

            # 验证密码
            if not self.verify_password(password, user.password_hash):
                logger.warning(f"[{self.name}] 密码错误: {username}")

                # 增加失败次数
                user.failed_login_attempts += 1

                # 失败次数超过5次，锁定账户30分钟
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                    logger.warning(f"[{self.name}] 账户已锁定: {username}, 失败次数: {user.failed_login_attempts}")

                await session.commit()
                await self._record_login_attempt(session, user.user_id, username, False, ip_address, user_agent, "密码错误")
                return None

            # 认证成功，重置失败次数
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address

            await session.commit()

            # 创建Token
            token_data = {
                "sub": user.user_id,
                "username": user.username,
                "full_name": user.full_name
            }
            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token(token_data)

            # 创建会话
            session_obj = UserSession(
                session_id=self.generate_session_id(),
                user_id=user.user_id,
                token=access_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            )
            session.add(session_obj)
            await session.commit()
            await session.refresh(session_obj)

            # 记录登录日志
            await self._record_login_attempt(session, user.user_id, username, True, ip_address, user_agent)

            # 获取用户权限
            permissions = await self._get_user_permissions(session, user)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "department": user.department,
                    "position": user.position,
                    "roles": [role.name for role in user.roles if role.is_active],
                    "permissions": permissions
                },
                "session_id": session_obj.session_id
            }

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        刷新访问Token

        Args:
            refresh_token: 刷新Token

        Returns:
            成功返回新的访问Token，失败返回None
        """
        # 解码刷新Token
        payload = self.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 查询会话
            stmt = select(UserSession).where(
                and_(
                    UserSession.refresh_token == refresh_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            )
            result = await session.execute(stmt)
            user_session = result.scalar_one_or_none()

            if not user_session:
                logger.warning(f"[{self.name}] 无效的刷新Token")
                return None

            # 查询用户
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                logger.warning(f"[{self.name}] 用户不存在或已禁用: {user_id}")
                return None

            # 创建新的访问Token
            token_data = {
                "sub": user.user_id,
                "username": user.username,
                "full_name": user.full_name
            }
            access_token = self.create_access_token(token_data)

            # 更新会话
            user_session.token = access_token
            user_session.last_activity_at = datetime.utcnow()
            await session.commit()

            # 获取用户权限
            permissions = await self._get_user_permissions(session, user)

            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "roles": [role.name for role in user.roles if role.is_active],
                    "permissions": permissions
                }
            }

    async def logout_user(self, session_id: str) -> bool:
        """
        用户登出

        Args:
            session_id: 会话ID

        Returns:
            成功返回True，失败返回False
        """
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            stmt = select(UserSession).where(UserSession.session_id == session_id)
            result = await session.execute(stmt)
            user_session = result.scalar_one_or_none()

            if user_session:
                user_session.is_active = False
                user_session.logged_out_at = datetime.utcnow()
                user_session.logout_reason = "user_logout"
                await session.commit()

                logger.info(f"[{self.name}] 用户登出成功: session_id={session_id}")
                return True

            return False

    # ============================================
    # 权限检查
    # ============================================

    async def check_permission(
        self,
        user_id: str,
        permission_name: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """
        检查用户是否拥有指定权限

        Args:
            user_id: 用户ID
            permission_name: 权限名称
            resource_id: 资源ID（用于资源级权限检查）

        Returns:
            拥有权限返回True，否则返回False
        """
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                return False

            # 检查用户是否拥有该权限
            return user.has_permission(permission_name)

    async def check_role(self, user_id: str, role_name: str) -> bool:
        """
        检查用户是否拥有指定角色

        Args:
            user_id: 用户ID
            role_name: 角色名称

        Returns:
            拥有角色返回True，否则返回False
        """
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                return False

            return user.has_role(role_name)

    # ============================================
    # 用户管理
    # ============================================

    async def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        department: Optional[str] = None,
        position: Optional[str] = None,
        role_names: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> Optional[User]:
        """
        创建用户

        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            full_name: 全名
            department: 部门
            position: 职位
            role_names: 角色列表
            created_by: 创建者用户ID

        Returns:
            成功返回用户对象，失败返回None
        """
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 检查用户名是否已存在
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                logger.warning(f"[{self.name}] 用户名已存在: {username}")
                return None

            # 检查邮箱是否已存在
            if email:
                stmt = select(User).where(User.email == email)
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    logger.warning(f"[{self.name}] 邮箱已存在: {email}")
                    return None

            # 创建用户
            user = User(
                user_id=self.generate_user_id(username),
                username=username,
                email=email,
                full_name=full_name,
                department=department,
                position=position,
                password_hash=self.hash_password(password),
                created_by=created_by
            )

            session.add(user)
            await session.flush()

            # 分配角色
            if role_names:
                for role_name in role_names:
                    stmt = select(Role).where(Role.name == role_name)
                    result = await session.execute(stmt)
                    role = result.scalar_one_or_none()
                    if role:
                        user.roles.append(role)

            await session.commit()
            await session.refresh(user)

            logger.info(f"[{self.name}] 用户创建成功: {user.user_id}")
            return user

    # ============================================
    # 辅助方法
    # ============================================

    async def _get_user_permissions(self, session: AsyncSession, user: User) -> List[str]:
        """获取用户权限列表"""
        permissions = set()
        for role in user.roles:
            if not role.is_active:
                continue
            for permission in role.permissions:
                if permission.is_active:
                    permissions.add(permission.name)
        return list(permissions)

    async def _record_login_attempt(
        self,
        session: AsyncSession,
        user_id: Optional[str],
        username: str,
        success: bool,
        ip_address: str,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """记录登录尝试"""
        audit_log = AuditLog(
            user_id=user_id,
            action="login" if success else "login_failed",
            status="success" if success else "failure",
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )
        session.add(audit_log)
        await session.commit()


# 全局认证服务实例
auth_service = AuthService()
