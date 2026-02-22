"""
芯片失效分析AI Agent系统 - API数据模型
使用Pydantic定义请求和响应schema
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


# ==================== 请求Schema ====================

class AnalyzeRequest(BaseModel):
    """分析请求模型"""

    chip_model: str = Field(..., description="芯片型号", min_length=1)
    raw_log: str = Field(..., description="原始日志内容", min_length=1)
    session_id: Optional[str] = Field(None, description="会话ID（可选，系统自动生成）")
    user_id: Optional[str] = Field(None, description="用户ID（可选）")
    infer_threshold: float = Field(0.7, description="推理阈值（0-1）", ge=0.0, le=1.0)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "chip_model": "XC9000",
                    "raw_log": "[ERROR] 0XCO001 CPU core 0 fault detected\n...",
                    "infer_threshold": 0.7
                }
            ]
        }
    }


class ExpertCorrectionRequest(BaseModel):
    """专家修正请求模型（Phase 2）"""

    session_id: str = Field(..., description="会话ID")
    expert_id: Optional[str] = Field(None, description="专家ID")
    correction_data: Dict[str, Any] = Field(..., description="修正数据")
    notes: Optional[str] = Field(None, description="修正备注")


# ==================== 响应Schema ====================

class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field("healthy", description="服务状态")
    version: str = Field(..., description="系��版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")


class StatsResponse(BaseModel):
    """统计数据响应"""

    today_analyses: int = Field(..., description="今日分析次数")
    success_rate: float = Field(..., description="成功率")
    avg_duration: float = Field(..., description="平均耗时（秒）")
    expert_interventions: int = Field(..., description="专家介入次数")
    total_analyses: int = Field(..., description="总分析次数")
    today_change: float = Field(0.0, description="今日变化率")
    duration_change: float = Field(0.0, description="耗时变化率")
    expert_change: float = Field(0.0, description="专家介入变化率")


class FaultFeatures(BaseModel):
    """故障特征响应"""

    error_codes: List[str] = Field(default_factory=list, description="错误码列表")
    registers: Dict[str, Any] = Field(default_factory=dict, description="寄存器信息")
    fault_description: Optional[str] = Field(None, description="故障描述")
    timestamp: Optional[str] = Field(None, description="故障时间戳")
    modules: List[str] = Field(default_factory=list, description="涉及模块")
    domain: Optional[str] = Field(None, description="失效域")
    severity: Optional[str] = Field(None, description="严重程度")


class RootCauseInfo(BaseModel):
    """根因信息响应"""

    module: Optional[str] = Field(None, description="失效模块")
    root_cause: Optional[str] = Field(None, description="根本原因")
    failure_domain: Optional[str] = Field(None, description="失效域")
    confidence: float = Field(0.0, description="置信度")
    reasoning: Optional[str] = Field(None, description="推理过程")


class DelimitResult(BaseModel):
    """定界结果响应"""

    type: str = Field(..., description="推理源类型")
    result: Dict[str, Any] = Field(..., description="推理结果")


class AnalysisResult(BaseModel):
    """分析结果响应"""

    session_id: str = Field(..., description="会话ID")
    chip_model: str = Field(..., description="芯片型号")
    fault_features: Optional[FaultFeatures] = Field(None, description="故障特征")
    final_root_cause: Optional[RootCauseInfo] = Field(None, description="最终根因")
    need_expert: bool = Field(False, description="是否需要专家介入")
    infer_report: Optional[str] = Field(None, description="分析报告路径")
    infer_trace: Optional[List[Dict[str, Any]]] = Field(None, description="推理链路")
    expert_correction: Optional[Dict[str, Any]] = Field(None, description="专家修正信息")
    tokens_used: int = Field(0, description="Token消耗数量")
    token_usage: Optional[Dict[str, Any]] = Field(None, description="详细Token使用信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class AnalyzeResponse(BaseModel):
    """分析API响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[AnalysisResult] = Field(None, description="分析结果")
    error: Optional[str] = Field(None, description="错误信息")


class ErrorResponse(BaseModel):
    """错误响应"""

    success: bool = Field(False, description="是否成功")
    error: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")


# ==================== 数据库Schema ====================

class AnalysisResultDB(BaseModel):
    """数据库存储的分析结果"""

    session_id: str
    user_id: Optional[str]
    chip_model: str
    fault_features: Dict[str, Any]
    final_root_cause: Dict[str, Any]
    need_expert: bool
    infer_report: Optional[str]
    infer_trace: Optional[List[Dict[str, Any]]]
    expert_correction: Optional[Dict[str, Any]]


class FailureCaseDB(BaseModel):
    """数据库存储的失效案例"""

    chip_model: str
    failure_domain: str
    root_cause: str
    error_codes: List[str]
    modules: List[str]
    solution: Optional[str]
    severity: Optional[str]
    feature_vector: Optional[List[float]]


# ==================== 分页Schema ====================

class PaginatedResponse(BaseModel):
    """分页响应"""

    success: bool = Field(..., description="是否成功")
    data: List[Any] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    has_next: bool = Field(..., description="是否有下一页")
