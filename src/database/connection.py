"""
芯片失效分析AI Agent系统 - 数据库连接配置
"""
import traceback
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import select
from loguru import logger


# ============================================
# 基础模型基类 - 从models.py导入
# ============================================
# 延迟导入以避免循环依赖
# 实际Base在models.py中定义为: class Base(AsyncAttrs, DeclarativeBase)

def get_base():
    """获取Base类（延迟导入）"""
    from src.database.models import Base as ModelBase
    return ModelBase

# 对于向后兼容，提供一个Base的引用
# 注意：这个变量会在首次使用时被初始化
Base = None


class DatabaseConfig:
    """数据库配置类"""

    def __init__(self):
        from src.config.settings import get_settings
        self.settings = get_settings()

    @property
    def database_url(self) -> str:
        """获取数据库URL"""
        return self.settings.DATABASE_URL

    @property
    def redis_url(self) -> str:
        """获取Redis URL"""
        return self.settings.REDIS_URL


# ============================================
# 数据库引擎管理
# ============================================
class DatabaseManager:
    """数据库管理器 - 单例模式"""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._engine is not None:
            return

        config = DatabaseConfig()
        self._engine = create_async_engine(
            config.database_url,
            echo=False,  # 生产环境设置为False
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    @property
    def engine(self):
        """获取数据库引擎"""
        return self._engine

    @property
    def session_factory(self):
        """获取会话工厂"""
        return self._session_factory

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话（上下文管理器）"""
        async with self._session_factory() as session:
            yield session

    async def close(self):
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()

    async def initialize(self):
        """初始化数据库表"""
        from src.database.models import Base
        from src.database.rbac_models import (
            User, Role, Permission, UserSession
        )
        # 确保所有模型都已导入并注册到Base.metadata
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("[DatabaseManager] 数据库表初始化完成")

    async def store_analysis_result(
        self,
        session_id: str,
        chip_model: str,
        analysis_result: Dict[str, Any],
        processing_duration: Optional[float] = None,
        started_at: Optional['datetime'] = None
    ):
        """存储分析结果到数据库"""
        from src.database.models import AnalysisResult as AnalysisResultModel
        from datetime import datetime
        import uuid

        logger.info(f"[DatabaseManager] 开始存储分析结果 - session: {session_id}, chip: {chip_model}")
        logger.info(f"[DatabaseManager] analysis_result keys: {list(analysis_result.keys())}")

        # 调试：检查 infer_report
        infer_report_value = analysis_result.get("infer_report")
        logger.info(f"[DatabaseManager] infer_report 值: {infer_report_value is not None}, 长度: {len(infer_report_value) if infer_report_value else 0}")

        logger.info(f"[DatabaseManager] final_root_cause type: {type(analysis_result.get('final_root_cause'))}")
        logger.info(f"[DatabaseManager] final_root_cause value: {analysis_result.get('final_root_cause')}")
        if processing_duration is not None:
            logger.info(f"[DatabaseManager] 处理时长: {processing_duration:.2f}秒")

        async with self._session_factory() as session:
            try:
                # 检查是否已存在
                stmt = select(AnalysisResultModel).where(
                    AnalysisResultModel.session_id == session_id
                )
                existing = await session.execute(stmt)
                existing_result = existing.scalar_one_or_none()

                logger.info(f"[DatabaseManager] 查询现有记录 - 找到: {existing_result is not None}")

                if existing_result:
                    # 更新现有记录
                    logger.info(f"[DatabaseManager] 更新现有记录")

                    # 从analysis_result中提取数据并映射到数据库字段
                    final_root_cause = analysis_result.get("final_root_cause", {})

                    # 更新状态字段
                    existing_result.status = "completed"

                    # 更新推理结果字段
                    existing_result.failure_domain = final_root_cause.get("failure_domain")
                    existing_result.root_cause = final_root_cause.get("root_cause")
                    existing_result.root_cause_category = final_root_cause.get("root_cause_category")
                    existing_result.confidence = final_root_cause.get("confidence", 0.0)

                    # 更新推理步骤和AI报告
                    existing_result.infer_trace = analysis_result.get("infer_trace", {})
                    existing_result.infer_report = analysis_result.get("infer_report")

                    existing_result.updated_at = datetime.now()
                else:
                    # 创建新记录
                    logger.info(f"[DatabaseManager] 创建新记录")

                    # 从analysis_result中提取数据
                    final_root_cause = analysis_result.get("final_root_cause", {})
                    fault_features = analysis_result.get("fault_features", {})

                    # 生成唯一的analysis_id
                    now = datetime.now()
                    date_str = now.strftime("%Y%m%d")
                    analysis_id = f"FA-{date_str}-{chip_model}-{str(uuid.uuid4())[:8]}"

                    db_result = AnalysisResultModel(
                        analysis_id=analysis_id,
                        session_id=session_id,
                        chip_model=chip_model,
                        fault_features=fault_features,
                        raw_log=analysis_result.get("raw_log"),
                        status="completed",
                        # 推理结果字段
                        failure_domain=final_root_cause.get("failure_domain"),
                        root_cause=final_root_cause.get("root_cause"),
                        root_cause_category=final_root_cause.get("root_cause_category"),
                        confidence=final_root_cause.get("confidence", 0.0),
                        reasoning_sources=analysis_result.get("infer_trace", {}),
                        # AI分析报告和推理步骤
                        infer_trace=analysis_result.get("infer_trace", {}),
                        infer_report=analysis_result.get("infer_report"),
                        # 处理时长相关字段
                        processing_duration=processing_duration,
                        started_at=started_at,
                        created_at=now,
                        updated_at=now
                    )
                    session.add(db_result)

                await session.commit()
                logger.info(f"[DatabaseManager] 分析结果已存储 - session: {session_id}")

            except Exception as e:
                await session.rollback()
                logger.error(f"[DatabaseManager] 存储分析结果失败: {str(e)}")
                logger.error(traceback.format_exc())
                raise

    async def get_analysis_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """从数据库获取分析结果"""
        from src.database.models import AnalysisResult as AnalysisResultModel

        async with self._session_factory() as session:
            try:
                # 先用ORM查询主要数据
                stmt = select(AnalysisResultModel).where(
                    AnalysisResultModel.session_id == session_id
                )
                result = await session.execute(stmt)
                db_result = result.scalar_one_or_none()

                if not db_result:
                    return None

                # 直接用SQL查询 infer_report（ORM可能未识别新字段）
                infer_report = None
                infer_trace = db_result.infer_trace or db_result.reasoning_sources or {}

                try:
                    from sqlalchemy import text
                    sql_result = await session.execute(text("""
                        SELECT infer_report, infer_trace
                        FROM analysis_results
                        WHERE session_id = :sid
                    """), {"sid": session_id})
                    sql_row = sql_result.first()
                    logger.info(f"[DatabaseManager] SQL查询结果: has_row={sql_row is not None}")
                    if sql_row:
                        infer_report = sql_row[0]  # infer_report
                        logger.info(f"[DatabaseManager] infer_report from SQL: {infer_report is not None}, len={len(infer_report) if infer_report else 0}")
                        if sql_row[1]:  # infer_trace (JSONB)
                            import json
                            if isinstance(sql_row[1], str):
                                infer_trace = json.loads(sql_row[1])
                            else:
                                infer_trace = sql_row[1]
                except Exception as e:
                    logger.warning(f"[DatabaseManager] SQL查询infer_report失败，使用ORM值: {e}")
                    import traceback
                    logger.warning(traceback.format_exc())

                # 构建final_root_cause对象
                final_root_cause = {
                    "failure_domain": db_result.failure_domain,
                    "root_cause": db_result.root_cause,
                    "root_cause_category": db_result.root_cause_category,
                    "confidence": float(db_result.confidence) if db_result.confidence else 0.0
                }

                return {
                    "session_id": db_result.session_id,
                    "chip_model": db_result.chip_model,
                    "fault_features": db_result.fault_features or {},
                    "final_root_cause": final_root_cause,
                    "need_expert": (db_result.confidence or 0) < 0.7,  # 根据置信度判断
                    "infer_report": infer_report,  # 从SQL查询获取
                    "infer_trace": infer_trace,  # 优先使用SQL查询的infer_trace
                    "expert_correction": db_result.expert_correction_id,
                    "created_at": db_result.created_at.isoformat() if db_result.created_at else None
                }

            except Exception as e:
                logger.error(f"[DatabaseManager] 获取分析结果失败: {str(e)}")
                raise

    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取系统统计数据

        Returns:
            包含今日分析次数、成功率、平均耗时等统计数据的字典
        """
        from src.database.models import AnalysisResult as AnalysisResultModel
        from datetime import datetime, timedelta

        async with self._session_factory() as session:
            try:
                # 获取今天的日期（从午夜开始）
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                yesterday = today - timedelta(days=1)

                logger.info(f"[DatabaseManager] 查询统计数据 - 今天: {today}, 昨天: {yesterday}")

                # 今日分析次数
                stmt_today = select(AnalysisResultModel).where(
                    AnalysisResultModel.created_at >= today
                )
                result_today = await session.execute(stmt_today)
                today_results = result_today.scalars().all()
                today_count = len(today_results)

                logger.info(f"[DatabaseManager] 今日分析记录数: {today_count}")

                # 查询总记录数（用于调试）
                stmt_all = select(AnalysisResultModel)
                result_all = await session.execute(stmt_all)
                all_results = result_all.scalars().all()
                total_count_debug = len(all_results)

                logger.info(f"[DatabaseManager] 数据库总记录数: {total_count_debug}")

                # 如果有记录，打印第一条记录的时间
                if total_count_debug > 0:
                    first_record = all_results[0]
                    logger.info(f"[DatabaseManager] 第一条记录时间: {first_record.created_at}")

                # 昨日分析次数（用于计算变化率）
                stmt_yesterday = select(AnalysisResultModel).where(
                    AnalysisResultModel.created_at >= yesterday,
                    AnalysisResultModel.created_at < today
                )
                result_yesterday = await session.execute(stmt_yesterday)
                yesterday_results = result_yesterday.scalars().all()
                yesterday_count = len(yesterday_results)

                logger.info(f"[DatabaseManager] 昨日分析记录数: {yesterday_count}")

                # 计算变化率
                today_change = 0.0
                if yesterday_count > 0:
                    today_change = ((today_count - yesterday_count) / yesterday_count) * 100

                # 总分析次数
                stmt_total = select(AnalysisResultModel)
                result_total = await session.execute(stmt_total)
                total_results = result_total.scalars().all()
                total_count = len(total_results)

                # 成功率（根据status和confidence判断）
                # status为"completed"且confidence >= 0.5算成功
                successful_count = sum(1 for r in total_results if r.status == "completed" and (r.confidence or 0) >= 0.5)
                success_rate = (successful_count / total_count * 100) if total_count > 0 else 0.0

                # 今日专家介入次数（status为"pending"的算需要专家介入）
                today_expert_count = sum(1 for r in today_results if r.status == "pending")

                # 昨日专家介入次数
                yesterday_expert_count = sum(1 for r in yesterday_results if r.status == "pending")

                # 专家介入变化率
                expert_change = 0.0
                if yesterday_expert_count > 0:
                    expert_change = ((today_expert_count - yesterday_expert_count) / yesterday_expert_count) * 100
                elif today_expert_count > 0:
                    expert_change = 100.0  # 从0到有，增加100%

                # 计算今日平均处理时长
                today_durations = [r.processing_duration for r in today_results if r.processing_duration is not None]
                avg_duration_today = sum(today_durations) / len(today_durations) if today_durations else 0.0

                # 计算昨日平均处理时长
                yesterday_durations = [r.processing_duration for r in yesterday_results if r.processing_duration is not None]
                avg_duration_yesterday = sum(yesterday_durations) / len(yesterday_durations) if yesterday_durations else 0.0

                # 计算平均耗时（优先使用今日数据）
                avg_duration = avg_duration_today if avg_duration_today > 0 else avg_duration_yesterday
                if avg_duration == 0.0:
                    avg_duration = 2.5  # 如果没有任何数据，使用默认值

                # 计算耗时变化率
                duration_change = 0.0
                if avg_duration_yesterday > 0:
                    duration_change = ((avg_duration_today - avg_duration_yesterday) / avg_duration_yesterday) * 100
                elif avg_duration_today > 0:
                    duration_change = 0.0  # 昨天没有数据，无法计算变化

                stats = {
                    "today_count": today_count,
                    "success_rate": round(success_rate, 1),
                    "avg_duration": round(avg_duration, 1),
                    "expert_count": today_expert_count,
                    "total_count": total_count,
                    "today_change": round(today_change, 1),
                    "duration_change": round(duration_change, 1),
                    "expert_change": round(expert_change, 1)
                }

                logger.info(f"[DatabaseManager] 统计数据: {stats}")
                return stats

            except Exception as e:
                logger.error(f"[DatabaseManager] 获取统计数据失败: {str(e)}")
                logger.error(traceback.format_exc())
                # 返回默认值
                return {
                    "today_count": 0,
                    "success_rate": 0.0,
                    "avg_duration": 0.0,
                    "expert_count": 0,
                    "total_count": 0,
                    "today_change": 0.0,
                    "duration_change": 0.0,
                    "expert_change": 0.0
                }

    async def get_analysis_history(
        self,
        limit: int = 50,
        offset: int = 0,
        chip_model: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取分析历史记录

        Args:
            limit: 返回记录数量限制
            offset: 偏移量
            chip_model: 筛选芯片型号
            date_from: 起始日期
            date_to: 结束日期

        Returns:
            包含历史记录列表和总数的字典
        """
        from src.database.models import AnalysisResult as AnalysisResultModel
        from datetime import timedelta

        async with self._session_factory() as session:
            try:
                # 构建查询
                stmt = select(AnalysisResultModel).order_by(
                    AnalysisResultModel.created_at.desc()
                )

                # 添加筛选条件
                conditions = []
                if chip_model:
                    conditions.append(AnalysisResultModel.chip_model == chip_model)
                if date_from:
                    conditions.append(AnalysisResultModel.created_at >= date_from)
                if date_to:
                    end_of_day = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
                    conditions.append(AnalysisResultModel.created_at <= end_of_day)

                if conditions:
                    from sqlalchemy import and_
                    stmt = stmt.where(and_(*conditions))

                # 获取总数
                from sqlalchemy import func
                count_stmt = select(func.count()).select_from(stmt.alias())
                total_result = await session.execute(count_stmt)
                total_count = total_result.scalar() or 0

                # 分页
                stmt = stmt.limit(limit).offset(offset)

                result = await session.execute(stmt)
                records = result.scalars().all()

                # 构建返回数据
                history_list = []
                for record in records:
                    history_list.append({
                        "analysis_id": record.analysis_id,
                        "session_id": record.session_id,
                        "chip_model": record.chip_model,
                        "failure_domain": record.failure_domain,
                        "root_cause": record.root_cause,
                        "root_cause_category": record.root_cause_category,
                        "confidence": float(record.confidence) if record.confidence else 0.0,
                        "status": record.status,
                        "processing_duration": float(record.processing_duration) if record.processing_duration else None,
                        "created_at": record.created_at.isoformat() if record.created_at else None,
                        "started_at": record.started_at.isoformat() if record.started_at else None,
                        "need_expert": (record.confidence or 0) < 0.7,
                    })

                return {
                    "records": history_list,
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset
                }

            except Exception as e:
                logger.error(f"[DatabaseManager] 获取分析历史失败: {str(e)}")
                logger.error(traceback.format_exc())
                return {
                    "records": [],
                    "total_count": 0,
                    "limit": limit,
                    "offset": offset
                }

    # ============================================
    # 多轮对话功能方法
    # ============================================
    async def get_session_messages(
        self,
        session_id: str
    ) -> list:
        """获取会话的所有消息（返回字典格式以避免序列化问题）"""
        from src.database.models import AnalysisMessage

        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AnalysisMessage)
                    .where(AnalysisMessage.session_id == session_id)
                    .order_by(AnalysisMessage.sequence_number)
                )
                messages = result.scalars().all()
                # 转换为字典格式
                return [
                    {
                        "message_id": msg.message_id,
                        "session_id": msg.session_id,
                        "message_type": msg.message_type,
                        "sequence_number": msg.sequence_number,
                        "content": msg.content,
                        "content_type": msg.content_type,
                        "is_correction": msg.is_correction,
                        "corrected_message_id": msg.corrected_message_id,
                        "extracted_fields": msg.extracted_fields or {},
                        "created_at": msg.created_at.isoformat() if msg.created_at else None
                    }
                    for msg in messages
                ]
        except Exception as e:
            logger.error(f"[DatabaseManager] 获取会话消息失败: {str(e)}")
            return []

    async def get_session_snapshots(
        self,
        session_id: str
    ) -> list:
        """获取会话的所有快照"""
        from src.database.models import AnalysisSnapshot

        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AnalysisSnapshot)
                    .where(AnalysisSnapshot.session_id == session_id)
                    .order_by(AnalysisSnapshot.created_at)
                )
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"[DatabaseManager] 获取会话快照失败: {str(e)}")
            return []

    async def get_latest_snapshot(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取会话的最新快照"""
        from src.database.models import AnalysisSnapshot

        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AnalysisSnapshot)
                    .where(AnalysisSnapshot.session_id == session_id)
                    .order_by(AnalysisSnapshot.created_at.desc())
                    .limit(1)
                )
                snapshot = result.scalar_one_or_none()

                if snapshot:
                    return {
                        "snapshot_id": snapshot.snapshot_id,
                        "message_id": snapshot.message_id,
                        "accumulated_context": snapshot.accumulated_context,
                        "analysis_result": snapshot.analysis_result,
                        "created_at": snapshot.created_at
                    }
                return None
        except Exception as e:
            logger.error(f"[DatabaseManager] 获取最新快照失败: {str(e)}")
            return None

    async def get_approved_correction(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取会话的已批准但未应用的专家修正"""
        from src.database.models import ExpertCorrection

        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(ExpertCorrection)
                    .where(
                        ExpertCorrection.analysis_id == session_id,
                        ExpertCorrection.approval_status == "approved",
                        ExpertCorrection.is_applied == False
                    )
                    .order_by(ExpertCorrection.approved_at.desc())
                    .limit(1)
                )
                correction = result.scalar_one_or_none()

                if correction:
                    return {
                        "correction_id": correction.correction_id,
                        "analysis_id": correction.analysis_id,
                        "original_result": correction.original_result,
                        "corrected_result": correction.corrected_result,
                        "correction_reason": correction.correction_reason,
                        "submitted_by": correction.submitted_by,
                        "approved_by": correction.approved_by,
                        "approval_status": correction.approval_status,
                        "is_applied": correction.is_applied,
                        "submitted_at": correction.submitted_at.isoformat() if correction.submitted_at else None,
                        "approved_at": correction.approved_at.isoformat() if correction.approved_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"[DatabaseManager] 获取专家修正失败: {str(e)}")
            return None

    async def mark_correction_as_applied(
        self,
        correction_id: str
    ) -> bool:
        """标记专家修正为已应用"""
        from src.database.models import ExpertCorrection

        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(ExpertCorrection)
                    .where(ExpertCorrection.correction_id == correction_id)
                )
                correction = result.scalar_one_or_none()

                if correction:
                    correction.is_applied = True
                    await session.commit()
                    logger.info(f"[DatabaseManager] 标记修正为已应用: {correction_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"[DatabaseManager] 标记修正为已应用失败: {str(e)}")
            return False


# ============================================
# 全局数据库管理器实例
# ============================================
db_manager = DatabaseManager()


# ============================================
# 依赖注入辅助函数
# ============================================
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于FastAPI依赖注入）"""
    async with db_manager.get_session() as session:
        yield session


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器单例"""
    return db_manager
