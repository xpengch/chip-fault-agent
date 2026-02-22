"""
芯片失效分析AI Agent系统 - 简化API（不依赖torch）
用于基础功能测试
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
from datetime import datetime

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")

# 创建简化版API
app = FastAPI(
    title="芯片失效分��AI Agent系统 - 简化版",
    description="基础API测试（不依赖AI功能）",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 基础端点 ====================

@app.get("/")
async def root():
    """根端点"""
    return {
        "name": "芯片失效分析AI Agent系统 - 简化版",
        "version": "1.0.0",
        "status": "API运行正常",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/modules")
async def get_supported_modules():
    """获取支持的模块列表"""
    return {
        "success": True,
        "data": {
            "compute": {
                "name": "计算子系统",
                "modules": ["cpu", "l2_cache", "l3_cache"]
            },
            "memory": {
                "name": "内存子系统",
                "modules": ["ddr_controller", "hbm_controller"]
            },
            "interconnect": {
                "name": "互连子系统",
                "modules": ["ha", "noc_router", "noc_endpoint"]
            }
        }
    }


@app.get("/api/v1/chips")
async def get_supported_chips():
    """获取支持的芯片列表"""
    return {
        "success": True,
        "data": [
            {
                "model": "XC9000",
                "description": "高性能自研SoC芯片",
                "architecture": "ARMv9",
                "process_node": "7nm"
            },
            {
                "model": "XC8000",
                "description": "标准版自研SoC芯片",
                "architecture": "ARMv8",
                "process_node": "12nm"
            },
            {
                "model": "XC7000",
                "description": "入门级自研SoC芯片",
                "architecture": "ARMv8",
                "process_node": "14nm"
            }
        ]
    }


@app.post("/api/v1/analyze")
async def analyze_chip_fault(request: dict):
    """
    简化的分析端点（不使用AI）
    仅用于测试API功能
    """
    log_content = request.get("raw_log", "")

    # 简化的错误码分析
    error_codes = []
    if "0XCO" in log_content:
        error_codes.append("0XCO001")
        failure_domain = "compute"
        failure_module = "cpu"
        root_cause = "CPU核心运算错误"
    elif "0XLA" in log_content:
        error_codes.append("0XLA001")
        failure_domain = "cache"
        failure_module = "l3_cache"
        root_cause = "L3缓存一致性错误"
    elif "0XME" in log_content:
        error_codes.append("0XME001")
        failure_domain = "memory"
        failure_module = "ddr_controller"
        root_cause = "DDR控制器时序违例"
    else:
        failure_domain = "unknown"
        failure_module = "unknown"
        root_cause = "无法识别"

    return {
        "success": True,
        "message": "简化分析完成",
        "data": {
            "session_id": f"simple_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "chip_model": request.get("chip_model", "XC9000"),
            "final_root_cause": {
                "failure_domain": failure_domain,
                "module": failure_module,
                "root_cause": root_cause,
                "confidence": 0.6,
                "reasoning": "简化规则分析（未使用AI）"
            },
            "need_expert": True,
            "infer_report": "简化版未生成报告"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
