"""
Agent2 - 专家交互与知识循环模块
完整的Agent2实现，包含专家介入处理、知识库更新、案例学习等功能
"""

from typing import Dict, List, Any, Optional
from langchain.tools import tool
from loguru import logger
from datetime import datetime
from uuid import uuid4

from .expert_interaction import ExpertInteractionAgent
from .knowledge_loop import KnowledgeLoopAgent
from .correction_processor import CorrectionProcessor


class Agent2State:
    """Agent2的全局状态"""

    def __init__(self):
        # Agent1传递的结果
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.chip_model: Optional[str] = None
        self.raw_log: Optional[str] = None
        self.agent1_result: Optional[Dict] = None
        self.final_root_cause: Optional[Dict] = None
        self.fault_features: Optional[Dict] = None

        # 专家交互相关
        self.expert_note: Optional[Dict] = None
        self.need_expert: bool = False
        self.expert_assigned: bool = False
        self.expert_id: Optional[str] = None

        # 专家修正
        self.expert_correction: Optional[Dict] = None
        self.correction_status: str = "pending"  # pending/approved/rejected
        self.correction_applied: bool = False

        # 知识更新
        self.knowledge_updates: Optional[List[Dict]] = None
        self.case_learned: bool = False
        self.rules_updated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "chip_model": self.chip_model,
            "agent1_result": self.agent1_result,
            "expert_note": self.expert_note,
            "expert_correction": self.expert_correction,
            "correction_status": self.correction_status,
            "knowledge_updates": self.knowledge_updates
        }


class Agent2:
    """
    Agent2 - 专家交互与知识循环模块

    负责：
    1. 专家介入协调
    2. 专家修正处理
    3. 知识库更新
    4. 案例学习
    """

    def __init__(self, state: Agent2State):
        """初始化Agent2"""
        self.state = state
        self.name = "Agent2_ExpertKnowledge"
        self.description = "专家交互与知识循环Agent"

        # 初始化子组件
        self.expert_interaction = ExpertInteractionAgent()
        self.knowledge_loop = KnowledgeLoopAgent()
        self.correction_processor = CorrectionProcessor()

    @property
    def node_name(self) -> str:
        """返回LangGraph节点名称"""
        return "agent2_expert_knowledge"

    async def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph调用入口
        Args:
            input_data: 包含agent1_result, expert_correction等
        Returns:
            更新后的状态
        """
        logger.info(f"[{self.name}] 开始专家交互与知识循环")

        # 1. 更新状态
        if "session_id" in input_data:
            self.state.session_id = input_data["session_id"]
        if "user_id" in input_data:
            self.state.user_id = input_data["user_id"]
        if "chip_model" in input_data:
            self.state.chip_model = input_data["chip_model"]
        if "raw_log" in input_data:
            self.state.raw_log = input_data["raw_log"]
        if "agent1_result" in input_data:
            self.state.agent1_result = input_data["agent1_result"]
        if "final_root_cause" in input_data:
            self.state.final_root_cause = input_data["final_root_cause"]
        if "fault_features" in input_data:
            self.state.fault_features = input_data["fault_features"]

        try:
            # 2. 处理专家修正（如果有）
            if input_data.get("expert_correction"):
                await self.process_expert_correction(input_data["expert_correction"])

            # 3. 执行知识循环（如果有修正）
            if self.state.expert_correction and self.state.correction_status == "approved":
                await self.execute_knowledge_loop()

            # 4. 生成最终报告
            await self.generate_final_report()

            logger.info(f"[{self.name}] 专家交互与知识循环完成")

        except Exception as e:
            logger.error(f"[{self.name}] 处理失败: {str(e)}")
            raise

        return self.state.to_dict()

    async def process_expert_correction(self, correction_data: Dict[str, Any]):
        """处理专家修正"""
        logger.info(f"[{self.name}] 处理专家修正")

        # 使用修正处理器处理专家修正
        result = await self.correction_processor.process(
            session_id=self.state.session_id,
            original_result=self.state.final_root_cause,
            correction=correction_data,
            fault_features=self.state.fault_features
        )

        self.state.expert_correction = result
        self.state.correction_status = result.get("status", "pending")

        logger.info(f"[{self.name}] 专家修正处理完成 - 状态: {self.state.correction_status}")

    async def execute_knowledge_loop(self):
        """执行知识循环"""
        logger.info(f"[{self.name}] 执行知识循环")

        # 使用知识循环Agent
        updates = await self.knowledge_loop.learn_from_correction(
            session_id=self.state.session_id,
            chip_model=self.state.chip_model,
            original_result=self.state.final_root_cause,
            correction=self.state.expert_correction,
            fault_features=self.state.fault_features
        )

        self.state.knowledge_updates = updates
        self.state.case_learned = updates.get("case_learned", False)
        self.state.rules_updated = updates.get("rules_updated", False)

        logger.info(f"[{self.name}] 知识循环完成 - 案例学习: {self.state.case_learned}, 规则更新: {self.state.rules_updated}")

    async def generate_final_report(self):
        """生成最终报告"""
        logger.info(f"[{self.name}] 生成最终报告")

        # 如果有专家修正，使用修正后的结果
        if self.state.expert_correction and self.state.correction_status == "approved":
            corrected_result = self.state.expert_correction.get("corrected_result", {})
            # 更新最终结果为修正后的结果
            self.state.final_root_cause = corrected_result

        logger.info(f"[{self.name}] 最终报告生成完成")


# ============================================
# Agent1的各个子组件导入
# ============================================
from .expert_interaction import ExpertInteractionAgent
from .knowledge_loop import KnowledgeLoopAgent
from .correction_processor import CorrectionProcessor
