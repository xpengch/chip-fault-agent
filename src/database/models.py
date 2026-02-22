"""
芯片失效分析AI Agent系统 - 数据库模型
使用JSONB混合方案：核心字段 + JSONB扩展属性
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, ForeignKey, Index, Text, Numeric, Date,
    CheckConstraint, UniqueConstraint, ARRAY, UUID, MetaData, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs


# ============================================
# 声明式基类
# ============================================
class Base(AsyncAttrs, DeclarativeBase):
    """所有模型的基类"""
    pass


# ============================================
# SoC芯片型号表
# ============================================
class SoCChip(Base):
    """自研SoC芯片型号表"""
    __tablename__ = "soc_chips"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chip_model: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    chip_series: Mapped[Optional[str]] = mapped_column(String(50))
    architecture: Mapped[Optional[str]] = mapped_column(String(50))  # ARM/x86/RISC-V/自研架构
    process_node: Mapped[Optional[str]] = mapped_column(String(20))  # 7nm/5nm
    generation: Mapped[Optional[str]] = mapped_column(String(20))
    target_market: Mapped[Optional[str]] = mapped_column(String(50))  # 汽车/手机/服务器
    release_date: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    subsystems: Mapped[List["SoCSubsystem"]] = relationship(
        "SoCSubsystem", back_populates="chip"
    )
    modules: Mapped[List["SoCModule"]] = relationship(
        "SoCModule", back_populates="chip"
    )

    __table_args__ = (
        Index("idx_soc_chip_active", "is_active"),
    )


# ============================================
# SoC子系统表
# ============================================
class SoCSubsystem(Base):
    """SoC子系统表（CPU集群、缓存子系统、互连子系统等）"""
    __tablename__ = "soc_subsystems"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chip_model: Mapped[str] = mapped_column(String(50), ForeignKey("soc_chips.chip_model"))
    subsystem_name: Mapped[str] = mapped_column(String(100), nullable=False)
    subsystem_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    design_team: Mapped[Optional[str]] = mapped_column(String(100))
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    chip: Mapped["SoCChip"] = relationship("SoCChip", back_populates="subsystems")
    modules: Mapped[List["SoCModule"]] = relationship(
        "SoCModule", back_populates="subsystem"
    )

    __table_args__ = (
        Index("idx_subsystem_chip", "chip_model"),
        Index("idx_subsystem_type", "subsystem_type"),
    )


# ============================================
# 模块属性模板表
# ============================================
class ModuleAttributeTemplate(Base):
    """模块属性模板表 - 定义每种模块类型的属性模板"""
    __tablename__ = "module_attribute_templates"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    module_type: Mapped[str] = mapped_column(String(50), nullable=False)
    attribute_name: Mapped[str] = mapped_column(String(100), nullable=False)
    attribute_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    default_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("module_type", "attribute_name", name="uq_module_attribute"),
        Index("idx_attr_template_module_type", "module_type"),
    )


# ============================================
# SoC模块表
# ============================================
class SoCModule(Base):
    """
    SoC模块表 - 支持CPU/L3/HA/NoC/DDR/HBM等模块类型
    使用JSONB存储模块特定属性，实现灵活扩展
    """
    __tablename__ = "soc_modules"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chip_model: Mapped[str] = mapped_column(String(50), ForeignKey("soc_chips.chip_model"))
    subsystem_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("soc_subsystems.id"))

    # 核心通用字段（所有模块都有）
    module_name: Mapped[str] = mapped_column(String(100), nullable=False)
    module_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    internal_id: Mapped[Optional[str]] = mapped_column(String(100))
    power_domain: Mapped[Optional[str]] = mapped_column(String(50))
    clock_domain: Mapped[Optional[str]] = mapped_column(String(50))
    address_range: Mapped[Optional[str]] = mapped_column(String(100))
    version: Mapped[Optional[str]] = mapped_column(String(50))

    # ✅ JSONB字段：模块特定属性（灵活扩展）
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    # 状态字段
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    chip: Mapped["SoCChip"] = relationship("SoCChip", back_populates="modules")
    subsystem: Mapped[Optional["SoCSubsystem"]] = relationship(
        "SoCSubsystem", back_populates="modules"
    )

    __table_args__ = (
        UniqueConstraint("chip_model", "module_name", name="uq_soc_module"),
        Index("idx_module_chip", "chip_model"),
        Index("idx_module_type", "module_type"),
        Index("idx_module_active", "is_active"),
        # JSONB属性索引
        Index("idx_module_attributes_gin", "attributes", postgresql_using="gin"),
    )

    def get_attribute(self, key: str, default=None):
        """获取JSONB属性"""
        return self.attributes.get(key, default)

    def set_attribute(self, key: str, value):
        """设置JSONB属性"""
        if self.attributes is None:
            self.attributes = {}
        self.attributes[key] = value


# ============================================
# 失效案例表
# ============================================
class FailureCase(Base):
    """
    失效案例表 - 历史故障案例
    使用JSONB存储案例特定属性
    """
    __tablename__ = "failure_cases"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    chip_model: Mapped[str] = mapped_column(String(50), ForeignKey("soc_chips.chip_model"))

    # 失效位置（层次化）
    subsystem_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("soc_subsystems.id"))
    module_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("soc_modules.id"))
    module_type: Mapped[Optional[str]] = mapped_column(String(50))
    failure_domain: Mapped[Optional[str]] = mapped_column(String(50))
    internal_location: Mapped[Optional[str]] = mapped_column(String(200))  # 内部定位信息

    # 故障症状
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    error_codes: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)

    # 失效模式
    failure_mode: Mapped[Optional[str]] = mapped_column(String(100))
    failure_mechanism: Mapped[Optional[str]] = mapped_column(String(100))

    # 根因与解决方案
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    root_cause_category: Mapped[Optional[str]] = mapped_column(String(50))
    solution: Mapped[Optional[str]] = mapped_column(Text)

    # 测试与验证
    test_conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[str]] = mapped_column(String(50))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # 敏感度
    sensitivity_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # 向量检索（后续添加）
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float))

    # 版本
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_case_chip_model", "chip_model"),
        Index("idx_case_failure_domain", "failure_domain"),
        Index("idx_case_module_type", "module_type"),
        Index("idx_case_module", "module_id"),
    )


# ============================================
# 分析结果表
# ============================================
class AnalysisResult(Base):
    """
    分析结果表 - 存储所有分析结果
    使用JSONB存储提取的特征和推理结果
    """
    __tablename__ = "analysis_results"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(50))
    chip_model: Mapped[str] = mapped_column(String(50), ForeignKey("soc_chips.chip_model"))

    # 输入日志
    log_source: Mapped[Optional[str]] = mapped_column(String(255))
    log_hash: Mapped[Optional[str]] = mapped_column(String(64))
    raw_log: Mapped[Optional[str]] = mapped_column(Text)

    # 提取的特征（JSON格式）
    fault_features: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    affected_modules: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(UUID))
    affected_subsystems: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(UUID))

    # NoC相关信息（如适用）
    noc_path: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    noc_congestion_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)

    # 推理结果
    failure_domain: Mapped[Optional[str]] = mapped_column(String(50))
    failure_subsystem: Mapped[Optional[UUID]] = mapped_column(ForeignKey("soc_subsystems.id"))
    failure_module: Mapped[Optional[UUID]] = mapped_column(ForeignKey("soc_modules.id"))
    internal_location: Mapped[Optional[str]] = mapped_column(String(200))
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    root_cause_category: Mapped[Optional[str]] = mapped_column(String(50))

    # 置信度与匹配
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    matched_case_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("failure_cases.id"))
    reasoning_sources: Mapped[Dict[str, bool]] = mapped_column(JSONB, default=dict)

    # 专家修正
    expert_correction_id: Mapped[Optional[str]] = mapped_column(String(50))

    # AI分析报告和推理步骤
    infer_report: Mapped[Optional[str]] = mapped_column(Text)  # AI生成的分析报告
    infer_trace: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, default=dict)  # 推理步骤轨迹

    # 处理时长（秒）
    processing_duration: Mapped[Optional[float]] = mapped_column(Numeric(10, 3))

    # 状态
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_analysis_chip_model", "chip_model"),
        Index("idx_analysis_status", "status"),
        Index("idx_analysis_module", "failure_module"),
        Index("idx_analysis_user", "user_id"),
        Index("idx_analysis_created", "created_at"),
    )


# ============================================
# 推理规则表
# ============================================
class InferenceRule(Base):
    """
    推理规则表 - 存储基于规则的推理逻辑
    使用JSONB存储灵活的条件和结论
    """
    __tablename__ = "inference_rules"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 规则适用范围
    chip_model: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("soc_chips.chip_model"))
    subsystem_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("soc_subsystems.id"))
    module_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("soc_modules.id"))
    failure_domain: Mapped[Optional[str]] = mapped_column(String(50))

    # 规则条件（JSON格式，灵活配置）
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # 规则结论（JSON格式）
    conclusion: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))

    # 规则元数据
    rule_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_rule_chip_model", "chip_model"),
        Index("idx_rule_is_active", "is_active"),
        Index("idx_rule_priority", "priority"),
    )


# ============================================
# 专家修正表（第二阶段实现）
# ============================================
class ExpertCorrection(Base):
    """
    专家修正表 - 存储专家对分析结果的修正
    """
    __tablename__ = "expert_corrections"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    correction_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    analysis_id: Mapped[str] = mapped_column(String(50), ForeignKey("analysis_results.analysis_id"))

    original_result: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    corrected_result: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    correction_reason: Mapped[Optional[str]] = mapped_column(Text)

    submitted_by: Mapped[str] = mapped_column(String(50), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(50))
    approval_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False)

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_correction_analysis_id", "analysis_id"),
        Index("idx_correction_status", "approval_status"),
        Index("idx_correction_submitted_by", "submitted_by"),
    )


# ============================================
# 统计汇总表
# ============================================
class StatisticsSummary(Base):
    """统计汇总表"""
    __tablename__ = "statistics_summary"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    stat_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    chip_model: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("soc_chips.chip_model"))

    total_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    failure_domain_stats: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    error_code_stats: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    module_stats: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    correction_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    accuracy_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stat_date", "stat_type", "chip_model", name="uq_statistics"),
        Index("idx_stats_date", "stat_date"),
    )


# ============================================
# 多轮对话功能表
# ============================================
class AnalysisMessage(Base):
    """用户交互消息表"""
    __tablename__ = "analysis_messages"

    message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user_input, correction, system_response, analysis_result
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(50))  # text, log, correction_data
    message_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    is_correction: Mapped[bool] = mapped_column(Boolean, default=False)
    corrected_message_id: Mapped[Optional[int]] = mapped_column(BigInteger)  # 指向被纠正的消息

    # 多轮对话扩展字段
    extracted_fields: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)  # 从此消息提取的字段
    is_conflicted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superseded: Mapped[bool] = mapped_column(Boolean, default=False)
    superseded_by: Mapped[Optional[int]] = mapped_column(BigInteger)  # 被哪条消息替代
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)  # 信息的置信度

    # 关系
    corrected_message: Mapped[Optional["AnalysisMessage"]] = relationship(
        "AnalysisMessage", remote_side=[message_id], foreign_keys=[corrected_message_id]
    )
    superseding_message: Mapped[Optional["AnalysisMessage"]] = relationship(
        "AnalysisMessage", remote_side=[message_id], foreign_keys=[superseded_by]
    )

    __table_args__ = (
        Index("idx_analysis_messages_session", "session_id"),
        Index("idx_analysis_messages_sequence", "session_id", "sequence_number"),
        Index("idx_analysis_messages_correction", "corrected_message_id"),
    )


class AnalysisSnapshot(Base):
    """分析快照表"""
    __tablename__ = "analysis_snapshots"

    snapshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 关联到触发的消息
    accumulated_context: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)  # 累积的所有信息
    analysis_result: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)  # 该次分析结果
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    message: Mapped["AnalysisMessage"] = relationship("AnalysisMessage", foreign_keys=[message_id])

    __table_args__ = (
        Index("idx_analysis_snapshots_session", "session_id"),
        Index("idx_analysis_snapshots_message", "message_id"),
    )


class AnalysisConflict(Base):
    """冲突记录表"""
    __tablename__ = "analysis_conflicts"

    conflict_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    conflict_type: Mapped[str] = mapped_column(String(50), nullable=False)  # direct, indirect, temporal, causal
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    existing_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    new_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    existing_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    new_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # high, medium, low
    resolution: Mapped[Optional[str]] = mapped_column(String(50))  # use_existing, use_new, merge, manual
    resolved_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # 关系
    existing_message: Mapped["AnalysisMessage"] = relationship(
        "AnalysisMessage", foreign_keys=[existing_message_id]
    )
    new_message: Mapped["AnalysisMessage"] = relationship(
        "AnalysisMessage", foreign_keys=[new_message_id]
    )

    __table_args__ = (
        Index("idx_analysis_conflicts_session", "session_id"),
        Index("idx_analysis_conflicts_messages", "existing_message_id", "new_message_id"),
    )


# ============================================
# 审计日志表 - 从rbac_models导入（第二阶段增强）
# ============================================
# 为避免重复定义，这里��rbac_models导入更完善的AuditLog类
# 包含更多字段：status, error_message, request_method, request_path, response_data等
# 以及与User的关系
try:
    from .rbac_models import AuditLog
except ImportError:
    # 如果rbac_models尚未导入，定义一个占位符
    # 实际使用时会使用rbac_models中的完整定义
    class AuditLog:
        """占位符类 - 实际定义在rbac_models.py中"""
        pass
