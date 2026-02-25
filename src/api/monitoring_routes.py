"""
芯片失效分析AI Agent系统 - 监控告警API路由
提供告警查询、统计、embedding状态查询等端点
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from loguru import logger

from ..monitoring import get_alert_manager, AlertSeverity
from ..auth.dependencies import get_current_user_required
from ..database.rbac_models import User


# ============================================
# 路由器
# ============================================
router = APIRouter(prefix="/api/v1/monitoring", tags=["监控告警"])


# ============================================
# API端点
# ============================================

@router.get("/alerts/recent", tags=["监控告警"])
async def get_recent_alerts(
    hours: int = Query(24, ge=1, le=168, description="查询最近几小时的告警"),
    severity: Optional[str] = Query(None, description="筛选严重程度"),
    current_user: User = Depends(get_current_user_required)
):
    """获取最近的告警"""
    from ..database.rbac_models import SystemPermissions
    if not current_user.has_permission(SystemPermissions.AUDIT_LOG_READ):
        return {"success": False, "error": "权限不足"}

    severity_filter = None
    if severity:
        try:
            severity_filter = AlertSeverity(severity)
        except ValueError:
            pass

    alert_manager = get_alert_manager()
    alerts = alert_manager.get_recent_alerts(hours=hours, severity=severity_filter)

    return {
        "success": True,
        "data": [
            {
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "details": alert.details,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved
            }
            for alert in alerts
        ],
        "total": len(alerts)
    }


@router.get("/alerts/statistics", tags=["监控告警"])
async def get_alert_statistics(
    current_user: User = Depends(get_current_user_required)
):
    """获取告警统计"""
    from ..database.rbac_models import SystemPermissions
    if not current_user.has_permission(SystemPermissions.AUDIT_LOG_READ):
        return {"success": False, "error": "权限不足"}

    alert_manager = get_alert_manager()
    stats = alert_manager.get_alert_statistics()

    return {"success": True, "data": stats}


@router.get("/health/alerts", tags=["监控告警"])
async def get_alert_health():
    """获取告警健康状态（无需认证）"""
    alert_manager = get_alert_manager()
    stats = alert_manager.get_alert_statistics()

    has_critical = stats.get("by_severity", {}).get("critical", 0) > 0
    has_recent_critical = any(
        a.severity == AlertSeverity.CRITICAL and not a.resolved
        for a in alert_manager.get_recent_alerts(hours=1)
    )

    return {
        "status": "unhealthy" if has_recent_critical else "healthy",
        "total_alerts": stats.get("total_alerts", 0),
        "last_24_hours": stats.get("last_24_hours", 0),
        "has_critical_alerts": has_critical,
        "by_type": stats.get("by_type", {}),
        "by_severity": stats.get("by_severity", {})
    }


@router.get("/embedding/status", tags=["监控告警"])
async def get_embedding_status():
    """获取Embedding服务状态（无需认证）"""
    from ..config.settings import get_settings
    from ..embedding import get_bge_model_manager

    settings = get_settings()
    bge_manager = get_bge_model_manager()

    status = {
        "backend": settings.EMBEDDING_BACKEND,
        "model": settings.EMBEDDING_MODEL,
        "device": settings.EMBEDDING_DEVICE,
        "dimensions": settings.EMBEDDING_DIMENSIONS
    }

    if settings.EMBEDDING_BACKEND == "bge":
        try:
            import asyncio
            def _check_model():
                return bge_manager.is_loaded()
            loop = asyncio.get_event_loop()
            is_loaded = await loop.run_in_executor(None, _check_model)

            if is_loaded:
                dimension = bge_manager.get_embedding_dimension()
                status["bge_loaded"] = True
                status["actual_dimensions"] = dimension
                status["status"] = "ready"
            else:
                status["bge_loaded"] = False
                status["status"] = "not_loaded"
                status["message"] = "BGE模型未加载，首次调用时将自动下载"
        except Exception as e:
            status["status"] = "error"
            status["error"] = str(e)

    return {"success": True, "data": status}


@router.post("/embedding/test", tags=["监控告警"])
async def test_embedding(
    text: str = Query(..., description="测试文本")
):
    """测试Embedding生成"""
    from ..config.settings import get_settings
    from ..mcp.tools.llm_tool import LLMTool

    settings = get_settings()

    try:
        llm_tool = LLMTool()
        start_time = datetime.utcnow()
        embedding = await llm_tool.generate_embedding(text)
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        return {
            "success": True,
            "data": {
                "backend": settings.EMBEDDING_BACKEND,
                "model": settings.EMBEDDING_MODEL,
                "text_length": len(text),
                "embedding_dimension": len(embedding),
                "duration_seconds": duration,
                "first_5_values": embedding[:5]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "backend": settings.EMBEDDING_BACKEND,
                "model": settings.EMBEDDING_MODEL
            }
        }
