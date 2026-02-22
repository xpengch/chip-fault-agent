"""
数据库迁移脚本 - 添加处理时长字段
执行时间: 2026-02-21
"""
import asyncio
from sqlalchemy import text
from src.database.connection import db_manager
from loguru import logger


async def run_migration():
    """执行迁移"""
    logger.info("开始执行数据库迁移...")

    # 迁移SQL
    migration_sql = """
    ALTER TABLE analysis_results
    ADD COLUMN IF NOT EXISTS processing_duration NUMERIC(10, 3),
    ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE;

    COMMENT ON COLUMN analysis_results.processing_duration IS '分析处理时长（秒）';
    COMMENT ON COLUMN analysis_results.started_at IS '分析开始时间';
    """

    try:
        async with db_manager.engine.begin() as conn:
            await conn.execute(text(migration_sql))

        logger.success("数据库迁移完成！")
        print("成功添加 processing_duration 和 started_at 字段")

    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(run_migration())
