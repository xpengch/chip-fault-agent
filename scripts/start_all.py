"""
芯片失效分析AI Agent系统 - 一键启动脚本
同时启动API和前端服务
"""

import subprocess
import sys
import time
from pathlib import Path
from loguru import logger


def start_api():
    """启动API服务"""
    logger.info("启动API服务...")

    api_process = subprocess.Popen(
        [sys.executable, "run.py", "api"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return api_process


def start_frontend():
    """启动前端服务"""
    logger.info("启动前端服务...")

    frontend_process = subprocess.Popen(
        [sys.executable, "run.py", "frontend"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return frontend_process


def main():
    """主函数"""

    print("=" * 60)
    print("芯片失效分析AI Agent系统 - 一键启动")
    print("=" * 60)
    print()

    processes = []

    try:
        # 启动API
        print("1. 启动API服务...")
        api_proc = start_api()
        processes.append(api_proc)
        time.sleep(2)

        # 启动前端
        print("2. 启动前端服务...")
        frontend_proc = start_frontend()
        processes.append(frontend_proc)
        time.sleep(1)

        print()
        print("=" * 60)
        print("✅ 所有服务已启动!")
        print("=" * 60)
        print()
        print("API服务:     http://localhost:8000")
        print("API文档:      http://localhost:8000/docs")
        print("前端界面:     http://localhost:8501")
        print()
        print("按 Ctrl+C 停止所有服务")
        print("=" * 60)
        print()

        # 等待进程
        try:
            for proc in processes:
                proc.wait()
        except KeyboardInterrupt:
            print()
            print("正在停止服务...")

            for proc in processes:
                proc.terminate()
                proc.wait(timeout=5)

            print("所有服务已停止")

    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        for proc in processes:
            try:
                proc.terminate()
            except:
                pass

    print()
    print("已退出")


if __name__ == "__main__":
    main()
