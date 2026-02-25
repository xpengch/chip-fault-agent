"""
芯片失效分析AI Agent系统 - 认证中间件
提供请求认证检查和审计日志记录
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy import select
from loguru import logger
from datetime import datetime
import json

from ..database.connection import get_db_manager
from ..database.rbac_models import AuditLog, User
from .service import auth_service


class AuditLogMiddleware(BaseHTTPMiddleware):
    """审计日志中间件 - 记录所有API请求"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """处理请求并记录日志"""
        start_time = datetime.utcnow()

        # 读取请求体（如果有）
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                request_body = await request.body()
            except Exception:
                pass

        # 处理请求
        response = await call_next(request)

        # 记录审计日志
        await self._log_audit(request, response, request_body, start_time)

        return response

    async def _log_audit(
        self,
        request: Request,
        response: Response,
        request_body: bytes,
        start_time: datetime
    ):
        """记录审计日志"""
        try:
            # 获取用户信息
            user_id = getattr(request.state, "user_id", None)
            username = None

            if user_id:
                user = getattr(request.state, "user", None)
                if user:
                    username = user.username

            # 确定操作类型
            action = self._get_action_from_path(request.method, request.url.path)

            # 跳过健康检查等端点
            if self._should_skip_logging(request.url.path):
                return

            # 解析请求体
            request_data = None
            if request_body:
                try:
                    request_data = json.loads(request_body.decode())
                except Exception:
                    pass

            # 创建审计日志
            db_manager = get_db_manager()
            async with db_manager.get_session() as session:
                audit_log = AuditLog(
                    user_id=user_id,
                    action=action,
                    resource_type=self._get_resource_type(request.url.path),
                    status="success" if response.status_code < 400 else "failure",
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    request_method=request.method,
                    request_path=request.url.path,
                    request_data=request_data
                )
                session.add(audit_log)
                await session.commit()

        except Exception as e:
            logger.error(f"[AuditLog] 记录审计日志失败: {str(e)}")

    def _get_action_from_path(self, method: str, path: str) -> str:
        """从路径和HTTP方法获取操作类型"""
        # 特殊路径处理
        if "/auth/login" in path:
            return "login"
        elif "/auth/logout" in path:
            return "logout"
        elif "/auth/refresh" in path:
            return "refresh_token"

        # 通用HTTP方法映射
        method_action_map = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }
        return method_action_map.get(method, method.lower())

    def _get_resource_type(self, path: str) -> str:
        """从路径获取资源类型"""
        if "/auth/" in path:
            return "auth"
        elif "/users/" in path:
            return "user"
        elif "/roles/" in path:
            return "role"
        elif "/permissions/" in path:
            return "permission"
        elif "/analysis/" in path:
            return "analysis"
        elif "/cases/" in path:
            return "case"
        elif "/rules/" in path:
            return "rule"
        return "unknown"

    def _should_skip_logging(self, path: str) -> bool:
        """判断是否跳过日志记录"""
        skip_paths = [
            "/health",
            "/api/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """认证中间件 - 验证请求Token"""

    # 不需要认证的路径
    EXEMPT_PATHS = [
        "/",
        "/health",
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/token",
        "/api/v1/monitoring",
    ]

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """处理请求并验证认证"""
        path = request.url.path

        # 检查是否需要认证
        if self._is_exempt_path(path):
            return await call_next(request)

        # 获取Token
        authorization = request.headers.get("Authorization")
        if not authorization:
            return await call_next(request)

        # 验证Token并设置用户信息到request.state
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            payload = auth_service.decode_token(token)

            if payload and payload.get("type") == "access":
                user_id = payload.get("sub")
                if user_id:
                    # 查询用户信息
                    db_manager = get_db_manager()
                    async with db_manager.get_session() as session:
                        stmt = select(User).where(
                            User.user_id == user_id,
                            User.is_active == True
                        )
                        result = await session.execute(stmt)
                        user = result.scalar_one_or_none()

                        if user:
                            # 设置用户信息到request.state
                            request.state.user_id = user.user_id
                            request.state.user = user
                            request.state.username = user.username

        return await call_next(request)

    def _is_exempt_path(self, path: str) -> bool:
        """检查路径是否免于认证"""
        return any(path.startswith(exempt_path) for exempt_path in self.EXEMPT_PATHS)
