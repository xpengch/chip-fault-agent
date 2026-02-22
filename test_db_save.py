"""Test database save directly"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database.connection import get_db_manager


async def test_db_save():
    """Test database saving"""
    print("Testing database save...")

    db = get_db_manager()

    # Test storing a result - matching the actual workflow output structure
    await db.store_analysis_result(
        session_id='direct_test_003',
        chip_model='XC9000',
        analysis_result={
            'success': True,
            'session_id': 'direct_test_003',
            'chip_model': 'XC9000',
            'final_root_cause': {
                'module': 'cpu',
                'root_cause': 'CPU核心运算错误',
                'failure_domain': 'compute',
                'confidence': 0.75,
                'reasoning': '多源融合结果'
            },
            'need_expert': False,
            'infer_report': 'test report',
            'infer_trace': {'step': 'test'},
            'fault_features': {'error_codes': ['0XCO001']},
            'raw_log': '[ERROR] CPU fault'
        }
    )
    print("[OK] Data saved successfully")

    # Test statistics
    stats = await db.get_statistics()
    print(f"[OK] Statistics: {stats}")


if __name__ == '__main__':
    asyncio.run(test_db_save())
