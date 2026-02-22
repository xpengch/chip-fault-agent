"""
芯片失效分析AI Agent系统 - 启动脚本
支持启动API服务、前端界面或两者同时启动
"""

import asyncio
import sys
import argparse
from loguru import logger

# 添加项目路径
sys.path.insert(0, ".")


async def start_api():
    """启动API服务器"""
    from src.api.app import run_server

    logger.info("启动API服务器...")
    run_server(host="0.0.0.0", port=8000)


def start_frontend():
    """启动Streamlit前端"""
    import subprocess

    logger.info("启动Streamlit前端...")

    subprocess.run(
        [
            sys.executable, "-m", "streamlit", "run",
            "frontend/app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ]
    )


def main():
    """主函数"""

    parser = argparse.ArgumentParser(
        description="芯片失效分析AI Agent系统启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py api         # 仅启动API服务
  python run.py frontend    # 仅启动前端
  python run.py all        # 同时启动API和前端（需要两个终端）
        """
    )

    parser.add_argument(
        "service",
        choices=["api", "frontend", "all"],
        help="要启动的服务"
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API监听地址"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API监听端口"
    )

    parser.add_argument(
        "--frontend-port",
        type=int,
        default=8501,
        help="前端监听端口"
    )

    args = parser.parse_args()

    if args.service == "api":
        logger.info(f"启动API服务 - {args.host}:{args.port}")
        from src.api.app import run_server
        run_server(host=args.host, port=args.port)

    elif args.service == "frontend":
        import subprocess
        logger.info(f"启动前端服务 - {args.host}:{args.frontend_port}")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "frontend/app.py",
            "--server.port", str(args.frontend_port),
            "--server.address", args.host
        ])

    elif args.service == "all":
        print("=" * 60)
        print("同时启动API和前端需要使用两个终端:")
        print("")
        print(f"终端1 - API服务:")
        print(f"  python run.py api --port {args.port}")
        print("")
        print(f"终端2 - 前端服务:")
        print(f"  python run.py frontend --frontend-port {args.frontend_port}")
        print("")
        print(f"然后访问前端: http://localhost:{args.frontend_port}")
        print("=" * 60)


if __name__ == "__main__":
    main()
