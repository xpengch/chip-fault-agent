"""
芯片失效分析AI Agent系统 - 数据库MCP工具
支持PostgreSQL数据存储和pgvector相似度搜索
"""

from typing import Dict, List, Any, Optional
from sqlalchemy import text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json


class DatabaseTool:
    """数据库操作工具类"""

    def __init__(self):
        """初始化工具"""
        from src.database.connection import get_db_session
        self.get_session = get_db_session

    async def store(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        存储数据到PostgreSQL

        Args:
            table_name: 目标表名
                - analysis_results: 分析结果
                - failure_cases: 失效案例
                - inference_rules: 推理规则
            data: 要存���的数据（字典格式）

        Returns:
            存储结果
        """

        async with self.get_session() as session:
            # 根据表名选择存储逻辑
            if table_name == "analysis_results":
                result = await self._store_analysis_result(session, data)
            elif table_name == "failure_cases":
                result = await self._store_failure_case(session, data)
            elif table_name == "inference_rules":
                result = await self._store_inference_rule(session, data)
            else:
                raise ValueError(f"Unknown table name: {table_name}")

            await session.commit()
            return result

    async def _store_analysis_result(
        self,
        session: AsyncSession,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """存储分析结果"""
        from src.database.models import AnalysisResult, SoCModule, SoCChip
        from uuid import uuid4

        # 查询芯片ID
        chip = await session.execute(
            text("SELECT id FROM soc_chips WHERE chip_model = :chip_model"),
            {"chip_model": data.get("chip_model")}
        )
        chip_row = chip.fetchone()
        if not chip_row:
            raise ValueError(f"Chip model not found: {data.get('chip_model')}")

        chip_id = chip_row[0]

        # 查询模块ID
        module_id = None
        if data.get("failure_module_id"):
            module_result = await session.execute(
                text("SELECT id FROM soc_modules WHERE id = :module_id"),
                {"module_id": data["failure_module_id"]}
            )
            module_row = module_result.fetchone()
            if module_row:
                module_id = str(module_row[0])

        # 查询子系统ID
        subsystem_id = None
        if data.get("failure_subsystem_id"):
            subsystem_result = await session.execute(
                text("SELECT id FROM soc_subsystems WHERE id = :subsystem_id"),
                {"subsystem_id": data["failure_subsystem_id"]}
            )
            subsystem_row = subsystem_result.fetchone()
            if subsystem_row:
                subsystem_id = str(subsystem_row[0])

        # 生成分析ID
        from datetime import datetime
        analysis_id = f"ANA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}"

        # 计算日志哈希
        import hashlib
        log_hash = hashlib.sha256(
            data.get("raw_log", "").encode()
        ).hexdigest()

        # 创建分析结果记录
        result = AnalysisResult(
            analysis_id=analysis_id,
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            chip_model=data.get("chip_model"),
            log_source=data.get("log_source", ""),
            log_hash=log_hash,
            raw_log=data.get("raw_log"),
            fault_features=data.get("fault_features", {}),
            affected_modules=data.get("affected_modules", []),
            affected_subsystems=data.get("affected_subsystems", []),
            noc_path=data.get("noc_path", []),
            noc_congestion_info=data.get("noc_congestion_info", {}),
            failure_domain=data.get("failure_domain"),
            failure_subsystem=subsystem_id,
            failure_module=module_id,
            internal_location=data.get("internal_location"),
            root_cause=data.get("root_cause"),
            root_cause_category=data.get("root_cause_category"),
            confidence=data.get("confidence"),
            matched_case_id=data.get("matched_case_id"),
            reasoning_sources=data.get("reasoning_sources", {}),
            status=data.get("status", "pending")
        )

        session.add(result)
        await session.flush()

        return {
            "success": True,
            "table": "analysis_results",
            "analysis_id": analysis_id,
            "record_id": str(result.id)
        }

    async def _store_failure_case(
        self,
        session: AsyncSession,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """存储失效案例"""
        from src.database.models import FailureCase, SoCModule, SoCSubsystem
        from uuid import uuid4

        # 查询芯片ID
        chip_result = await session.execute(
            text("SELECT id FROM soc_chips WHERE chip_model = :chip_model"),
            {"chip_model": data.get("chip_model")}
        )
        chip_row = chip_result.fetchone()
        if not chip_row:
            # 如果芯片不存在，先创建
            from src.database.models import SoCChip
            chip = SoCChip(
                chip_model=data.get("chip_model"),
                is_active=True
            )
            session.add(chip)
            await session.flush()
            chip_id = chip.id
        else:
            chip_id = chip_row[0]

        # 查询模块ID
        module_id = None
        if data.get("module_name"):
            module_result = await session.execute(
                text("SELECT id FROM soc_modules WHERE chip_model = :chip_model AND module_name = :module_name"),
                {"chip_model": data.get("chip_model"), "module_name": data.get("module_name")}
            )
            module_row = module_result.fetchone()
            if module_row:
                module_id = str(module_row[0])

        # 查询子系统ID
        subsystem_id = None
        if data.get("subsystem_name"):
            subsystem_result = await session.execute(
                text("SELECT id FROM soc_subsystems WHERE chip_model = :chip_model AND subsystem_name = :subsystem_name"),
                {"chip_model": data.get("chip_model"), "subsystem_name": data.get("subsystem_name")}
            )
            subsystem_row = subsystem_result.fetchone()
            if subsystem_row:
                subsystem_id = str(subsystem_row[0])

        # 生成案例ID
        case_id = f"CASE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}"

        # 创建失效案例记录
        result = FailureCase(
            case_id=case_id,
            chip_model=data.get("chip_model"),
            subsystem_id=subsystem_id,
            module_id=module_id,
            module_type=data.get("module_type"),
            failure_domain=data.get("failure_domain"),
            internal_location=data.get("internal_location"),
            symptoms=data.get("symptoms", ""),
            error_codes=data.get("error_codes", []),
            failure_mode=data.get("failure_mode"),
            failure_mechanism=data.get("failure_mechanism"),
            root_cause=data.get("root_cause"),
            root_cause_category=data.get("root_cause_category"),
            solution=data.get("solution"),
            test_conditions=data.get("test_conditions", {}),
            sensitivity_level=data.get("sensitivity_level", 1),
            is_verified=False
        )

        session.add(result)
        await session.flush()

        return {
            "success": True,
            "table": "failure_cases",
            "case_id": case_id,
            "record_id": str(result.id)
        }

    async def _store_inference_rule(
        self,
        session: AsyncSession,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """存储推理规则"""
        from src.database.models import InferenceRule, SoCModule, SoCSubsystem
        from uuid import uuid4

        # 查询芯片ID
        chip_result = await session.execute(
            text("SELECT id FROM soc_chips WHERE chip_model = :chip_model"),
            {"chip_model": data.get("chip_model")}
        )
        chip_row = chip_result.fetchone()
        chip_id = chip_row[0] if chip_row else None

        # 查询模块ID
        module_id = None
        if data.get("module_name"):
            module_result = await session.execute(
                text("SELECT id FROM soc_modules WHERE chip_model = :chip_model AND module_name = :module_name"),
                {"chip_model": data.get("chip_model"), "module_name": data.get("module_name")}
            )
            module_row = module_result.fetchone()
            if module_row:
                module_id = str(module_row[0])

        # 查询子系统ID
        subsystem_id = None
        if data.get("subsystem_name"):
            subsystem_result = await session.execute(
                text("SELECT id FROM soc_subsystems WHERE chip_model = :chip_model AND subsystem_name = :subsystem_name"),
                {"chip_model": data.get("chip_model"), "subsystem_name": data.get("subsystem_name")}
            )
            subsystem_row = subsystem_result.fetchone()
            if subsystem_row:
                subsystem_id = str(subsystem_row[0])

        # 生成规则ID
        rule_id = f"RULE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8]}"

        # 创建推理规则记录
        result = InferenceRule(
            rule_id=rule_id,
            rule_name=data.get("rule_name", ""),
            chip_model=data.get("chip_model"),
            subsystem_id=subsystem_id,
            module_id=module_id,
            failure_domain=data.get("failure_domain"),
            conditions=data.get("conditions", {}),
            priority=data.get("priority", 0),
            conclusion=data.get("conclusion", {}),
            confidence=data.get("confidence"),
            rule_type=data.get("rule_type", "syntax"),
            is_active=True,
            created_by=data.get("created_by", "system")
        )

        session.add(result)
        await session.flush()

        return {
            "success": True,
            "table": "inference_rules",
            "rule_id": rule_id,
            "record_id": str(result.id)
        }

    async def query(
        self,
        table_name: str,
        filters: Optional[Dict] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        从PostgreSQL查询数据

        Args:
            table_name: 目标表名
            filters: 过滤条件（字典格式）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            查询结果
        """

        async with self.get_session() as session:
            if table_name == "analysis_results":
                return await self._query_analysis_results(session, filters, limit, offset)
            elif table_name == "failure_cases":
                return await self._query_failure_cases(session, filters, limit, offset)
            elif table_name == "inference_rules":
                return await self._query_inference_rules(session, filters, limit, offset)
            else:
                raise ValueError(f"Unknown table name: {table_name}")

    async def _query_analysis_results(
        self,
        session: AsyncSession,
        filters: Optional[Dict],
        limit: int,
        offset: int
    ) -> Dict[str, Any]:
        """查询分析结果"""
        from src.database.models import AnalysisResult
        from sqlalchemy import and_, or_, desc

        query = session.query(AnalysisResult)

        # 应用过滤条件
        if filters:
            if "chip_model" in filters:
                query = query.filter(AnalysisResult.chip_model == filters["chip_model"])
            if "status" in filters:
                query = query.filter(AnalysisResult.status == filters["status"])
            if "user_id" in filters:
                query = query.filter(AnalysisResult.user_id == filters["user_id"])
            if "date_from" in filters or "date_to" in filters:
                if "date_from" in filters:
                    query = query.filter(AnalysisResult.created_at >= filters["date_from"])
                if "date_to" in filters:
                    query = query.filter(AnalysisResult.created_at <= filters["date_to"])
            if "failure_domain" in filters:
                query = query.filter(AnalysisResult.failure_domain == filters["failure_domain"])

        # 排序：按创建时间倒序
        query = query.order_by(desc(AnalysisResult.created_at))

        # 应用分页
        query = query.offset(offset).limit(limit)

        results = await query.all()

        return {
            "table": "analysis_results",
            "total": len(results),
            "results": [
                {
                    "analysis_id": r.analysis_id,
                    "session_id": r.session_id,
                    "user_id": r.user_id,
                    "chip_model": r.chip_model,
                    "failure_domain": r.failure_domain,
                    "root_cause": r.root_cause,
                    "confidence": float(r.confidence) if r.confidence else None,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in results
            ]
        }

    async def _query_failure_cases(
        self,
        session: AsyncSession,
        filters: Optional[Dict],
        limit: int,
        offset: int
    ) -> Dict[str, Any]:
        """查询失效案例"""
        from src.database.models import FailureCase

        query = session.query(FailureCase)

        # 应用过滤条件
        if filters:
            if "chip_model" in filters:
                query = query.filter(FailureCase.chip_model == filters["chip_model"])
            if "failure_domain" in filters:
                query = query.filter(FailureCase.failure_domain == filters["failure_domain"])
            if "module_type" in filters:
                query = query.filter(FailureCase.module_type == filters["module_type"])
            if "is_verified" in filters:
                query = query.filter(FailureCase.is_verified == filters["is_verified"])
            if "error_codes" in filters:
                for code in filters["error_codes"]:
                    query = query.filter(FailureCase.error_codes.contains([code]))
            if "search" in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        FailureCase.symptoms.ilike(search_term),
                        FailureCase.root_cause.ilike(search_term),
                        FailureCase.solution.ilike(search_term)
                    )
                )

        # 排序：按验证状态、创建时间
        query = query.order_by(desc(FailureCase.is_verified), desc(FailureCase.created_at))

        # 应用分页
        query = query.offset(offset).limit(limit)

        results = await query.all()

        return {
            "table": "failure_cases",
            "total": len(results),
            "results": [
                {
                    "case_id": r.case_id,
                    "chip_model": r.chip_model,
                    "module_type": r.module_type,
                    "failure_domain": r.failure_domain,
                    "symptoms": r.symptoms,
                    "error_codes": r.error_codes,
                    "failure_mode": r.failure_mode,
                    "root_cause": r.root_cause,
                    "root_cause_category": r.root_cause_category,
                    "solution": r.solution,
                    "sensitivity_level": r.sensitivity_level,
                    "is_verified": r.is_verified,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in results
            ]
        }

    async def _query_inference_rules(
        self,
        session: AsyncSession,
        filters: Optional[Dict],
        limit: int,
        offset: int
    ) -> Dict[str, Any]:
        """查询推理规则"""
        from src.database.models import InferenceRule

        query = session.query(InferenceRule)

        # 应用过滤条件
        if filters:
            if "chip_model" in filters:
                query = query.filter(InferenceRule.chip_model == filters["chip_model"])
            if "is_active" in filters:
                query = query.filter(InferenceRule.is_active == filters["is_active"])
            if "failure_domain" in filters:
                query = query.filter(InferenceRule.failure_domain == filters["failure_domain"])
            if "rule_type" in filters:
                query = query.filter(InferenceRule.rule_type == filters["rule_type"])
            if "priority_min" in filters:
                query = query.filter(InferenceRule.priority >= filters["priority_min"])
            if "priority_max" in filters:
                query = query.filter(InferenceRule.priority <= filters["priority_max"])

        # 排序：按优先级倒序
        query = query.order_by(desc(InferenceRule.priority), desc(InferenceRule.created_at))

        # 应用分页
        query = query.offset(offset).limit(limit)

        results = await query.all()

        return {
            "table": "inference_rules",
            "total": len(results),
            "results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "chip_model": r.chip_model,
                    "failure_domain": r.failure_domain,
                    "conditions": r.conditions,
                    "priority": r.priority,
                    "conclusion": r.conclusion,
                    "confidence": float(r.confidence) if r.confidence else None,
                    "rule_type": r.rule_type,
                    "is_active": r.is_active,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in results
            ]
        }

    async def vector_search(
        self,
        feature_vector: List[float],
        chip_model: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        使用pgvector进行向量相似度搜索

        Args:
            feature_vector: 特征向量
            chip_model: 芯片型号
            top_k: 返回Top-K结果
            threshold: 相似度阈值（0-1）

        Returns:
            相似案例列表及相似度
        """

        async with self.get_session() as session:
            # 使用余弦相似度搜索
            # pgvector余弦距离：1 - 余弦相似度
            # 相似度 = 1 - 距离

            query = text("""
                SELECT
                    fc.case_id,
                    fc.chip_model,
                    fc.module_type,
                    fc.failure_domain,
                    fc.symptoms,
                    fc.error_codes,
                    fc.failure_mode,
                    fc.root_cause,
                    fc.root_cause_category,
                    fc.solution,
                    fc.sensitivity_level,
                    fc.is_verified,
                    1 - (fc.embedding <=> :vector) as similarity
                FROM failure_cases fc
                JOIN soc_chips sc ON fc.chip_model = sc.chip_model
                WHERE sc.is_active = true
                  AND fc.chip_model = :chip_model
                  AND fc.embedding IS NOT NULL
                  AND (1 - (fc.embedding <=> :vector)) >= :threshold
                ORDER BY fc.embedding <=> :vector
                LIMIT :limit
            """)

            result = await session.execute(
                query,
                {
                    "vector": feature_vector,
                    "chip_model": chip_model,
                    "threshold": threshold,
                    "limit": top_k
                }
            )

            rows = result.fetchall()

            return {
                "table": "failure_cases",
                "search_type": "vector_similarity",
                "similarity_threshold": threshold,
                "top_k": top_k,
                "results": [
                    {
                        "case_id": row[0],
                        "chip_model": row[1],
                        "module_type": row[2],
                        "failure_domain": row[3],
                        "symptoms": row[4],
                        "error_codes": row[5],
                        "failure_mode": row[6],
                        "root_cause": row[7],
                        "root_cause_category": row[8],
                        "solution": row[9],
                        "sensitivity_level": row[10],
                        "is_verified": row[11],
                        "similarity": float(row[12])
                    }
                    for row in rows
                ]
            }
