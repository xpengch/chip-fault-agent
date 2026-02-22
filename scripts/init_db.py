"""
芯片失效分析AI Agent系统 - 数据库初始化脚本
创建基础芯片型号、模块类型和样本数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from datetime import datetime

from src.database.connection import db_manager
from src.database.models import (
    SoCChip,
    SoCSubsystem,
    SoCModule,
    ModuleAttributeTemplate,
    FailureCase,
    InferenceRule
)
from sqlalchemy import select


async def init_chip_models():
    """初始化基础芯片型号"""
    logger.info("初始化芯片型号...")

    # 先确保表已创建
    from src.database.connection import Base
    async with db_manager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    chip_models = [
        {
            "chip_model": "XC9000",
            "architecture": "ARMv9",
            "process_node": "7nm",
            "target_market": "高性能计算"
        },
        {
            "chip_model": "XC8000",
            "architecture": "ARMv8",
            "process_node": "12nm",
            "target_market": "标准计算"
        },
        {
            "chip_model": "XC7000",
            "architecture": "ARMv8",
            "process_node": "14nm",
            "target_market": "入门级计算"
        }
    ]

    async with db_manager.session_factory() as session:
        for model_data in chip_models:
            # 检查是否已存在
            stmt = select(SoCChip).where(SoCChip.chip_model == model_data["chip_model"])
            existing = await session.execute(stmt)
            if existing.scalar_one_or_none():
                logger.info(f"  芯片型号已存在: {model_data['chip_model']}")
                continue

            chip = SoCChip(**model_data, created_at=datetime.now())
            session.add(chip)
            logger.info(f"  添加芯片型号: {model_data['chip_model']}")

        await session.commit()
        await session.rollback()

    logger.info("芯片型号初始化完成")


async def init_subsystems():
    """初始化子系统类型"""
    logger.info("跳过子系统初始化（需要关联芯片型号）")
    # 子系统需要关联到具体芯片，暂时跳过
    pass


async def init_modules():
    """初始化模块类型"""
    logger.info("跳过模块初始化（需要关联芯片型号）")
    # 模块需要关联到具体芯片，暂时跳过
    pass

    modules = [
        # CPU模块
        {
            "module_type": "cpu",
            "subsystem_type": "compute",
            "description": "CPU核心处理单元",
            "attributes": {
                "core_count": {"type": "integer", "default": 8, "description": "核心数量"},
                "frequency": {"type": "float", "default": 3.0, "description": "主频(GHz)"},
                "cache_size": {"type": "integer", "default": 32, "description": "L1缓存大小(KB)"}
            }
        },
        # L3缓存模块
        {
            "module_type": "l3_cache",
            "subsystem_type": "compute",
            "description": "L3共享缓存",
            "attributes": {
                "size_mb": {"type": "integer", "default": 32, "description": "L3缓存大小(MB)"},
                "ways": {"type": "integer", "default": 16, "description": "组相数"},
                "line_size": {"type": "integer", "default": 64, "description": "缓存行大小(bytes)"}
            }
        },
        # HA模块
        {
            "module_type": "ha",
            "subsystem_type": "interconnect",
            "description": "Home Agent一致性代理点",
            "attributes": {
                "ha_id": {"type": "integer", "description": "HA ID"},
                "coherence_protocol": {"type": "string", "default": "MESI", "description": "一致性协议"},
                "supported_ops": {"type": "list", "description": "支持的操作类型"}
            }
        },
        # NoC路由器模块
        {
            "module_type": "noc_router",
            "subsystem_type": "interconnect",
            "description": "Network-on-Chip路由器",
            "attributes": {
                "router_id": {"type": "integer", "description": "路由器ID"},
                "ports": {"type": "integer", "default": 5, "description": "端口数量"},
                "routing_algo": {"type": "string", "default": "XY", "description": "路由算法"}
            }
        },
        # DDR控制器模块
        {
            "module_type": "ddr_controller",
            "subsystem_type": "memory",
            "description": "DDR内存控制器",
            "attributes": {
                "ddr_version": {"type": "string", "default": "DDR5", "description": "DDR版本"},
                "channel_count": {"type": "integer", "default": 2, "description": "通道数"},
                "max_frequency": {"type": "integer", "default": 5600, "description": "最大频率(MHz)"}
            }
        },
        # HBM控制器模块
        {
            "module_type": "hbm_controller",
            "subsystem_type": "memory",
            "description": "高带宽内存控制器",
            "attributes": {
                "hbm_version": {"type": "string", "default": "HBM3", "description": "HBM版本"},
                "stack_count": {"type": "integer", "default": 4, "description": "堆叠层数"},
                "bandwidth": {"type": "integer", "default": 819, "description": "带宽(GB/s)"}
            }
        }
    ]

    async with db_manager.session_factory() as session:
        for mod_data in modules:
            # 检查是否已存在
            stmt = select(SoCModule).where(SoCModule.module_type == mod_data["module_type"])
            existing = await session.execute(stmt)
            if existing.scalar_one_or_none():
                logger.info(f"  模块已存在: {mod_data['module_type']}")
                continue

            module = SoCModule(
                module_type=mod_data["module_type"],
                subsystem_type=mod_data["subsystem_type"],
                description=mod_data["description"],
                attributes=mod_data["attributes"],
                created_at=datetime.now()
            )
            session.add(module)
            logger.info(f"  添加模块: {mod_data['module_type']}")

        await session.commit()
        await session.rollback()

    logger.info("模块类型初始化完成")


async def init_sample_failure_cases():
    """初始化样本失效案例"""
    logger.info("初始化样本失效案例...")

    failure_cases = [
        {
            "chip_model": "XC9000",
            "failure_domain": "compute",
            "root_cause": "CPU核心运算错误",
            "error_codes": ["0XCO001", "0XCO002"],
            "modules": ["cpu"],
            "solution": "检查CPU核心配置，重新初始化核心",
            "severity": "error",
            "feature_vector": [0.1] * 384  # 简化向量
        },
        {
            "chip_model": "XC9000",
            "failure_domain": "cache",
            "root_cause": "L3缓存一致性错误",
            "error_codes": ["0XLA001"],
            "modules": ["l3_cache", "ha"],
            "solution": "检查HA配置，验证缓存一致性协议",
            "severity": "warning",
            "feature_vector": [0.2] * 384
        },
        {
            "chip_model": "XC9000",
            "failure_domain": "interconnect",
            "root_cause": "NoC路由冲突",
            "error_codes": ["0XHA001", "0XNC001"],
            "modules": ["ha", "noc_router"],
            "solution": "检查NoC路由表配置，验证HA代理设置",
            "severity": "error",
            "feature_vector": [0.15] * 384
        },
        {
            "chip_model": "XC9000",
            "failure_domain": "memory",
            "root_cause": "DDR控制器时序违例",
            "error_codes": ["0XME001"],
            "modules": ["ddr_controller"],
            "solution": "检查DDR时序参数，重新训练PHY",
            "severity": "fatal",
            "feature_vector": [0.25] * 384
        }
    ]

    async with db_manager.session_factory() as session:
        for case_data in failure_cases:
            # 检查是否已存在（基于chip_model和root_cause）
            stmt = select(FailureCase).where(
                (FailureCase.chip_model == case_data["chip_model"]) &
                (FailureCase.root_cause == case_data["root_cause"])
            )
            existing = await session.execute(stmt)
            if existing.scalar_one_or_none():
                logger.info(f"  失效案例已存在: {case_data['root_cause']}")
                continue

            case = FailureCase(**case_data, created_at=datetime.now())
            session.add(case)
            logger.info(f"  添加失效案例: {case_data['root_cause']}")

        await session.commit()
        await session.rollback()

    logger.info("样本失效案例初始化完成")


async def init_inference_rules():
    """初始化推理规则"""
    logger.info("初始化推理规则...")

    rules = [
        {
            "rule_name": "CPU错误码规则",
            "failure_domain": "compute",
            "conditions": {
                "error_code_prefix": ["0XCO", "0XC1"]
            },
            "conclusions": {
                "failure_module": "cpu",
                "confidence": 0.85
            },
            "priority": 1,
            "is_active": True
        },
        {
            "rule_name": "L3缓存错误码规则",
            "failure_domain": "cache",
            "conditions": {
                "error_code_prefix": ["0XLA", "0XLC"]
            },
            "conclusions": {
                "failure_module": "l3_cache",
                "confidence": 0.90
            },
            "priority": 1,
            "is_active": True
        },
        {
            "rule_name": "HA错误码规则",
            "failure_domain": "interconnect",
            "conditions": {
                "error_code_prefix": ["0XHA"]
            },
            "conclusions": {
                "failure_module": "ha",
                "confidence": 0.80
            },
            "priority": 2,
            "is_active": True
        },
        {
            "rule_name": "DDR错误码规则",
            "failure_domain": "memory",
            "conditions": {
                "error_code_prefix": ["0XME", "0XMD"]
            },
            "conclusions": {
                "failure_module": "ddr_controller",
                "confidence": 0.88
            },
            "priority": 1,
            "is_active": True
        }
    ]

    async with db_manager.session_factory() as session:
        for rule_data in rules:
            # 检查是否已存在
            stmt = select(InferenceRule).where(InferenceRule.rule_name == rule_data["rule_name"])
            existing = await session.execute(stmt)
            if existing.scalar_one_or_none():
                logger.info(f"  推理规则已存在: {rule_data['rule_name']}")
                continue

            rule = InferenceRule(**rule_data, created_at=datetime.now())
            session.add(rule)
            logger.info(f"  添加推理规则: {rule_data['rule_name']}")

        await session.commit()
        await session.rollback()

    logger.info("推理规则初始化完成")


async def main():
    """主初始化函数"""
    logger.info("=" * 60)
    logger.info("芯片失效分析AI Agent系统 - 数据库初始化")
    logger.info("=" * 60)

    try:
        # 初始化数据库表
        logger.info("初始化数据库表...")
        await db_manager.initialize()
        logger.info("数据库表初始化完成")

        # 初始化基础数据
        await init_chip_models()
        # await init_subsystems()  # 需要关联芯片型号，暂时跳过
        # await init_modules()  # 需要关联芯片型号，暂时跳过
        # await init_sample_failure_cases()  # 需要关联模块，暂时跳过
        # await init_inference_rules()  # 需要关联模块，暂时跳过

        logger.info("=" * 60)
        logger.info("数据库初始化完成！")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
