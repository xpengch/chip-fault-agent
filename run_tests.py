"""
内存优化测试运行器
"""

import sys
import gc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def run_lightweight_tests():
    """运行轻量级测试"""
    print("=" * 60)
    print("运行轻量级内存友好测试...")
    print("=" * 60)

    from tests.test_lightweight import main
    main()


def run_unit_tests():
    """运行单元测试"""
    print("=" * 60)
    print("运行单元测试...")
    print("=" * 60)

    import pytest

    # 使用最少的内存配置
    exit_code = pytest.main([
        "tests/test_unit_simple.py",
        "-v",
        "--tb=short",
        "-p", "no:warnings",
    ])

    # 清理
    gc.collect()

    return exit_code == 0


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="内存优化测试运行器")
    parser.add_argument(
        "--type",
        choices=["light", "unit", "all"],
        default="light",
        help="测试类型: light=轻量级, unit=单元测试, all=全部"
    )

    args = parser.parse_args()

    print("\n╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "内存优化测试运行器" + " " * 23 + "║")
    print("╚" + "═" * 58 + "╝")

    try:
        if args.type == "light":
            run_lightweight_tests()
        elif args.type == "unit":
            success = run_unit_tests()
            sys.exit(0 if success else 1)
        else:  # all
            run_lightweight_tests()
            print("\n" + "=" * 60 + "\n")
            success = run_unit_tests()
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
