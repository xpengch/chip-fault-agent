"""
Agent2 - 修正处理器
处理专家提交的修正数据，验证并应用修正
"""

from typing import Dict, List, Any, Optional
from loguru import logger
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import get_db_manager
from ...database.models import ExpertCorrection
from ...database.rbac_models import User, SystemRoles


class CorrectionProcessor:
    """修正处理器类"""

    def __init__(self):
        """初始化处理器"""
        self.name = "CorrectionProcessor"
        self.description = "处理专家修正数据"

    async def process(
        self,
        session_id: str,
        original_result: Dict[str, Any],
        correction: Dict[str, Any],
        fault_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理专家修正

        Args:
            session_id: 会话ID
            original_result: Agent1的原始结果
            correction: 专家修正数据
            fault_features: 故障特征

        Returns:
            处理结果
        """
        logger.info(f"[{self.name}] 处理专家修正")

        # 1. 验证修正数据
        validation = await self._validate_correction(correction, original_result)
        if not validation["valid"]:
            return {
                "success": False,
                "status": "rejected",
                "message": validation["message"]
            }

        # 2. 创建修正记录
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            correction_record = ExpertCorrection(
                correction_id=f"EC_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:6]}".upper(),
                analysis_id=session_id,
                original_result=original_result,
                corrected_result=correction,
                correction_reason=correction.get("correction_reason", ""),
                submitted_by=correction.get("expert_id", "system"),
                approval_status="approved",  # 专家提交的默认为已批准
                is_applied=False
            )

            session.add(correction_record)
            await session.commit()
            await session.refresh(correction_record)

            logger.info(f"[{self.name}] 修正记录创建成功: {correction_record.correction_id}")

            return {
                "success": True,
                "status": "approved",
                "correction_id": correction_record.correction_id,
                "corrected_result": correction,
                "message": "修正处理成功"
            }

    async def _validate_correction(
        self,
        correction: Dict[str, Any],
        original_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证修正数据"""
        # 检查必需字段
        required_fields = ["failure_domain", "root_cause"]
        for field in required_fields:
            if field not in correction:
                return {
                    "valid": False,
                    "message": f"缺少必需字段: {field}"
                }

        # 验证失效域
        valid_domains = ["compute", "cache", "interconnect", "memory", "io", "unknown"]
        if correction["failure_domain"] not in valid_domains:
            return {
                "valid": False,
                "message": f"无效的失效域: {correction['failure_domain']}"
            }

        # 验证根因不为空
        if not correction["root_cause"] or correction["root_cause"].strip() == "":
            return {
                "valid": False,
                "message": "根因不能为空"
            }

        # 检查置信度
        if "confidence" in correction:
            confidence = correction["confidence"]
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                return {
                    "valid": False,
                    "message": "置信度必须在0-1之间"
                }

        return {
            "valid": True,
            "message": "验证通过"
        }

    async def apply_correction(
        self,
        correction_id: str
    ) -> Dict[str, Any]:
        """
        应用修正到分析结果

        Args:
            correction_id: 修正ID

        Returns:
            应用结果
        """
        logger.info(f"[{self.name}] 应用修正: {correction_id}")

        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 查询修正记录
            stmt = select(ExpertCorrection).where(
                ExpertCorrection.correction_id == correction_id
            )
            result = await session.execute(stmt)
            correction = result.scalar_one_or_none()

            if not correction:
                return {
                    "success": False,
                    "message": "修正记录不存在"
                }

            # 检查状态
            if correction.approval_status != "approved":
                return {
                    "success": False,
                    "message": f"修正未批准，状态: {correction.approval_status}"
                }

            # 标记为已应用
            correction.is_applied = True
            await session.commit()

            logger.info(f"[{self.name}] 修正应用成功: {correction_id}")

            return {
                "success": True,
                "message": "修正应用成功",
                "corrected_result": correction.corrected_result
            }

    async def get_pending_corrections(
        self,
        expert_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取待处理的修正

        Args:
            expert_id: 筛选专家ID

        Returns:
            待处理修正列表
        """
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            stmt = select(ExpertCorrection).where(
                ExpertCorrection.approval_status == "pending"
            )

            if expert_id:
                stmt = stmt.where(ExpertCorrection.submitted_by == expert_id)

            stmt = stmt.order_by(ExpertCorrection.submitted_at.desc())
            result = await session.execute(stmt)
            corrections = result.scalars().all()

            correction_list = []
            for correction in corrections:
                correction_list.append({
                    "correction_id": correction.correction_id,
                    "analysis_id": correction.analysis_id,
                    "submitted_by": correction.submitted_by,
                    "submitted_at": correction.submitted_at.isoformat(),
                    "correction_reason": correction.correction_reason,
                    "original_result": correction.original_result,
                    "corrected_result": correction.corrected_result
                })

            return correction_list

    async def approve_correction(
        self,
        correction_id: str,
        approver_id: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批准修正

        Args:
            correction_id: 修正ID
            approver_id: 批准者ID
            comments: 批准意见

        Returns:
            批准结果
        """
        logger.info(f"[{self.name}] 批准修正: {correction_id} by {approver_id}")

        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 查询修正记录
            stmt = select(ExpertCorrection).where(
                ExpertCorrection.correction_id == correction_id
            )
            result = await session.execute(stmt)
            correction = result.scalar_one_or_none()

            if not correction:
                return {
                    "success": False,
                    "message": "修正记录不存在"
                }

            # 更新状态
            correction.approval_status = "approved"
            correction.approved_by = approver_id
            correction.approved_at = datetime.utcnow()

            # 添加审批意见到修正原因
            if comments:
                original_reason = correction.correction_reason or ""
                correction.correction_reason = f"{original_reason}\n\n[审批意见] {comments}"

            await session.commit()

            logger.info(f"[{self.name}] 修正批准成功: {correction_id}")

            return {
                "success": True,
                "message": "修正批准成功"
            }

    async def reject_correction(
        self,
        correction_id: str,
        approver_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        拒绝修正

        Args:
            correction_id: 修正ID
            approver_id: 批准者ID
            reason: 拒绝原因

        Returns:
            拒绝结果
        """
        logger.info(f"[{self.name}] 拒绝修正: {correction_id} by {approver_id}")

        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 查询修正记录
            stmt = select(ExpertCorrection).where(
                ExpertCorrection.correction_id == correction_id
            )
            result = await session.execute(stmt)
            correction = result.scalar_one_or_none()

            if not correction:
                return {
                    "success": False,
                    "message": "修正记录不存在"
                }

            # 更新状态
            correction.approval_status = "rejected"
            correction.approved_by = approver_id
            correction.approved_at = datetime.utcnow()

            # 添加拒绝原因
            original_reason = correction.correction_reason or ""
            correction.correction_reason = f"{original_reason}\n\n[拒绝原因] {reason}"

            await session.commit()

            logger.info(f"[{self.name}] 修正拒绝成功: {correction_id}")

            return {
                "success": True,
                "message": "修正拒绝成功"
            }
