"""
多轮对话功能 - 数据库迁移脚本

创建以下新表：
1. analysis_messages - 存储用户交互消息
2. analysis_snapshots - 存储分析快照
3. analysis_conflicts - 存储冲突记录
"""

import asyncio
import sys
sys.path.insert(0, 'D:/ai_dir/chip_fault_agent')

from src.database.connection import get_db_manager
from sqlalchemy import text
from loguru import logger


async def migrate():
    """执行迁移"""
    db = get_db_manager()
    await db.initialize()

    async with db._engine.begin() as conn:
        # ==================== 1. 创建 analysis_messages 表 ====================
        logger.info("[迁移] 检查/创建 analysis_messages 表...")

        # 检查表是否存在
        check_table = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'analysis_messages'
            )
        """))
        table_exists = check_table.scalar()

        if not table_exists:
            logger.info("[迁移] 创建 analysis_messages 表...")
            await conn.execute(text("""
                CREATE TABLE analysis_messages (
                    message_id BIGSERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    message_type VARCHAR(50) NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    content_type VARCHAR(50),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    is_correction BOOLEAN DEFAULT FALSE,
                    corrected_message_id BIGINT,
                    FOREIGN KEY (corrected_message_id) REFERENCES analysis_messages(message_id)
                )
            """))

            # 创建索引
            await conn.execute(text("""
                CREATE INDEX idx_analysis_messages_session
                ON analysis_messages(session_id)
            """))
            await conn.execute(text("""
                CREATE INDEX idx_analysis_messages_sequence
                ON analysis_messages(session_id, sequence_number)
            """))
            await conn.execute(text("""
                CREATE INDEX idx_analysis_messages_correction
                ON analysis_messages(corrected_message_id)
                WHERE corrected_message_id IS NOT NULL
            """))
            logger.info("[迁移] ✓ analysis_messages 表创建成功")
        else:
            logger.info("[迁移] ✓ analysis_messages 表已存在")

        # ==================== 2. 创建 analysis_snapshots 表 ====================
        logger.info("[迁移] 检查/创建 analysis_snapshots 表...")

        check_table = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'analysis_snapshots'
            )
        """))
        table_exists = check_table.scalar()

        if not table_exists:
            logger.info("[迁移] 创建 analysis_snapshots 表...")
            await conn.execute(text("""
                CREATE TABLE analysis_snapshots (
                    snapshot_id BIGSERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    message_id BIGINT NOT NULL,
                    accumulated_context JSONB NOT NULL,
                    analysis_result JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES analysis_messages(message_id)
                )
            """))

            # 创建索引
            await conn.execute(text("""
                CREATE INDEX idx_analysis_snapshots_session
                ON analysis_snapshots(session_id)
            """))
            await conn.execute(text("""
                CREATE INDEX idx_analysis_snapshots_message
                ON analysis_snapshots(message_id)
            """))
            logger.info("[迁移] ✓ analysis_snapshots 表创建成功")
        else:
            logger.info("[迁移] ✓ analysis_snapshots 表已存在")

        # ==================== 3. 创建 analysis_conflicts 表 ====================
        logger.info("[迁移] 检查/创建 analysis_conflicts 表...")

        check_table = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'analysis_conflicts'
            )
        """))
        table_exists = check_table.scalar()

        if not table_exists:
            logger.info("[迁移] 创建 analysis_conflicts 表...")
            await conn.execute(text("""
                CREATE TABLE analysis_conflicts (
                    conflict_id BIGSERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    conflict_type VARCHAR(50) NOT NULL,
                    field_name VARCHAR(100) NOT NULL,
                    existing_message_id BIGINT NOT NULL,
                    new_message_id BIGINT NOT NULL,
                    existing_value JSONB,
                    new_value JSONB,
                    severity VARCHAR(20) NOT NULL,
                    resolution VARCHAR(50),
                    resolved_value JSONB,
                    resolved_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (existing_message_id) REFERENCES analysis_messages(message_id),
                    FOREIGN KEY (new_message_id) REFERENCES analysis_messages(message_id)
                )
            """))

            # 创建索引
            await conn.execute(text("""
                CREATE INDEX idx_analysis_conflicts_session
                ON analysis_conflicts(session_id)
            """))
            await conn.execute(text("""
                CREATE INDEX idx_analysis_conflicts_messages
                ON analysis_conflicts(existing_message_id, new_message_id)
            """))
            logger.info("[迁移] ✓ analysis_conflicts 表创建成功")
        else:
            logger.info("[迁移] ✓ analysis_conflicts 表已存在")

        # ==================== 4. 扩展 analysis_messages 表字段 ====================
        logger.info("[迁移] 检查/扩展 analysis_messages 表字段...")

        # 检查并添加 extracted_fields 字段
        check_column = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'analysis_messages'
                AND column_name = 'extracted_fields'
            )
        """))
        column_exists = check_column.scalar()

        if not column_exists:
            await conn.execute(text("""
                ALTER TABLE analysis_messages
                ADD COLUMN extracted_fields JSONB DEFAULT '{}'
            """))
            logger.info("[迁移] ✓ 添加 extracted_fields 字段")
        else:
            logger.info("[迁移] ✓ extracted_fields 字段已存在")

        # 检查并添加 is_conflicted 字段
        check_column = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'analysis_messages'
                AND column_name = 'is_conflicted'
            )
        """))
        column_exists = check_column.scalar()

        if not column_exists:
            await conn.execute(text("""
                ALTER TABLE analysis_messages
                ADD COLUMN is_conflicted BOOLEAN DEFAULT FALSE
            """))
            logger.info("[迁移] ✓ 添加 is_conflicted 字段")
        else:
            logger.info("[迁移] ✓ is_conflicted 字段已存在")

        # 检查并添加 is_superseded 字段
        check_column = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'analysis_messages'
                AND column_name = 'is_superseded'
            )
        """))
        column_exists = check_column.scalar()

        if not column_exists:
            await conn.execute(text("""
                ALTER TABLE analysis_messages
                ADD COLUMN is_superseded BOOLEAN DEFAULT FALSE
            """))
            logger.info("[迁移] ✓ 添加 is_superseded 字段")
        else:
            logger.info("[迁移] ✓ is_superseded 字段已存在")

        # 检查并添加 superseded_by 字段
        check_column = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'analysis_messages'
                AND column_name = 'superseded_by'
            )
        """))
        column_exists = check_column.scalar()

        if not column_exists:
            await conn.execute(text("""
                ALTER TABLE analysis_messages
                ADD COLUMN superseded_by BIGINT
            """))
            logger.info("[迁移] ✓ 添加 superseded_by 字段")
        else:
            logger.info("[迁移] ✓ superseded_by 字段已存在")

        # 检查并添加 confidence_score 字段
        check_column = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'analysis_messages'
                AND column_name = 'confidence_score'
            )
        """))
        column_exists = check_column.scalar()

        if not column_exists:
            await conn.execute(text("""
                ALTER TABLE analysis_messages
                ADD COLUMN confidence_score FLOAT
            """))
            logger.info("[迁移] ✓ 添加 confidence_score 字段")
        else:
            logger.info("[迁移] ✓ confidence_score 字段已存在")

    logger.info("[迁移] ✅ 多轮对话功能数据库迁移完成!")


async def verify():
    """验证迁移结果"""
    db = get_db_manager()
    await db.initialize()

    async with db._engine.begin() as conn:
        # 检查表是否创建成功
        tables_to_check = ['analysis_messages', 'analysis_snapshots', 'analysis_conflicts']

        for table in tables_to_check:
            result = await conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table}'
                )
            """))
            exists = result.scalar()
            status = "✓" if exists else "✗"
            logger.info(f"[验证] {status} {table}")

        # 检查 analysis_messages 表的字段
        result = await conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'analysis_messages'
            ORDER BY ordinal_position
        """))
        logger.info("\n[验证] analysis_messages 表字段:")
        for row in result:
            logger.info(f"  - {row[0]}: {row[1]}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="多轮对话功能数据库迁移")
    parser.add_argument("--verify", action="store_true", help="验证迁移结果")
    args = parser.parse_args()

    if args.verify:
        asyncio.run(verify())
    else:
        asyncio.run(migrate())
        asyncio.run(verify())
