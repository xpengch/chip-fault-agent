import asyncio
from src.database.connection import get_db_manager
from sqlalchemy import text

async def check():
    db = get_db_manager()
    await db.initialize()
    async with db._engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'analysis_results'
            AND column_name IN ('infer_report', 'infer_trace')
        """))
        print("已添加的字段:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")

asyncio.run(check())
