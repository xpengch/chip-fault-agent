"""
Agent2 - 专家交互Agent
负责协调专家介入流程，分配专家，收集专家反馈
"""

from typing import Dict, List, Any, Optional
from loguru import logger
from datetime import datetime, timedelta
from uuid import uuid4
import random

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import get_db_manager
from ...database.rbac_models import User, SystemRoles
from ...database.models import ExpertCorrection


class ExpertInteractionAgent:
    """专家交互Agent类"""

    def __init__(self):
        """初始化Agent"""
        self.name = "ExpertInteractionAgent"
        self.description = "协调专家交互流程"

    async def assign_expert(
        self,
        session_id: str,
        failure_domain: str,
        chip_model: str,
        confidence: float,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分配专家处理任务

        Args:
            session_id: 会话ID
            failure_domain: 失效域
            chip_model: 芯片型号
            confidence: Agent1的置信度
            department: 部门筛选条件

        Returns:
            分配结果
        """
        logger.info(f"[{self.name}] 分配专家 - 失效域: {failure_domain}, 芯片: {chip_model}")

        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 查找具有专家角色的用户
            stmt = select(User).join(User.roles).where(
                and_(
                    User.is_active == True,
                    Role.name == SystemRoles.EXPERT
                )
            )

            # 如果指定了部门，筛选部门
            if department:
                stmt = stmt.where(User.department == department)

            result = await session.execute(stmt)
            experts = result.scalars().all()

            if not experts:
                logger.warning(f"[{self.name}] 没有找到可用的专家")
                return {
                    "success": False,
                    "message": "没有可用的专家",
                    "expert_id": None
                }

            # 选择专家（简单随机选择，实际可以基于负载、专业领域等）
            expert = self._select_expert(experts, failure_domain, chip_model)

            if not expert:
                return {
                    "success": False,
                    "message": "没有匹配的专家",
                    "expert_id": None
                }

            # 创建专家介入记录
            correction = ExpertCorrection(
                correction_id=f"EC_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:6]}".upper(),
                analysis_id=session_id,
                original_result={},  # 稍后填充
                corrected_result={},  # 等待专家填充
                correction_reason="",
                submitted_by=expert.user_id,
                approval_status="pending",
                is_applied=False
            )

            session.add(correction)
            await session.commit()

            logger.info(f"[{self.name}] 专家分配成功 - 专家: {expert.username}")

            return {
                "success": True,
                "expert_id": expert.user_id,
                "expert_name": expert.full_name or expert.username,
                "expert_department": expert.department,
                "expert_position": expert.position,
                "correction_id": correction.correction_id,
                "assigned_at": datetime.utcnow().isoformat()
            }

    def _select_expert(
        self,
        experts: List[User],
        failure_domain: str,
        chip_model: str
    ) -> Optional[User]:
        """
        选择最合适的专家

        Args:
            experts: 专家列表
            failure_domain: 失效域
            chip_model: 芯片型号

        Returns:
            选择的专家
        """
        # 优先选择匹配部门的专家
        domain_departments = {
            "compute": ["研发部", "CPU设计部"],
            "cache": ["研发部", "缓存设计部"],
            "interconnect": ["研发部", "互连设计部"],
            "memory": ["研发部", "存储设计部"],
            "io": ["研发部", "IO设计部"]
        }

        preferred_depts = domain_departments.get(failure_domain, [])

        # 先筛选匹配部门的专家
        matched_experts = [
            e for e in experts
            if e.department and any(dept in e.department for dept in preferred_depts)
        ]

        if matched_experts:
            return random.choice(matched_experts)

        # 如果没有匹配的，随机选择一个专家
        return random.choice(experts)

    async def get_expert_workload(self, expert_id: str) -> Dict[str, Any]:
        """
        获取专家工作负载

        Args:
            expert_id: 专家用户ID

        Returns:
            工作负载信息
        """
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 查询待处理的专家修正数量
            stmt = select(ExpertCorrection).where(
                and_(
                    ExpertCorrection.submitted_by == expert_id,
                    ExpertCorrection.approval_status == "pending"
                )
            )
            result = await session.execute(stmt)
            pending_count = len(result.all())

            # 查询已完成的专家修正数量（最近30天）
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            stmt = select(ExpertCorrection).where(
                and_(
                    ExpertCorrection.submitted_by == expert_id,
                    ExpertCorrection.submitted_at >= thirty_days_ago
                )
            )
            result = await session.execute(stmt)
            completed_count = len(result.all())

            return {
                "expert_id": expert_id,
                "pending_tasks": pending_count,
                "completed_last_30_days": completed_count,
                "workload_score": pending_count * 2 + completed_count * 0.1
            }

    async def notify_expert(
        self,
        expert_id: str,
        session_id: str,
        message: str
    ) -> bool:
        """
        通知专家

        Args:
            expert_id: 专家用户ID
            session_id: 会话ID
            message: 通知消息

        Returns:
            通知是否成功
        """
        logger.info(f"[{self.name}] 通知专家 - 专家ID: {expert_id}, 会话: {session_id}")

        # TODO: 实现实际的通知机制（邮件、消息、WebSocket等）
        # 这里只是模拟
        logger.info(f"[{self.name}] 通知消息: {message}")

        return True

    async def get_available_experts(
        self,
        department: Optional[str] = None,
        failure_domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取可用的专家列表

        Args:
            department: 部门筛选
            failure_domain: 失效域筛选

        Returns:
            专家列表
        """
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            stmt = select(User).join(User.roles).where(
                and_(
                    User.is_active == True,
                    Role.name == SystemRoles.EXPERT
                )
            )

            if department:
                stmt = stmt.where(User.department == department)

            result = await session.execute(stmt)
            experts = result.scalars().all()

            expert_list = []
            for expert in experts:
                # 获取工作负载
                workload = await self.get_expert_workload(expert.user_id)

                expert_list.append({
                    "expert_id": expert.user_id,
                    "username": expert.username,
                    "full_name": expert.full_name,
                    "department": expert.department,
                    "position": expert.position,
                    "pending_tasks": workload["pending_tasks"],
                    "completed_last_30_days": workload["completed_last_30_days"],
                    "workload_score": workload["workload_score"]
                })

            # 按工作负载排序
            expert_list.sort(key=lambda x: x["workload_score"])

            return expert_list
