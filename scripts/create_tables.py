"""创建数据库表"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import db_manager
from src.database.models import Base
from sqlalchemy import text


async def create_tables():
    """创建所有表"""
    print("正在创建数据库表...")

    # 使用同步方式创建表
    from sqlalchemy import create_engine
    from src.config.settings import get_settings

    settings = get_settings()

    # 创建同步引擎
    sync_engine = create_engine(
        settings.DATABASE_URL.replace("+asyncpg", ""),
        echo=True
    )

    # 创建表
    Base.metadata.create_all(sync_engine)

    print("数据库表创建完成!")

    # 关闭引擎
    sync_engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
