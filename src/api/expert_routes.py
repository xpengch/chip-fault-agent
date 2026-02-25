"""
芯片失效分析AI Agent系统 - 专家修正API路由
提供专家修正提交、审批、查询等端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from loguru import logger

from ..auth.dependencies import get_current_user_required, get_current_user
from ..database.rbac_models import User, SystemRoles, SystemPermissions
from ..agents.agent2.correction_processor import CorrectionProcessor
from ..agents.agent2.expert_interaction import ExpertInteractionAgent
from ..agents.agent2.knowledge_loop import KnowledgeLoopAgent


# ============================================
# 路由器
# ============================================
router = APIRouter(prefix="/api/v1/expert", tags=["专家修正"])

# 初始化Agent
correction_processor = CorrectionProcessor()
expert_interaction = ExpertInteractionAgent()
knowledge_loop = KnowledgeLoopAgent()


# ============================================
# 请求/响应模型
# ============================================

class ExpertCorrectionRequest(BaseModel):
    """专家修正请求"""
    failure_domain: str = Field(..., description="失效域")
    module: str = Field(..., description="失效模块")
    root_cause: str = Field(..., description="根因")
    root_cause_category: Optional[str] = Field(None, description="根因类别")
    failure_mode: Optional[str] = Field(None, description="失效模式")
    failure_mechanism: Optional[str] = Field(None, description="失效机制")
    confidence: float = Field(1.0, description="置信度", ge=0.0, le=1.0)
    correction_reason: str = Field(..., description="修正原因", min_length=10)


class CorrectionResponse(BaseModel):
    """修正响应"""
    correction_id: str
    analysis_id: str
    status: str
    message: str


class ExpertAssignmentRequest(BaseModel):
    """专家分配请求"""
    expert_id: Optional[str] = Field(None, description="指定专家ID（可选）")
    department: Optional[str] = Field(None, description="指定部门（可选）")


class RejectCorrectionRequest(BaseModel):
    """拒绝修正请求"""
    reason: str = Field(..., description="拒绝原因", min_length=10)


# ============================================
# API端点
# ============================================

@router.post("/corrections/{analysis_id}", response_model=CorrectionResponse, tags=["专家修正"])
async def submit_correction(
    analysis_id: str,
    correction_data: ExpertCorrectionRequest,
    request: Request = None
):
    """
    提交专家修正

    允许未登录用户提交（用于演示）
    """
    from fastapi import Request

    # 尝试从request获取用户信息
    current_user = getattr(request.state, "user", None) if request else None
    logger.info(f"[Expert] 用户 {current_user.username if current_user else 'anonymous'} 提交专家修正 - 分析: {analysis_id}")

    # 构建修正数据
    correction = {
        "expert_id": current_user.user_id if current_user else "anonymous",
        "expert_name": (current_user.full_name or current_user.username) if current_user else "匿名专家",
        "failure_domain": correction_data.failure_domain,
        "module": correction_data.module,
        "root_cause": correction_data.root_cause,
        "root_cause_category": correction_data.root_cause_category,
        "failure_mode": correction_data.failure_mode,
        "failure_mechanism": correction_data.failure_mechanism,
        "confidence": correction_data.confidence,
        "correction_reason": correction_data.correction_reason,
        "submitted_at": datetime.utcnow().isoformat()
    }

    # 从数据库查询原始分析结果（如果存在）
    from ..database.connection import get_db_manager
    db_manager = get_db_manager()

    analysis = await db_manager.get_analysis_result(analysis_id)

    # 构建原始结果数据
    if analysis:
        # 如果分析结果存在，使用数据库中的数据
        final_root_cause = analysis.get("final_root_cause", {})
        original_result = {
            "failure_domain": final_root_cause.get("failure_domain", "unknown"),
            "module": final_root_cause.get("module", "unknown"),
            "root_cause": final_root_cause.get("root_cause", "unknown"),
            "confidence": final_root_cause.get("confidence", 0.0),
            "chip_model": analysis.get("chip_model", "unknown")
        }

        # 提取故障特征
        fault_features = analysis.get("fault_features", {})
        if not fault_features.get("error_codes"):
            fault_features["error_codes"] = []
        if not fault_features.get("modules"):
            fault_features["modules"] = []
    else:
        # 如果分析结果不存在（多轮对话场景），使用提交的修正数据推断原始结果
        logger.warning(f"[Expert] 分析结果不存在，使用修正数据推断原始结果: {analysis_id}")
        original_result = {
            "failure_domain": "unknown",  # 原始失效域未知
            "module": "unknown",
            "root_cause": "待分析",
            "confidence": 0.0,
            "chip_model": "XC9000"  # 默认芯片型号
        }
        fault_features = {
            "error_codes": [],
            "modules": []
        }

    # 处理修正
    result = await correction_processor.process(
        session_id=analysis_id,
        original_result=original_result,
        correction=correction,
        fault_features=fault_features
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "修正处理失败")
        )

    return CorrectionResponse(
        correction_id=result["correction_id"],
        analysis_id=analysis_id,
        status=result["status"],
        message=result.get("message", "修正提交成功")
    )


@router.get("/corrections", tags=["专家修正"])
async def list_corrections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="筛选状态"),
    current_user: User = Depends(get_current_user_required)
):
    """
    获取修正列表

    需要权限: expert_correction:read
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.EXPERT_CORRECTION_CREATE):
        # 只能查看自己提交的修正
        expert_id = current_user.user_id
    else:
        expert_id = None

    # 获取待处理修正
    corrections = await correction_processor.get_pending_corrections(
        expert_id=expert_id
    )

    # 按状态筛选
    if status:
        corrections = [c for c in corrections if c.get("approval_status") == status]

    return {
        "success": True,
        "data": corrections[skip:skip + limit],
        "total": len(corrections),
        "skip": skip,
        "limit": limit
    }


@router.post("/corrections/{correction_id}/approve", tags=["专家修正"])
async def approve_correction(
    correction_id: str,
    comments: Optional[str] = None,
    current_user: User = Depends(get_current_user_required)
):
    """
    批准专家修正

    需要权限: expert_correction:approve
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.EXPERT_CORRECTION_APPROVE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: expert_correction:approve"
        )

    # 批准修正
    result = await correction_processor.approve_correction(
        correction_id=correction_id,
        approver_id=current_user.user_id,
        comments=comments
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "批准失败")
        )

    logger.info(f"[Expert] 用户 {current_user.username} 批准修正: {correction_id}")

    # 触发知识学习
    try:
        from ..database.connection import get_db_manager
        from ..database.models import ExpertCorrection
        from sqlalchemy import select

        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 获取修正记录
            stmt = select(ExpertCorrection).where(
                ExpertCorrection.correction_id == correction_id
            )
            correction_result = await session.execute(stmt)
            correction = correction_result.scalar_one_or_none()

            if correction:
                # 获取原始分析结果以获取故障特征
                analysis = await db_manager.get_analysis_result(correction.analysis_id)
                fault_features = analysis.get("fault_features", {}) if analysis else {}

                # 添加原始日志到故障特征（如果存在）
                if analysis and analysis.get("raw_log"):
                    fault_features["raw_log"] = analysis["raw_log"]

                # 构建学习数据
                learning_result = await knowledge_loop.learn_from_correction(
                    session_id=correction.analysis_id,
                    chip_model=correction.original_result.get("chip_model", ""),
                    original_result=correction.original_result,
                    correction={
                        "corrected_result": correction.corrected_result,
                        "correction_reason": correction.correction_reason,
                        "submitted_by": correction.submitted_by
                    },
                    fault_features=fault_features
                )

                logger.info(f"[Expert] 知识学习完成 - {learning_result}")
                result["learning"] = learning_result
    except Exception as e:
        logger.error(f"[Expert] 知识学习失败: {str(e)}")
        # 不影响批准操作，只记录错误
        result["learning_error"] = str(e)

    return result


@router.post("/corrections/{correction_id}/reject", tags=["专家修正"])
async def reject_correction(
    correction_id: str,
    reject_data: RejectCorrectionRequest,
    current_user: User = Depends(get_current_user_required)
):
    """
    拒绝专家修正

    需要权限: expert_correction:reject
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.EXPERT_CORRECTION_REJECT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: expert_correction:reject"
        )

    # 拒绝修正
    result = await correction_processor.reject_correction(
        correction_id=correction_id,
        approver_id=current_user.user_id,
        reason=reject_data.reason
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "拒绝失败")
        )

    logger.info(f"[Expert] 用户 {current_user.username} 拒绝修正: {correction_id}")

    return result


@router.post("/assign/{analysis_id}", tags=["专家修正"])
async def assign_expert(
    analysis_id: str,
    assignment: ExpertAssignmentRequest,
    current_user: User = Depends(get_current_user_required)
):
    """
    分配专家处理任务

    需要权限: analysis:update
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.ANALYSIS_UPDATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: analysis:update"
        )

    # 从数据库查询分析结果
    from ..database.connection import get_db_manager
    db_manager = get_db_manager()

    analysis = await db_manager.get_analysis_result(analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"分析结果不存在: {analysis_id}"
        )

    final_root_cause = analysis.get("final_root_cause", {})
    failure_domain = final_root_cause.get("failure_domain", "unknown")
    chip_model = analysis.get("chip_model", "unknown")
    confidence = final_root_cause.get("confidence", 0.5)

    # 分配专家
    result = await expert_interaction.assign_expert(
        session_id=analysis_id,
        failure_domain=failure_domain,
        chip_model=chip_model,
        confidence=confidence,
        department=assignment.department
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "专家分配失败")
        )

    logger.info(f"[Expert] 用户 {current_user.username} 分配专家: {result.get('expert_name')}")

    return result


@router.get("/experts", tags=["专家修正"])
async def list_experts(
    department: Optional[str] = Query(None, description="筛选部门"),
    failure_domain: Optional[str] = Query(None, description="筛选失效域"),
    current_user: User = Depends(get_current_user_required)
):
    """
    获取可用专家列表

    需要权限: user:read
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.USER_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: user:read"
        )

    # 获取可用专家
    experts = await expert_interaction.get_available_experts(
        department=department,
        failure_domain=failure_domain
    )

    return {
        "success": True,
        "data": experts
    }


@router.get("/knowledge/statistics", tags=["专家修正"])
async def get_knowledge_statistics(
    current_user: User = Depends(get_current_user_required)
):
    """
    获取知识学习统计

    需要权限: audit_log:read
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.AUDIT_LOG_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: audit_log:read"
        )

    # 获取统计
    stats = await knowledge_loop.get_learning_statistics()

    return {
        "success": True,
        "data": stats
    }


@router.get("/workload/{expert_id}", tags=["专家修正"])
async def get_expert_workload(
    expert_id: str,
    current_user: User = Depends(get_current_user_required)
):
    """
    获取专家工作负载

    需要权限: user:read
    """
    # 检查权限
    if not current_user.has_permission(SystemPermissions.USER_READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要权限: user:read"
        )

    # 获取工作负载
    workload = await expert_interaction.get_expert_workload(expert_id)

    return {
        "success": True,
        "data": workload
    }
