"""
Agent2 - 知识循环Agent
负责从专家修正中学习，更新知识库、案例库和规则库
"""

from typing import Dict, List, Any, Optional
from loguru import logger
from datetime import datetime
from uuid import uuid4
import hashlib

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import get_db_manager
from ...database.models import (
    FailureCase, InferenceRule, ExpertCorrection
)
from ...database.rbac_models import SystemPermissions


class KnowledgeLoopAgent:
    """知识循环Agent类"""

    def __init__(self):
        """初始化Agent"""
        self.name = "KnowledgeLoopAgent"
        self.description = "从专家修正中学习并更新知识库"

    async def learn_from_correction(
        self,
        session_id: str,
        chip_model: str,
        original_result: Dict[str, Any],
        correction: Dict[str, Any],
        fault_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从专家修正中学习

        Args:
            session_id: 会话ID
            chip_model: 芯片型号
            original_result: Agent1的原始结果
            correction: 专家修正数据
            fault_features: 故障特征

        Returns:
            学习结果
        """
        logger.info(f"[{self.name}] 开始从专家修正中学习")

        updates = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "updates": []
        }

        # 1. 创建或更新失效案例
        case_result = await self._update_failure_case(
            chip_model, original_result, correction, fault_features
        )
        updates["updates"].append(case_result)
        updates["case_learned"] = case_result.get("success", False)

        # 2. 更新推理规则
        rule_result = await self._update_inference_rules(
            chip_model, original_result, correction, fault_features
        )
        updates["updates"].append(rule_result)
        updates["rules_updated"] = rule_result.get("success", False)

        # 3. 更新知识图谱（如果有Neo4j连接）
        kg_result = await self._update_knowledge_graph(
            chip_model, original_result, correction, fault_features
        )
        updates["updates"].append(kg_result)

        logger.info(f"[{self.name}] 知识学习完成 - 案例: {updates['case_learned']}, 规则: {updates['rules_updated']}")

        return updates

    async def _update_failure_case(
        self,
        chip_model: str,
        original_result: Dict[str, Any],
        correction: Dict[str, Any],
        fault_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新失效案例"""
        logger.info(f"[{self.name}] 更新失效案例")

        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 检查是否已存在相似案例
            error_codes = fault_features.get("error_codes", [])
            if not error_codes:
                return {"success": False, "message": "没有错误码，无法创建案例"}

            # 基于错误码查找相似案例
            primary_code = error_codes[0]
            stmt = select(FailureCase).where(
                and_(
                    FailureCase.chip_model == chip_model,
                    FailureCase.error_codes.any(primary_code)  # Postgres array syntax
                )
            )
            result = await session.execute(stmt)
            existing_case = result.scalar_one_or_none()

            # 获取修正后的结果
            corrected = correction.get("corrected_result", {})
            correction_reason = correction.get("correction_reason", "")

            if existing_case:
                # 更新现有案例
                existing_case.root_cause = corrected.get("root_cause", existing_case.root_cause)
                existing_case.solution = correction_reason
                existing_case.version += 1
                existing_case.updated_at = datetime.utcnow()
                existing_case.is_verified = True

                await session.commit()

                logger.info(f"[{self.name}] 更新现有案例: {existing_case.case_id}")

                return {
                    "success": True,
                    "action": "updated",
                    "case_id": existing_case.case_id,
                    "message": "案例更新成功"
                }
            else:
                # 创建新案例
                case_id = f"CASE_{primary_code}_{datetime.utcnow().strftime('%Y%m%d')}".upper()

                new_case = FailureCase(
                    case_id=case_id,
                    chip_model=chip_model,
                    failure_domain=corrected.get("failure_domain", original_result.get("failure_domain")),
                    failure_mode=corrected.get("failure_mode", "unknown"),
                    failure_mechanism=corrected.get("failure_mechanism", "unknown"),
                    root_cause=corrected.get("root_cause", ""),
                    root_cause_category=corrected.get("root_cause_category", "unknown"),
                    solution=correction_reason,
                    error_codes=error_codes,
                    symptoms=fault_features.get("fault_description", ""),
                    is_verified=True,
                    verified_by=correction.get("submitted_by", "system"),
                    verified_at=datetime.utcnow(),
                    sensitivity_level=1
                )

                session.add(new_case)
                await session.commit()

                logger.info(f"[{self.name}] 创建新案例: {case_id}")

                return {
                    "success": True,
                    "action": "created",
                    "case_id": case_id,
                    "message": "案例创建成功"
                }

    async def _update_inference_rules(
        self,
        chip_model: str,
        original_result: Dict[str, Any],
        correction: Dict[str, Any],
        fault_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新推理规则"""
        logger.info(f"[{self.name}] 更新推理规则")

        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 获取修正后的结果
            corrected = correction.get("corrected_result", {})
            error_codes = fault_features.get("error_codes", [])

            if not error_codes:
                return {"success": False, "message": "没有错误码，无法创建规则"}

            # 为每个错误码创建或更新规则
            rules_created = []
            for error_code in error_codes[:3]:  # 限制最多创建3条规则
                # 检查是否已存在规则
                stmt = select(InferenceRule).where(
                    and_(
                        InferenceRule.chip_model == chip_model,
                        InferenceRule.is_active == True
                    )
                )
                result = await session.execute(stmt)
                existing_rules = result.scalars().all()

                # 检查规则条件是否匹配
                rule_exists = False
                for rule in existing_rules:
                    conditions = rule.conditions
                    if conditions.get("error_codes") and error_code in conditions.get("error_codes", []):
                        # 更新现有规则
                        rule.conclusion = {
                            "failure_domain": corrected.get("failure_domain"),
                            "failure_module": corrected.get("module"),
                            "root_cause": corrected.get("root_cause"),
                            "confidence": 1.0  # 专家修正后置信度为1.0
                        }
                        rule.updated_at = datetime.utcnow()
                        rule_exists = True
                        rules_created.append(rule.rule_id)
                        break

                if not rule_exists:
                    # 创建新规则
                    rule_id = f"RULE_{error_code}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}".upper()

                    new_rule = InferenceRule(
                        rule_id=rule_id,
                        rule_name=f"{error_code} 修正规则",
                        chip_model=chip_model,
                        conditions={
                            "error_codes": [error_code],
                            "min_confidence": 0.0
                        },
                        conclusion={
                            "failure_domain": corrected.get("failure_domain"),
                            "failure_module": corrected.get("module"),
                            "root_cause": corrected.get("root_cause"),
                            "confidence": 1.0
                        },
                        confidence=1.0,
                        priority=100,  # 专家修正的规则优先级最高
                        rule_type="expert_learned",
                        is_active=True,
                        created_by=correction.get("submitted_by", "system")
                    )

                    session.add(new_rule)
                    rules_created.append(rule_id)

            await session.commit()

            logger.info(f"[{self.name}] 创建/更新规则: {len(rules_created)} 条")

            return {
                "success": len(rules_created) > 0,
                "rules_created": rules_created,
                "message": f"规则更新成功: {len(rules_created)} 条"
            }

    async def _update_knowledge_graph(
        self,
        chip_model: str,
        original_result: Dict[str, Any],
        correction: Dict[str, Any],
        fault_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新知识图谱"""
        logger.info(f"[{self.name}] 更新知识图谱")

        # TODO: 实现Neo4j知识图谱更新
        # 这里需要连接到Neo4j并更新节点和关系

        # 简化实现：记录日志
        corrected = correction.get("corrected_result", {})

        kg_update = {
            "node_type": "failure_pattern",
            "properties": {
                "error_codes": fault_features.get("error_codes", []),
                "failure_domain": corrected.get("failure_domain"),
                "root_cause": corrected.get("root_cause"),
                "chip_model": chip_model
            },
            "relationship": "LEADS_TO"
        }

        logger.info(f"[{self.name}] 知识图谱更新: {kg_update}")

        return {
            "success": True,
            "message": "知识图谱更新记录成功",
            "kg_update": kg_update
        }

    async def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # 统计专家学习的规则数量
            stmt = select(InferenceRule).where(
                InferenceRule.rule_type == "expert_learned"
            )
            result = await session.execute(stmt)
            learned_rules = len(result.all())

            # 统计专家验证的案例数量
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            stmt = select(FailureCase).where(
                and_(
                    FailureCase.is_verified == True,
                    FailureCase.verified_at >= thirty_days_ago
                )
            )
            result = await session.execute(stmt)
            verified_cases = len(result.all())

            return {
                "learned_rules": learned_rules,
                "verified_cases_last_30_days": verified_cases,
                "timestamp": datetime.utcnow().isoformat()
            }
