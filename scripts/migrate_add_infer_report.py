"""
数据库迁移脚本：添加 infer_report 和 infer_trace 字段
运行方式：python -m scripts.migrate_add_infer_report
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import text
from src.database.connection import get_db_manager


async def migrate():
    """执行数据库迁移"""
    logger.info("开始数据库迁移：添加 infer_report 和 infer_trace 字段")

    db_manager = get_db_manager()
    await db_manager.initialize()

    async with db_manager._engine.begin() as conn:
        # 检查列是否已存在
        try:
            # 检查 infer_report 列
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'analysis_results' AND column_name = 'infer_report'
            """))
            infer_report_exists = result.first() is not None

            # 检查 infer_trace 列
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'analysis_results' AND column_name = 'infer_trace'
            """))
            infer_trace_exists = result.first() is not None

            if infer_report_exists and infer_trace_exists:
                logger.info("字段已存在，无需迁移")
                return

            # 添加 infer_report 列
            if not infer_report_exists:
                logger.info("添加 infer_report 列...")
                await conn.execute(text("""
                    ALTER TABLE analysis_results
                    ADD COLUMN infer_report TEXT
                """))
                logger.info("✓ infer_report 列添加成功")

            # 添加 infer_trace 列
            if not infer_trace_exists:
                logger.info("添加 infer_trace 列...")
                await conn.execute(text("""
                    ALTER TABLE analysis_results
                    ADD COLUMN infer_trace JSONB DEFAULT '{}'::jsonb
                """))
                logger.info("✓ infer_trace 列添加成功")

            logger.info("数据库迁移完成！")

        except Exception as e:
            logger.error(f"迁移失败: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
