"""
多轮对话功能 API 路由

提供以下接口：
- POST /api/v1/analysis/{session_id}/message - 添加消息并触发分析
- GET /api/v1/analysis/{session_id}/messages - 获取对话历史
- POST /api/v1/analysis/{session_id}/correct - 纠正之前的信息
- GET /api/v1/analysis/{session_id}/timeline - 获取分析时间线
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger

from ..agents.multi_turn_handler import multi_turn_handler

router = APIRouter(prefix="/api/v1/analysis", tags=["多轮对话"])


# ============================================
# 请求/响应模型
# ============================================

class MessageRequest(BaseModel):
    """添加消息请求"""
    content: str = Field(..., description="消息内容")
    content_type: str = Field(default="text", description="内容类型: text, log, correction_data")
    correction_target: Optional[int] = Field(default=None, description="如果是纠正，指定要纠正的消息ID")
    chip_model: Optional[str] = Field(default=None, description="芯片型号（可选）")


class CorrectionRequest(BaseModel):
    """纠正信息请求"""
    target_message_id: int = Field(..., description="要纠正的消息ID")
    corrected_content: str = Field(..., description="纠正后的内容")
    reason: Optional[str] = Field(default=None, description="纠正原因")


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: int
    session_id: str
    message_type: str
    sequence_number: int
    content: str
    content_type: Optional[str]
    created_at: datetime
    is_correction: bool
    corrected_message_id: Optional[int]


class ConversationResponse(BaseModel):
    """对话历史响应"""
    success: bool
    session_id: str
    messages: List[Dict[str, Any]]
    current_analysis: Optional[Dict[str, Any]]
    total_messages: int


class TimelineEntry(BaseModel):
    """时间线条目"""
    snapshot_id: int
    message_id: int
    created_at: datetime
    analysis_summary: Dict[str, Any]
    accumulated_info_count: int


class TimelineResponse(BaseModel):
    """时间线响应"""
    success: bool
    session_id: str
    timeline: List[TimelineEntry]
    total_entries: int


# ============================================
# API 端点
# ============================================

@router.post("/{session_id}/message", response_model=Dict[str, Any])
async def add_message(
    session_id: str,
    request: MessageRequest
):
    """
    添加用户消息并触发分析

    Args:
        session_id: 会话ID
        request: 消息请求

    Returns:
        处理结果，包含分析结果和系统响应
    """
    logger.info(f"[MultiTurn API] 收到消息 - session: {session_id}, type: {request.content_type}")

    try:
        # 验证会话是否存在
        # 这里可以添加会话验证逻辑

        # 处理消息
        result = await multi_turn_handler.handle_user_message(
            session_id=session_id,
            content=request.content,
            content_type=request.content_type,
            correction_target=request.correction_target,
            user_id=None,  # 可以从认证上下文获取
            chip_model=request.chip_model
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "处理消息失败")
            )

        logger.info(f"[MultiTurn API] 消息处理成功 - message_id: {result['message_id']}")

        return {
            "success": True,
            "message_id": result["message_id"],
            "sequence_number": result["sequence_number"],
            "analysis_result": result["analysis_result"],
            "system_response": result["system_response"],
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MultiTurn API] 处理消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理消息失败: {str(e)}"
        )


@router.get("/{session_id}/messages", response_model=ConversationResponse)
async def get_conversation(
    session_id: str
):
    """
    获取会话的完整对话历史

    Args:
        session_id: 会话ID

    Returns:
        对话历史，包含所有消息和当前分析结果
    """
    logger.info(f"[MultiTurn API] 获取对话历史 - session: {session_id}")

    try:
        result = await multi_turn_handler.get_conversation_history(session_id)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"会话不存在: {session_id}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MultiTurn API] 获取对话历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话历史失败: {str(e)}"
        )


@router.post("/{session_id}/correct", response_model=Dict[str, Any])
async def correct_information(
    session_id: str,
    request: CorrectionRequest
):
    """
    纠正之前输入的信息

    Args:
        session_id: 会话ID
        request: 纠正请求

    Returns:
        纠正后的处理结果
    """
    logger.info(f"[MultiTurn API] 纠正信息 - session: {session_id}, target: {request.target_message_id}")

    try:
        # 使用 add_message 接口，将 correction_target 设置为 target_message_id
        result = await multi_turn_handler.handle_user_message(
            session_id=session_id,
            content=request.corrected_content,
            content_type="correction_data",
            correction_target=request.target_message_id,
            user_id=None
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="纠正信息失败"
            )

        return {
            "success": True,
            "message": "信息已纠正，分析已重新运行",
            "corrected_message_id": request.target_message_id,
            "new_message_id": result["message_id"],
            "analysis_result": result["analysis_result"],
            "system_response": result["system_response"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MultiTurn API] 纠正信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"纠正信息失败: {str(e)}"
        )


@router.get("/{session_id}/timeline", response_model=TimelineResponse)
async def get_analysis_timeline(
    session_id: str
):
    """
    获取分析时间线

    Args:
        session_id: 会话ID

    Returns:
        分析时间线，展示每次分析的变化
    """
    logger.info(f"[MultiTurn API] 获取分析时间线 - session: {session_id}")

    try:
        result = await multi_turn_handler.get_analysis_timeline(session_id)

        return result

    except Exception as e:
        logger.error(f"[MultiTurn API] 获取分析时间线失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分析时间线失败: {str(e)}"
        )


@router.post("/{session_id}/rollback", response_model=Dict[str, Any])
async def rollback_to_message(
    session_id: str,
    to_message_id: int,
    reason: Optional[str] = None
):
    """
    回滚到指定消息状态

    Args:
        session_id: 会话ID
        to_message_id: 回滚到的目标消息ID
        reason: 回滚原因（可选）

    Returns:
        回滚结果
    """
    logger.info(f"[MultiTurn API] 回滚会话 - session: {session_id}, to_message: {to_message_id}")

    try:
        # TODO: 实现回滚逻辑
        # 1. 删除指定消息之后的所有消息
        # 2. 删除指定快照之后的所有快照
        # 3. 恢复到指定消息时的分析状态

        return {
            "success": True,
            "message": "回滚功能待实现",
            "session_id": session_id,
            "rolled_back_to": to_message_id
        }

    except Exception as e:
        logger.error(f"[MultiTurn API] 回滚失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回滚失败: {str(e)}"
        )
