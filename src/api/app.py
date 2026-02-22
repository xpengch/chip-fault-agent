"""
芯片失效分析AI Agent系统 - FastAPI主应用
实现核心API端点和中间件
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
from datetime import datetime
from typing import Optional
import sys
import traceback

from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalysisResult,
    HealthResponse,
    StatsResponse,
    ErrorResponse
)
from ..agents import get_workflow
from ..database.connection import get_db_manager

from .routes import router as routes_router
from .auth_routes import router as auth_router
from .admin_routes import router as admin_router
from .expert_routes import router as expert_router
from ..auth.middleware import AuditLogMiddleware, AuthenticationMiddleware


# 配置日志
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("芯片失效分析AI Agent系统启动中...")

    # 初始化数据库连接
    db_manager = get_db_manager()
    await db_manager.initialize()

    logger.info("系统启动完成")
    yield

    # 清理资源
    logger.info("系统关闭中...")
    await db_manager.close()
    logger.info("系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="芯片失效分析AI Agent系统",
    description="基于2-Agent架构和MCP标准的自研SoC芯片失效分析系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 认证中间件
app.add_middleware(AuthenticationMiddleware)

# 审计日志中间件
app.add_middleware(AuditLogMiddleware)

# 包含额外路由
app.include_router(routes_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(expert_router)


# ==================== 全局异常处理 ====================

class APIError(Exception):
    """API错误基类"""

    def __init__(self, message: str, detail: str = None, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.detail = detail
        self.status_code = status_code


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """处理API错误"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    logger.error(f"未处理的异常: {str(exc)}")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "内部服务器错误",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


# ==================== API路由 ====================

@app.get("/api/v1/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """
    健康检查端点

    返回系统健康状态和版本信息
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now()
    )


@app.get("/api/v1/stats", response_model=StatsResponse, tags=["系统"])
async def get_statistics():
    """
    获取系统统计数据

    返回今日分析次数、成功率、平均耗时等统计信息
    """
    try:
        db_manager = get_db_manager()
        stats = await db_manager.get_statistics()

        return StatsResponse(
            today_analyses=stats.get("today_count", 0),
            success_rate=stats.get("success_rate", 0.0),
            avg_duration=stats.get("avg_duration", 0.0),
            expert_interventions=stats.get("expert_count", 0),
            total_analyses=stats.get("total_count", 0),
            today_change=stats.get("today_change", 0.0),
            duration_change=stats.get("duration_change", 0.0),
            expert_change=stats.get("expert_change", 0.0)
        )

    except Exception as e:
        logger.error(f"[API] 获取统计数据失败: {str(e)}")
        return StatsResponse(
            today_analyses=0,
            success_rate=0.0,
            avg_duration=0.0,
            expert_interventions=0,
            total_analyses=0,
            today_change=0.0,
            duration_change=0.0,
            expert_change=0.0
        )


@app.post("/api/v1/analyze", response_model=AnalyzeResponse, tags=["分析"])
async def analyze_chip_fault(request: AnalyzeRequest):
    """
    提交芯片故障日志进行分析

    Args:
        request: 分析请求，包含芯片型号和原始日志

    Returns:
        分析结果，包含失效域、根因、置信度等
    """
    logger.info(f"[API] 收到分析请求 - 芯片: {request.chip_model}, session: {request.session_id}")

    # 记录开始时间
    start_time = datetime.now()

    try:
        # 获取工作流
        workflow = get_workflow()

        # 执行分析
        result = await workflow.run(
            chip_model=request.chip_model,
            raw_log=request.raw_log,
            session_id=request.session_id,
            user_id=request.user_id,
            infer_threshold=request.infer_threshold
        )

        # 计算处理时长（秒）
        end_time = datetime.now()
        processing_duration = (end_time - start_time).total_seconds()

        logger.info(f"[API] 分析完成 - 耗时: {processing_duration:.2f}秒")

        # 检查是否成功
        if not result.get("success"):
            raise APIError(
                message="分析失败",
                detail=result.get("error_message"),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 构建响应
        response_data = AnalysisResult(
            session_id=result["session_id"],
            chip_model=result["chip_model"],
            final_root_cause=result.get("final_root_cause"),
            need_expert=result.get("need_expert", False),
            infer_report=result.get("infer_report"),
            infer_trace=result.get("infer_trace"),
            expert_correction=result.get("expert_correction"),
            tokens_used=result.get("tokens_used", 0),
            token_usage=result.get("token_usage"),
            created_at=datetime.now()
        )

        # 存储分析结果到数据库（包含处理时长）
        logger.info(f"[API] 准备存储分析结果 - result keys: {list(result.keys())}")
        logger.info(f"[API] result中有infer_report: {'infer_report' in result}")
        if 'infer_report' in result:
            logger.info(f"[API] infer_report is not None: {result['infer_report'] is not None}")
        try:
            db_manager = get_db_manager()
            logger.info(f"[API] 获取到db_manager: {db_manager}")
            await db_manager.store_analysis_result(
                session_id=result["session_id"],
                chip_model=result["chip_model"],
                analysis_result=result,
                processing_duration=processing_duration,
                started_at=start_time
            )

            # 临时方案：直接用SQL更新infer_report（确保存储）
            if result.get("infer_report"):
                try:
                    from sqlalchemy import text
                    async with db_manager._session_factory() as session:
                        await session.execute(text("""
                            UPDATE analysis_results
                            SET infer_report = :report
                            WHERE session_id = :sid
                        """), {"report": result["infer_report"], "sid": result["session_id"]})
                        await session.commit()
                        logger.info(f"[API] 直接SQL更新infer_report成功")
                except Exception as sql_e:
                    logger.warning(f"[API] 直接SQL更新失败: {sql_e}")

            logger.info(f"[API] 分析结果存储成功")
        except Exception as e:
            # 存储失败不影响主流程
            logger.error(f"[API] 存储分析结果失败: {str(e)}")
            logger.error(traceback.format_exc())

        return AnalyzeResponse(
            success=True,
            message="分析完成",
            data=response_data
        )

    except APIError:
        raise
    except Exception as e:
        logger.error(f"[API] 分析处理失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise APIError(
            message="分析处理失败",
            detail=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.get("/api/v1/analysis/{session_id}", response_model=AnalyzeResponse, tags=["分析"])
async def get_analysis_result(session_id: str):
    """
    获取分析结果

    Args:
        session_id: 会话ID

    Returns:
        分析结果
    """
    logger.info(f"[API] 查询分析结果 - session: {session_id}")

    try:
        db_manager = get_db_manager()

        # 从数据库查询结果
        result = await db_manager.get_analysis_result(session_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到会话ID: {session_id} 的分析结果"
            )

        # 构建响应
        response_data = AnalysisResult(
            session_id=result["session_id"],
            chip_model=result["chip_model"],
            final_root_cause=result.get("final_root_cause"),
            need_expert=result.get("need_expert", False),
            infer_report=result.get("infer_report"),
            infer_trace=result.get("infer_trace"),
            expert_correction=result.get("expert_correction")
        )

        return AnalyzeResponse(
            success=True,
            message="查询成功",
            data=response_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] 查询分析结果失败: {str(e)}")
        raise APIError(
            message="查询失败",
            detail=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.get("/api/v1/history", tags=["分析"])
async def get_analysis_history(
    limit: int = 50,
    offset: int = 0,
    chip_model: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """
    获取分析历史记录

    Args:
        limit: 返回记录数量限制 (默认50)
        offset: 偏移量 (默认0)
        chip_model: 筛选芯片型号
        date_from: 起始日期 (ISO格式)
        date_to: 结束日期 (ISO格式)

    Returns:
        历史记录列表和总数
    """
    try:
        db_manager = get_db_manager()

        # 转换日期字符串
        from datetime import datetime
        date_from_dt = None
        date_to_dt = None

        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                date_from_dt = None

        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                date_to_dt = None

        history = await db_manager.get_analysis_history(
            limit=limit,
            offset=offset,
            chip_model=chip_model,
            date_from=date_from_dt,
            date_to=date_to_dt
        )

        return history

    except Exception as e:
        logger.error(f"[API] 获取分析历史失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise APIError(
            message="获取历史记录失败",
            detail=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== 额外端点（文档友好） ====================

@app.get("/", tags=["系统"])
async def root():
    """
    根端点，提供系统信息
    """
    return {
        "name": "芯片失效分析AI Agent系统",
        "version": "1.0.0",
        "description": "基于2-Agent架构和MCP标准的自研SoC芯片失效分析系统",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# ==================== 启动配置 ====================

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """
    启动API服务器

    Args:
        host: 监听地址
        port: 监听端口
    """
    import uvicorn

    logger.info(f"启动API服务器 - {host}:{port}")

    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
