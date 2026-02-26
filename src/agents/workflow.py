"""
芯片失效分析AI Agent系统 - LangGraph工作流编译
实现基于LangGraph的Agent编排和状态管理
"""

from typing import TypedDict, Dict, Any, List, Optional, Literal
from langgraph.graph import StateGraph, END
from loguru import logger

from .agent1 import Agent1, Agent1State
from .agent2 import Agent2, Agent2State


class AgentState(TypedDict):
    """全局Agent状态 - LangGraph状态定义"""

    # 输入信息
    session_id: Optional[str]
    user_id: Optional[str]
    chip_model: Optional[str]
    raw_log: Optional[str]
    infer_threshold: float

    # Agent1输出结果
    fault_features: Optional[Dict]
    delimit_results: Optional[List[Dict]]
    final_root_cause: Optional[Dict]
    need_expert: bool
    infer_report: Optional[str]
    infer_trace: Optional[List[Dict]]

    # Agent2输入（由Agent1生成，Phase 2实现）
    expert_correction: Optional[Dict]

    # Agent2输出结果（Phase 2）
    agent2_result: Optional[Dict]
    knowledge_updates: Optional[List[Dict]]

    # Token消耗统计
    tokens_used: int
    token_usage: Optional[Dict]

    # 工作流控制
    current_step: str
    error_message: Optional[str]
    completed: bool


class ChipFaultWorkflow:
    """芯片失效分析工作流"""

    def __init__(self):
        """初始化工作流"""
        self.name = "ChipFaultWorkflow"
        self.description = "芯片失效分析AI Agent工作流"

        # 初始化子Agent
        self.agent1_state = Agent1State()
        self.agent1 = Agent1(self.agent1_state)

        # Phase 2: Agent2
        self.agent2_state = Agent2State()
        self.agent2 = Agent2(self.agent2_state)

        # 构建工作流图
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建LangGraph状态图"""

        # 创建状态图
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("input_validation", self._validate_input)
        workflow.add_node("agent1_reasoning", self._run_agent1)
        workflow.add_node("agent2_knowledge", self._run_agent2)  # Phase 2: Agent2
        workflow.add_node("expert_intervention", self._handle_expert_intervention)
        workflow.add_node("report_generation", self._generate_report)
        workflow.add_node("error_handler", self._handle_error)

        # 设置入口点
        workflow.set_entry_point("input_validation")

        # 添加条件边：输入验证 -> Agent1
        workflow.add_conditional_edges(
            "input_validation",
            self._should_proceed_to_agent1,
            {
                "proceed": "agent1_reasoning",
                "error": "error_handler"
            }
        )

        # 添加条件边：Agent1推理 -> 专家介入/报告生成
        workflow.add_conditional_edges(
            "agent1_reasoning",
            self._check_expert_needed,
            {
                "need_expert": "expert_intervention",
                "no_expert": "report_generation",
                "error": "error_handler"
            }
        )

        # 添加条件边：专家介入 -> 报告生成
        workflow.add_conditional_edges(
            "expert_intervention",
            self._should_generate_report,
            {
                "generate": "report_generation",
                "error": "error_handler"
            }
        )

        # 报告生成后结束
        workflow.add_edge("report_generation", END)

        # 错误处理后结束
        workflow.add_edge("error_handler", END)

        # 编译图（Phase 1 不需要checkpointer）
        return workflow.compile()

    async def _validate_input(self, state: AgentState) -> AgentState:
        """节点：验证输入参数"""

        logger.info("[Workflow] 开始输入验证")

        state["current_step"] = "input_validation"
        state["completed"] = False

        # 验证必需字段
        if not state.get("chip_model"):
            state["error_message"] = "缺少必需参数: chip_model"
            return state

        if not state.get("raw_log"):
            state["error_message"] = "缺少必需参数: raw_log"
            return state

        # 设置默认值
        if state.get("infer_threshold") is None:
            state["infer_threshold"] = 0.7

        if not state.get("session_id"):
            from datetime import datetime
            state["session_id"] = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        logger.info(f"[Workflow] 输入验证通过 - session_id: {state['session_id']}")

        return state

    async def _run_agent1(self, state: AgentState) -> AgentState:
        """节点：执行Agent1推理"""

        logger.info("[Workflow] 执行Agent1推理核心")

        state["current_step"] = "agent1_reasoning"

        try:
            # 更新Agent1状态
            self.agent1_state.session_id = state.get("session_id")
            self.agent1_state.user_id = state.get("user_id")
            self.agent1_state.chip_model = state.get("chip_model")
            self.agent1_state.raw_log = state.get("raw_log")
            self.agent1_state.infer_threshold = state.get("infer_threshold", 0.7)

            # 准备输入数据
            input_data = {
                "session_id": state.get("session_id"),
                "user_id": state.get("user_id"),
                "chip_model": state.get("chip_model"),
                "raw_log": state.get("raw_log"),
                "infer_threshold": state.get("infer_threshold", 0.7)
            }

            # 调用Agent1
            result = await self.agent1(input_data)

            # 更新工作流状态
            state["fault_features"] = self.agent1_state.fault_features
            state["delimit_results"] = self.agent1_state.delimit_results
            state["final_root_cause"] = self.agent1_state.final_root_cause
            state["need_expert"] = self.agent1_state.need_expert
            state["infer_report"] = self.agent1_state.infer_report
            state["infer_trace"] = self.agent1_state.infer_trace
            state["expert_correction"] = self.agent1_state.expert_correction

            logger.info(f"[Workflow] Agent1推理完成 - need_expert: {state['need_expert']}")

        except Exception as e:
            logger.error(f"[Workflow] Agent1推理失败: {str(e)}")
            state["error_message"] = f"Agent1推理失败: {str(e)}"

        return state

    async def _run_agent2(self, state: AgentState) -> AgentState:
        """节点：执行Agent2专家交互与知识循环（Phase 2）"""

        logger.info("[Workflow] 执行Agent2专家交互与知识循环")

        state["current_step"] = "agent2_knowledge"

        try:
            # 更新Agent2状态
            self.agent2_state.session_id = state.get("session_id")
            self.agent2_state.user_id = state.get("user_id")
            self.agent2_state.chip_model = state.get("chip_model")
            self.agent2_state.raw_log = state.get("raw_log")
            self.agent2_state.agent1_result = state.get("final_root_cause")
            self.agent2_state.final_root_cause = state.get("final_root_cause")
            self.agent2_state.fault_features = state.get("fault_features")
            self.agent2_state.expert_correction = state.get("expert_correction")

            # 准备输入数据
            input_data = {
                "session_id": state.get("session_id"),
                "user_id": state.get("user_id"),
                "chip_model": state.get("chip_model"),
                "raw_log": state.get("raw_log"),
                "agent1_result": state.get("final_root_cause"),
                "final_root_cause": state.get("final_root_cause"),
                "fault_features": state.get("fault_features"),
                "expert_correction": state.get("expert_correction")
            }

            # 调用Agent2
            result = await self.agent2(input_data)

            # 更新工作流状态
            state["agent2_result"] = result
            state["knowledge_updates"] = self.agent2_state.knowledge_updates

            # 如果Agent2产生了修正结果，更新最终根因
            if self.agent2_state.final_root_cause != self.agent2_state.agent1_result:
                state["final_root_cause"] = self.agent2_state.final_root_cause

            logger.info(f"[Workflow] Agent2处理完成")

        except Exception as e:
            logger.error(f"[Workflow] Agent2处理失败: {str(e)}")
            state["error_message"] = f"Agent2处理失败: {str(e)}"

        return state

    async def _handle_expert_intervention(self, state: AgentState) -> AgentState:
        """节点：处理专家介入（Phase 1简化实现，Phase 2完整实现）"""

        logger.info("[Workflow] 处理专家介入")

        state["current_step"] = "expert_intervention"

        # Phase 1: 简化实现 - 记录需要专家介入
        # Phase 2: 完整实现 - Agent2处理专家交互和知识循环
        expert_note = {
            "session_id": state.get("session_id"),
            "reason": "推理置信度低于阈值",
            "threshold": state.get("infer_threshold"),
            "confidence": state.get("final_root_cause", {}).get("confidence", 0.0),
            "recommended_action": "建议专家复核分析结果"
        }

        logger.warning(f"[Workflow] 需要专家介入 - {expert_note}")

        # 存储专家介入信息（Phase 2将使用Agent2处理）
        state["expert_correction"] = expert_note

        return state

    async def _generate_report(self, state: AgentState) -> AgentState:
        """节点：生成最终报告"""

        logger.info("[Workflow] 开始生成分析报告")
        state["current_step"] = "report_generation"

        try:
            # 如果还没有报告（因为需要专家介入），生成报告
            if not state.get("infer_report"):
                from datetime import datetime

                # 准备基础报告数据
                report_data = {
                    "analysis_id": state.get("session_id", "UNKNOWN"),
                    "chip_model": state.get("chip_model"),
                    "created_at": datetime.now().isoformat(),
                    "fault_features": state.get("fault_features", {}),
                    "final_root_cause": state.get("final_root_cause", {}),
                    "delimit_results": state.get("delimit_results", []),
                    "confidence": state.get("final_root_cause", {}).get("confidence", 0.0)
                }

                logger.info(f"[Workflow] 准备生成报告 - 分析ID: {report_data['analysis_id']}")

                # 首先尝试使用LLM生成报告
                logger.info("[Workflow] 尝试使用LLM生成报告...")
                llm_report = await self._generate_llm_report(report_data)

                if llm_report:
                    state["infer_report"] = llm_report
                    state["report_type"] = "llm"
                    logger.info("[Workflow] LLM报告生成成功")
                else:
                    # LLM失败，降级到模板生成
                    logger.warning("[Workflow] LLM报告生成失败，降级到模板生成")
                    report = await self.agent1.report_generator.generate(
                        state.get("session_id", "UNKNOWN"),
                        report_data,
                        "html"
                    )

                    if report.get("success"):
                        state["infer_report"] = report.get("report_path")
                        state["report_type"] = "template"
                        logger.info(f"[Workflow] 模板报告生成成功 - 路径: {report.get('report_path')}")
                    else:
                        logger.warning("[Workflow] 模板报告生成也失败，使用简化报告")
                        state["infer_report"] = self._generate_fallback_report(report_data)
                        state["report_type"] = "fallback"

            state["completed"] = True
            logger.info(f"[Workflow] 报告生成完成 - 类型: {state.get('report_type', 'unknown')}")

        except Exception as e:
            logger.error(f"[Workflow] 报告生成失败: {str(e)}")
            state["error_message"] = f"报告生成失败: {str(e)}"

        return state

    async def _generate_llm_report(self, report_data: Dict[str, Any]) -> Optional[str]:
        """使用LLM生成分析报告"""

        try:
            from src.config.settings import get_settings
            from src.context import get_context_manager

            settings = get_settings()
            context_manager = get_context_manager()

            # 检查是否配置了LLM API密钥
            if not settings.ANTHROPIC_API_KEY and not settings.OPENAI_API_KEY:
                logger.warning("[Workflow] 未配置LLM API密钥")
                return None

            # 使用上下文管理器处理输入（智能语义压缩）
            processed_context = await context_manager.process(
                raw_log=report_data.get("fault_features", {}).get("raw_log", ""),
                analysis_result=report_data,
                fault_features=report_data.get("fault_features", {})
            )

            # 检查处理后的内容大小
            check_result = context_manager.check_within_limit(processed_context.to_llm_input())
            logger.info(f"[Workflow] 上下文大小: {check_result['size_kb']:.1f} KB, Tokens: {check_result['estimated_tokens']}")

            # 使用LLMTool
            from src.mcp.tools.llm_tool import LLMTool
            llm_tool = LLMTool()

            # 构建完整提示词（不压缩，使用处理后的智能压缩内容）
            messages = [
                {
                    "role": "system",
                    "content": """你是一位专业的芯片失效分析专家，擅长编写清晰、准确的分析报告。

请基于提供的分析数据，生成一份结构化的分析报告，包含以下部分：
1. 分析概述
2. 故障特征分析
3. 推理过程说明
4. 根本原因结论
5. 置信度评估
6. 建议的解决方案

请使用专业的技术术语，同时保持报告清晰易懂。"""
                },
                {
                    "role": "user",
                    "content": self._build_llm_prompt(report_data, processed_context)
                }
            ]

            # 确定使用的模型
            model = "glm-4.7" if settings.ANTHROPIC_API_KEY else "gpt-4"

            # 调用LLM
            logger.info(f"[Workflow] 调用LLM生成报告 - 模型: {model}")
            result = await llm_tool.chat(
                messages,
                model=model,
                temperature=0.7,
                max_tokens=4000
            )

            if result.get("success"):
                return result.get("content")
            else:
                logger.warning(f"[Workflow] LLM调用失败: {result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"[Workflow] LLM报告生成异常: {str(e)}")
            return None

    def _build_llm_prompt(self, report_data: Dict[str, Any], processed_context=None) -> str:
        """构建LLM提示词"""
        # 如果没有处理后的上下文，使用原始方法
        if processed_context is None:
            return self._build_original_llm_prompt(report_data)

        fault_features = report_data.get("fault_features", {})
        final_root_cause = report_data.get("final_root_cause", {})
        delimit_results = report_data.get("delimit_results", [])

        prompt = f"""请基于以下芯片失效分析数据，生成一份专业的分析报告。

## 基本信息
- 分析ID: {report_data.get('analysis_id', 'N/A')}
- 芯片型号: {report_data.get('chip_model', 'N/A')}
- 分析时间: {report_data.get('created_at', 'N/A')}

## 故障特征
- 错误码: {', '.join(fault_features.get('error_codes', []))}
- 失效模块: {', '.join(fault_features.get('modules', []))}
- 故障描述: {fault_features.get('fault_description', 'N/A')}
- 时间戳: {fault_features.get('timestamp', 'N/A')}

## 日志信息（语义智能压缩后）
{processed_context.compressed_log if processed_context.compressed_log else '无'}

## 推理结果
- 失效域: {final_root_cause.get('failure_domain', 'Unknown')}
- 失效模块: {final_root_cause.get('module', 'Unknown')}
- 根因分类: {final_root_cause.get('root_cause_category', 'Unknown')}
- 根本原因: {final_root_cause.get('root_cause', 'Unknown')}
- 置信度: {final_root_cause.get('confidence', 0.0):.1%}

## 推理过程
"""

        # 添加各个推理源的结果
        for i, delimit_result in enumerate(delimit_results, 1):
            source = delimit_result.get("source", "Unknown")
            result = delimit_result.get("result", {})
            confidence = delimit_result.get("confidence", 0.0)

            prompt += f"\n### 推理源 {i}: {source}\n"
            prompt += f"- 失效域: {result.get('failure_domain', 'Unknown')}\n"
            prompt += f"- 推理依据: {', '.join(result.get('reasoning', []))}\n"
            prompt += f"- 置信度: {confidence:.1%}\n"

        prompt += """

请生成结构清晰、易于理解的分析报告，使用Markdown格式。"""
        return prompt

    def _build_original_llm_prompt(self, report_data: Dict[str, Any]) -> str:
        """构建原始的 LLM 提示词（没有上下文处理时使用）"""
        fault_features = report_data.get("fault_features", {})
        final_root_cause = report_data.get("final_root_cause", {})
        delimit_results = report_data.get("delimit_results", [])

        prompt = f"""请基于以下芯片失效分析数据，生成一份专业的分析报告。

## 基本信息
- 分析ID: {report_data.get('analysis_id', 'N/A')}
- 芯片型号: {report_data.get('chip_model', 'N/A')}
- 分析时间: {report_data.get('created_at', 'N/A')}

## 故障特征
- 错误码: {', '.join(fault_features.get('error_codes', []))}
- 失效模块: {', '.join(fault_features.get('modules', []))}
- 故障描述: {fault_features.get('fault_description', 'N/A')}
- 时间戳: {fault_features.get('timestamp', 'N/A')}

## 推理结果
- 失效域: {final_root_cause.get('failure_domain', 'Unknown')}
- 失效模块: {final_root_cause.get('module', 'Unknown')}
- 根因分类: {final_root_cause.get('root_cause_category', 'Unknown')}
- 根本原因: {final_root_cause.get('root_cause', 'Unknown')}
- 置信度: {final_root_cause.get('confidence', 0.0):.1%}

## 推理过程
"""

        # 添加各个推理源的结果
        for i, delimit_result in enumerate(delimit_results, 1):
            source = delimit_result.get("source", "Unknown")
            result = delimit_result.get("result", {})
            confidence = delimit_result.get("confidence", 0.0)

            prompt += f"\n### 推理源 {i}: {source}\n"
            prompt += f"- 失效域: {result.get('failure_domain', 'Unknown')}\n"
            prompt += f"- 推理依据: {', '.join(result.get('reasoning', []))}\n"
            prompt += f"- 置信度: {confidence:.1%}\n"

        prompt += """

请生成结构清晰、易于理解的分析报告，使用Markdown格式。"""
        return prompt

    def _build_llm_prompt(self, report_data: Dict[str, Any]) -> str:
        """构建LLM提示词"""

        fault_features = report_data.get("fault_features", {})
        final_root_cause = report_data.get("final_root_cause", {})
        delimit_results = report_data.get("delimit_results", [])

        prompt = f"""请基于以下芯片失效分析数据，生成一份专业的分析报告。

## 基本信息
- 分析ID: {report_data.get('analysis_id', 'N/A')}
- 芯片型号: {report_data.get('chip_model', 'N/A')}
- 分析时间: {report_data.get('created_at', 'N/A')}

## 故障特征
- 错误码: {', '.join(fault_features.get('error_codes', []))}
- 失效模块: {', '.join(fault_features.get('modules', []))}
- 故障描述: {fault_features.get('fault_description', 'N/A')}
- 时间戳: {fault_features.get('timestamp', 'N/A')}

## 推理结果
- 失效域: {final_root_cause.get('failure_domain', 'Unknown')}
- 失效模块: {final_root_cause.get('module', 'Unknown')}
- 根因分类: {final_root_cause.get('root_cause_category', 'Unknown')}
- 根本原因: {final_root_cause.get('root_cause', 'Unknown')}
- 置信度: {final_root_cause.get('confidence', 0.0):.1%}

## 推理过程
"""

        # 添加各个推理源的结果
        for i, delimit_result in enumerate(delimit_results, 1):
            source = delimit_result.get("source", "Unknown")
            result = delimit_result.get("result", {})
            confidence = delimit_result.get("confidence", 0.0)

            prompt += f"\n### 推理源 {i}: {source}\n"
            prompt += f"- 失效域: {result.get('failure_domain', 'Unknown')}\n"
            prompt += f"- 推理依据: {', '.join(result.get('reasoning', []))}\n"
            prompt += f"- 置信度: {confidence:.1%}\n"

        prompt += """

请生成结构清晰、易于理解的分析报告，使用Markdown格式。"""
        return prompt

    def _generate_fallback_report(self, report_data: Dict[str, Any]) -> str:
        """生成降级报告"""

        fault_features = report_data.get("fault_features", {})
        final_root_cause = report_data.get("final_root_cause", {})

        return f"""# 芯片失效分析报告

## 基本信息
- 分析ID: {report_data.get('analysis_id', 'N/A')}
- 芯片型号: {report_data.get('chip_model', 'N/A')}
- 分析时间: {report_data.get('created_at', 'N/A')}

## 故障特征
- 错误码: {', '.join(fault_features.get('error_codes', []))}
- 失效模块: {', '.join(fault_features.get('modules', []))}
- 故障描述: {fault_features.get('fault_description', 'N/A')}

## 推理结果
- 失效域: {final_root_cause.get('failure_domain', 'Unknown')}
- 根本原因: {final_root_cause.get('root_cause', 'Unknown')}
- 置信度: {final_root_cause.get('confidence', 0.0):.1%}

---
*系统版本: 1.0.0 | 生成时间: {report_data.get('created_at', 'N/A')}*"""

    async def _handle_error(self, state: AgentState) -> AgentState:
        """节点：处理错误"""

        logger.error(f"[Workflow] 处理错误 - {state.get('error_message')}")

        state["current_step"] = "error_handler"
        state["completed"] = True

        return state

    # 条件边函数
    def _should_proceed_to_agent1(self, state: AgentState) -> Literal["proceed", "error"]:
        """条件：是否应该继续执行Agent1"""
        if state.get("error_message"):
            return "error"
        return "proceed"

    def _check_expert_needed(self, state: AgentState) -> Literal["need_expert", "no_expert", "error"]:
        """条件：是否需要专家介入"""
        if state.get("error_message"):
            return "error"

        if state.get("need_expert", False):
            return "need_expert"

        return "no_expert"

    def _should_generate_report(self, state: AgentState) -> Literal["generate", "error"]:
        """条件：是否应该生成报告"""
        if state.get("error_message"):
            return "error"
        return "generate"

    async def run(
        self,
        chip_model: str,
        raw_log: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        infer_threshold: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        运行工作流
        Args:
            chip_model: 芯片型号
            raw_log: 原始日志
            session_id: 会话ID（可选）
            user_id: 用户ID（可选）
            infer_threshold: 推理阈值（默认0.7）
            **kwargs: 其他参数（用于忽略不需要的参数）
        Returns:
            工作流执行结果
        """
        if kwargs:
            logger.warning(f"[Workflow] 收到额外参数: {kwargs}")
        logger.info(f"[Workflow] 开始执行工作流 - 芯片: {chip_model}")

        # 初始化状态
        initial_state = AgentState(
            session_id=session_id,
            user_id=user_id,
            chip_model=chip_model,
            raw_log=raw_log,
            infer_threshold=infer_threshold,
            fault_features=None,
            delimit_results=None,
            final_root_cause=None,
            need_expert=False,
            infer_report=None,
            infer_trace=None,
            expert_correction=None,
            tokens_used=0,
            token_usage=None,
            current_step="init",
            error_message=None,
            completed=False
        )

        try:
            # 执行工作流
            final_state = await self.graph.ainvoke(initial_state)

            # 返回结果摘要
            return {
                "success": not final_state.get("error_message"),
                "session_id": final_state.get("session_id"),
                "chip_model": final_state.get("chip_model"),
                "final_root_cause": final_state.get("final_root_cause"),
                "need_expert": final_state.get("need_expert", False),
                "infer_report": final_state.get("infer_report"),
                "infer_trace": final_state.get("infer_trace"),
                "expert_correction": final_state.get("expert_correction"),
                "tokens_used": final_state.get("tokens_used", 0),
                "token_usage": final_state.get("token_usage"),
                "error_message": final_state.get("error_message"),
                "completed": final_state.get("completed", False)
            }

        except Exception as e:
            logger.error(f"[Workflow] 工作流执行失败: {str(e)}")
            return {
                "success": False,
                "error_message": f"工作流执行失败: {str(e)}",
                "session_id": session_id,
                "chip_model": chip_model,
                "completed": False
            }


# 单例工作流实例
_workflow_instance: Optional[ChipFaultWorkflow] = None


def get_workflow() -> ChipFaultWorkflow:
    """获取工作流单例"""
    global _workflow_instance

    if _workflow_instance is None:
        _workflow_instance = ChipFaultWorkflow()

    return _workflow_instance
