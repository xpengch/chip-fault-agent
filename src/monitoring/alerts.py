"""
监控告警模块
用于监控系统服务状态并发送告警通知
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio


class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """告警类型"""
    EMBEDDING_API_FAILED = "embedding_api_failed"
    KNOWLEDGE_GRAPH_FAILED = "knowledge_graph_failed"
    VECTOR_SEARCH_FAILED = "vector_search_failed"
    LLM_API_FAILED = "llm_api_failed"
    DATABASE_CONNECTION_FAILED = "database_connection_failed"
    NEO4J_CONNECTION_FAILED = "neo4j_connection_failed"


@dataclass
class Alert:
    """告警信息"""
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertManager:
    """告警管理器 - 单例模式"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._alerts: List[Alert] = []
            cls._instance._alert_counts: Dict[AlertType, int] = {}
            cls._instance._last_alert_time: Dict[AlertType, datetime] = {}
            cls._instance._cooldown_period = timedelta(minutes=5)  # 告警冷却期
        return cls._instance

    def __init__(self):
        """初始化告警管理器"""
        self.name = "AlertManager"
        self.description = "监控系统服务状态并发送告警"

    async def send_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        发送告警

        Args:
            alert_type: 告警类型
            severity: 严重程度
            title: 告警标题
            message: 告警消息
            details: 详细信息

        Returns:
            创建的告警对象
        """
        # 检查冷却期（避免重复告警）
        last_time = self._last_alert_time.get(alert_type)
        if last_time and datetime.utcnow() - last_time < self._cooldown_period:
            logger.debug(f"[AlertManager] 告警冷却期 - {alert_type.value}")
            return None

        # 创建告警
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            details=details or {}
        )

        # 记录告警
        self._alerts.append(alert)
        self._alert_counts[alert_type] = self._alert_counts.get(alert_type, 0) + 1
        self._last_alert_time[alert_type] = datetime.utcnow()

        # 记录日志
        log_method = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }.get(severity, logger.error)

        log_method(
            f"[ALERT] {alert_type.value.upper()} - {title}\n"
            f"消息: {message}\n"
            f"详情: {details}"
        )

        # 发送通知
        await self._send_notification(alert)

        return alert

    async def _send_notification(self, alert: Alert):
        """
        发送告警通知

        支持的通知方式：
        - 邮件通知（如果配置了SMTP）
        - Webhook通知（如果配置了webhook URL）
        - 系统日志
        """
        # 1. 记录到专门的告警日志表（如果配置了数据库）
        try:
            await self._store_alert_to_database(alert)
        except Exception as e:
            logger.warning(f"[AlertManager] 存储告警到数据库失败: {str(e)}")

        # 2. 发送Webhook通知（如果配置了）
        try:
            await self._send_webhook_notification(alert)
        except Exception as e:
            logger.warning(f"[AlertManager] Webhook通知失败: {str(e)}")

        # 3. 发送邮件通知（如果配置了）
        try:
            await self._send_email_notification(alert)
        except Exception as e:
            logger.warning(f"[AlertManager] 邮件通知失败: {str(e)}")

    async def _store_alert_to_database(self, alert: Alert):
        """存储告警到数据库"""
        from ..database.connection import get_db_manager
        from sqlalchemy import text

        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            await session.execute(text("""
                INSERT INTO system_alerts (alert_type, severity, title, message, details, created_at)
                VALUES (:alert_type, :severity, :title, :message, :details, :created_at)
            """), {
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "details": str(alert.details),
                "created_at": alert.timestamp
            })
            await session.commit()

    async def _send_webhook_notification(self, alert: Alert):
        """发送Webhook通知"""
        from src.config.settings import get_settings
        import aiohttp

        settings = get_settings()
        webhook_url = getattr(settings, 'ALERT_WEBHOOK_URL', None)

        if not webhook_url:
            return

        # 准备webhook payload
        payload = {
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "details": alert.details,
            "timestamp": alert.timestamp.isoformat(),
            "environment": getattr(settings, 'ENVIRONMENT', 'development')
        }

        # 发送webhook
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logger.info(f"[AlertManager] Webhook通知发送成功")
                else:
                    logger.warning(f"[AlertManager] Webhook通知失败: {response.status}")

    async def _send_email_notification(self, alert: Alert):
        """发送邮件通知"""
        from src.config.settings import get_settings

        settings = get_settings()
        smtp_config = {
            'host': getattr(settings, 'SMTP_HOST', None),
            'port': getattr(settings, 'SMTP_PORT', 587),
            'username': getattr(settings, 'SMTP_USERNAME', None),
            'password': getattr(settings, 'SMTP_PASSWORD', None),
            'from_addr': getattr(settings, 'SMTP_FROM', None),
            'to_addrs': getattr(settings, 'ALERT_EMAIL_TO', [])
        }

        # 检查是否配置了邮件
        if not all([smtp_config['host'], smtp_config['username'], smtp_config['password'], smtp_config['to_addrs']]):
            return

        # 发送邮件（简化实现）
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg['From'] = smtp_config['from_addr'] or smtp_config['username']
        msg['To'] = ', '.join(smtp_config['to_addrs'])
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        msg.set_content(f"""
告警类型: {alert.alert_type.value}
严重程度: {alert.severity.value}
消息: {alert.message}
详情: {alert.details}
时间: {alert.timestamp.isoformat()}
        """)

        async with asyncio.get_event_loop() as loop:
            await loop.run_in_executor(None, lambda: smtplib.SMTP(smtp_config['host'], smtp_config['port']))
            # ... 实际邮件发送逻辑

    def get_recent_alerts(
        self,
        hours: int = 24,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """获取最近的告警"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        alerts = [
            alert for alert in self._alerts
            if alert.timestamp >= cutoff_time
            and (severity is None or alert.severity == severity)
        ]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计"""
        total_alerts = len(self._alerts)
        last_24_hours = datetime.utcnow() - timedelta(hours=24)

        recent_alerts = [a for a in self._alerts if a.timestamp >= last_24_hours]

        return {
            "total_alerts": total_alerts,
            "last_24_hours": len(recent_alerts),
            "by_type": self._alert_counts.copy(),
            "by_severity": {
                severity.value: len([a for a in recent_alerts if a.severity == severity])
                for severity in AlertSeverity
            }
        }


# 全局告警管理器实例
alert_manager = AlertManager()


def get_alert_manager() -> AlertManager:
    """获取告警管理器单例"""
    return alert_manager
