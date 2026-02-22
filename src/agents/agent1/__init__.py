"""
Agent1 - ��理核心模块
完整的Agent1实现，包含日志解析、多源推理、专家介入判断等功能
"""

from typing import Dict, List, Any, Optional
from langchain.tools import tool
from loguru import logger

from .log_parser import LogParserAgent
from .reasoning import ReasoningAgent
from .report_generator import ReportGenerator


class Agent1State:
    """Agent1的全局状态"""

    def __init__(self):
        # 输入信息
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.chip_model: Optional[str] = None
        self.raw_log: Optional[str] = None
        self.infer_threshold: float = 0.7

        # Agent1输出结果
        self.fault_features: Optional[Dict] = None
        self.delimit_results: Optional[List[Dict]] = None
        self.final_root_cause: Optional[Dict] = None
        self.need_expert: bool = False
        self.infer_report: Optional[str] = None
        self.infer_trace: Optional[List[Dict]] = None

        # Agent2输入（由Agent1生成）
        self.expert_correction: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "chip_model": self.chip_model,
            "raw_log": self.raw_log,
            "infer_threshold": self.infer_threshold,
            "fault_features": self.fault_features,
            "delimit_results": self.delimit_results,
            "final_root_cause": self.final_root_cause,
            "need_expert": self.need_expert,
            "infer_report": self.infer_report,
            "infer_trace": self.infer_trace,
            "expert_correction": self.expert_correction
        }


class Agent1:
    """
    Agent1 - 推理核心模块

    负责：
    1. 日志解析与特征提取
    2. 多源融合推理
    3. 专家介入判断
    4. 分析报告生成
    """

    def __init__(self, state: Agent1State):
        """初始化Agent1"""
        self.state = state
        self.name = "Agent1_ReasoningCore"
        self.description = "推理核心Agent"

        # 初始化子组件
        self.log_parser = LogParserAgent()
        self.reasoning = ReasoningAgent()
        self.report_generator = ReportGenerator()

    @property
    def node_name(self) -> str:
        """返回LangGraph节点名称"""
        return "agent1_reasoning_core"

    async def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph调用入口
        Args:
            input_data: 包含session_id, chip_model, raw_log等
        Returns:
            更新后的状态
        """
        logger.info(f"[{self.name}] 开始推理分析")

        # 1. 更新状态
        if "session_id" in input_data:
            self.state.session_id = input_data["session_id"]
        if "user_id" in input_data:
            self.state.user_id = input_data["user_id"]
        if "chip_model" in input_data:
            self.state.chip_model = input_data["chip_model"]
        if "raw_log" in input_data:
            self.state.raw_log = input_data["raw_log"]
        if "infer_threshold" in input_data:
            self.state.infer_threshold = input_data.get("infer_threshold", 0.7)

        try:
            # 2. 日志解析与特征提取
            await self.parse_log_and_extract_features()

            # 3. 多源推理
            await self.perform_multi_source_reasoning()

            # 4. 专家介入判断
            self._check_expert_intervention()

            # 5. 生成分析报告（如果不需要专家介入）
            if not self.state.need_expert:
                await self.generate_analysis_report()

            # 6. 记录推理链路
            self._record_inference_trace()

            logger.info(f"[{self.name}] 推理分析完成 - 需要专家介入: {self.state.need_expert}")

        except Exception as e:
            logger.error(f"[{self.name}] 推理失败: {str(e)}")
            raise

        return self.state.to_dict()

    async def parse_log_and_extract_features(self):
        """步骤1: 解析日志并提取特征"""
        logger.info(f"[{self.name}] 开始日志解析和特征提取")

        # 调用日志解析Agent
        parse_result = await self.log_parser.parse(
            self.state.chip_model,
            self.state.raw_log
        )

        # 调试：查看返回结构
        logger.info(f"[{self.name}] parse_result keys: {list(parse_result.keys())}")
        logger.info(f"[{self.name}] has normalized_features: {'normalized_features' in parse_result}")
        if 'normalized_features' in parse_result:
            logger.info(f"[{self.name}] normalized_features error_codes: {parse_result['normalized_features'].get('error_codes', [])}")

        # 提取标准化特征
        self.state.fault_features = parse_result.get("normalized_features", parse_result)

        logger.info(f"[{self.name}] fault_features error_codes: {self.state.fault_features.get('error_codes', [])}")

        logger.info(f"[{self.name}] 特征提取完成: {len(self.state.fault_features.get('error_codes', []))} 个错误码")

    async def perform_multi_source_reasoning(self):
        """步骤2: 执行多源推理"""
        logger.info(f"[{self.name}] 开始多源推理")

        # 并行执行多种推理
        import asyncio

        # 芯片工具推理
        chip_tool_result = await self._reason_with_chip_tool()

        # 知识图谱推理
        kg_result = await self._reason_with_kg()

        # 案例匹配推理
        case_match_result = await self._reason_with_case_matching()

        # 存储各源结果
        self.state.delimit_results = []

        if chip_tool_result:
            self.state.delimit_results.append({
                "type": "chip_tool",
                "result": chip_tool_result
            })
        if kg_result:
            self.state.delimit_results.append({
                "type": "knowledge_graph",
                "result": kg_result
            })
        if case_match_result:
            self.state.delimit_results.append({
                "type": "case_match",
                "result": case_match_result
            })

        # 融合推理结果
        await self._fuse_reasoning_results()

    async def _reason_with_chip_tool(self) -> Dict:
        """基于规则引擎的芯片工具推理"""
        # 提取故障特征
        features = self.state.fault_features
        error_codes = features.get("error_codes", [])
        modules = features.get("modules", [])

        # 调用MCP工具（这里简化实现，实际应调用专门的芯片工具）
        result = {
            "failure_domain": "unknown",
            "failure_module": "unknown",
            "confidence": 0.0,
            "match_count": 0,
            "evidence_strength": "none"  # none, weak, medium, strong
        }

        # 如果没有错误码，返回零置信度
        if not error_codes:
            return result

        # 简单的规则匹配（实际应从数据库获取规则）
        matched_codes = []
        evidence_strength = "none"

        for code in error_codes:
            code_upper = code.upper()
            if code_upper.startswith("0X01") or code_upper.startswith("0X02"):
                result["failure_domain"] = "compute"
                result["failure_module"] = "cpu"
                matched_codes.append(code)
            elif code_upper.startswith("0X10") or code_upper.startswith("0X11"):
                result["failure_domain"] = "cache"
                result["failure_module"] = "l3_cache"
                matched_codes.append(code)
            elif code_upper.startswith("0X20") or code_upper.startswith("0X21"):
                result["failure_domain"] = "interconnect"
                result["failure_module"] = "ha"
                matched_codes.append(code)

        result["match_count"] = len(matched_codes)

        # 证据强度分级计算置信度
        if len(matched_codes) == 0:
            # 无匹配
            evidence_strength = "none"
            result["confidence"] = 0.0
        elif len(matched_codes) == 1:
            # 单个前缀匹配 - 弱证据
            evidence_strength = "weak"
            result["confidence"] = 0.15
        elif len(matched_codes) < len(error_codes):
            # 部分匹配 - 中等证据
            evidence_strength = "medium"
            match_ratio = len(matched_codes) / len(error_codes)
            result["confidence"] = round(0.25 + (match_ratio * 0.15), 4)
        else:
            # 全部匹配 - 强证据
            evidence_strength = "strong"
            result["confidence"] = 0.45

        result["evidence_strength"] = evidence_strength
        return result

    async def _reason_with_kg(self) -> Dict:
        """基于知识图谱的推理"""
        features = self.state.fault_features
        modules = features.get("modules", [])
        error_codes = features.get("error_codes", [])

        # 调用MCP知识图谱工具
        result = {
            "failure_domain": "unknown",
            "failure_module": "unknown",
            "confidence": 0.0,
            "evidence_strength": "none"
        }

        # 如果没有模块信息和错误码，返回零置信度
        if not modules and not error_codes:
            return result

        # 简单实现（实际应调用Neo4j）
        # 模拟知识图谱匹配：检查是否有足够的证据
        evidence_count = 0
        matched_module = None
        matched_domain = "unknown"

        # 检查模块匹配（模块名存在）
        for module in modules:
            if module in ["cpu", "l3_cache"]:
                matched_domain = "compute"
                matched_module = module
                evidence_count += 1
                break
            elif module in ["ha", "noc_router"]:
                matched_domain = "interconnect"
                matched_module = module
                evidence_count += 1
                break
            elif module in ["ddr_controller", "hbm_controller"]:
                matched_domain = "memory"
                matched_module = module
                evidence_count += 1
                break

        # 检查错误码是否支持模块判断
        code_supports = False
        for code in error_codes:
            code_upper = code.upper()
            if code_upper.startswith("0X") or "CPU" in code_upper or "L3" in code_upper or "DDR" in code_upper:
                code_supports = True
                evidence_count += 1
                break

        # 证据强度分级
        if not matched_module:
            # 无模块匹配
            result["evidence_strength"] = "none"
            result["confidence"] = 0.0
        elif evidence_count == 1:
            # 只有模块名，无错误码支持 - 弱证据
            result["evidence_strength"] = "weak"
            result["failure_domain"] = matched_domain
            result["failure_module"] = matched_module
            result["confidence"] = 0.1
        elif evidence_count == 2 and code_supports:
            # 模块名 + 错误码支持 - 中等证据
            result["evidence_strength"] = "medium"
            result["failure_domain"] = matched_domain
            result["failure_module"] = matched_module
            result["confidence"] = 0.35
        else:
            # 多个证据 - 强证据
            result["evidence_strength"] = "strong"
            result["failure_domain"] = matched_domain
            result["failure_module"] = matched_module
            result["confidence"] = 0.5

        return result

    async def _reason_with_case_matching(self) -> Dict:
        """基于案例匹配的推理"""
        features = self.state.fault_features
        error_codes = features.get("error_codes", [])

        # 简化实现：基于错误码的简单匹配
        result = {
            "failure_domain": "unknown",
            "failure_module": "unknown",
            "confidence": 0.0,
            "evidence_strength": "none",
            "matched_cases": []
        }

        if not error_codes:
            return result

        # 模拟案例匹配（实际应使用pgvector）
        matched_similarities = []

        for code in error_codes:
            code_upper = code.upper()
            if code_upper.startswith("0X01"):
                result["failure_domain"] = "compute"
                result["failure_module"] = "cpu"
                similarity = 0.9
                matched_similarities.append(similarity)
                result["matched_cases"].append({
                    "case_id": f"CASE_{code}",
                    "similarity": similarity
                })
            elif code_upper.startswith("0X10"):
                result["failure_domain"] = "cache"
                result["failure_module"] = "l3_cache"
                similarity = 0.88
                matched_similarities.append(similarity)
                result["matched_cases"].append({
                    "case_id": f"CASE_{code}",
                    "similarity": similarity
                })
            elif code_upper.startswith("0X20"):
                result["failure_domain"] = "interconnect"
                result["failure_module"] = "ha"
                similarity = 0.85
                matched_similarities.append(similarity)
                result["matched_cases"].append({
                    "case_id": f"CASE_{code}",
                    "similarity": similarity
                })

        # 证据强度分级
        if not matched_similarities:
            # 无匹配
            result["evidence_strength"] = "none"
            result["confidence"] = 0.0
        elif len(matched_similarities) == 1:
            # 单个案例匹配 - 弱证据
            avg_sim = sum(matched_similarities) / len(matched_similarities)
            result["evidence_strength"] = "weak"
            result["confidence"] = round(avg_sim * 0.4, 4)  # 相似度权重降低
        elif len(matched_similarities) == 2:
            # 两个案例匹配 - 中等证据
            avg_sim = sum(matched_similarities) / len(matched_similarities)
            result["evidence_strength"] = "medium"
            result["confidence"] = round(avg_sim * 0.6, 4)
        else:
            # 多个案例匹配 - 强证据
            avg_sim = sum(matched_similarities) / len(matched_similarities)
            result["evidence_strength"] = "strong"
            result["confidence"] = round(avg_sim * 0.8, 4)

        return result

    async def _fuse_reasoning_results(self):
        """融合多源推理结果"""
        logger.info(f"[{self.name}] 开始融合推理结果")

        results = self.state.delimit_results
        if not results:
            logger.warning(f"[{self.name}] 没有推理结果可融合")
            self.state.final_root_cause = {
                "module": "unknown",
                "root_cause": "无可用推理结果",
                "failure_domain": "unknown",
                "confidence": 0.0,
                "reasoning": "没有可用的推理结果"
            }
            return

        # 多源结果权重配置
        weights = {
            "chip_tool": 0.4,
            "knowledge_graph": 0.3,
            "case_match": 0.3
        }

        # 统计有效匹配源（置信度 > 0 且失效域不是unknown）
        valid_sources = []
        domain_votes = {}  # 各域的投票情况

        for result in results:
            r = result.get("result", {})
            domain = r.get("failure_domain", "unknown")
            confidence = r.get("confidence", 0.0)
            evidence_strength = r.get("evidence_strength", "none")
            source_type = result.get("type", "")

            # 只有置信度>0且域不是unknown才算有效
            if confidence > 0 and domain != "unknown":
                valid_sources.append({
                    "type": source_type,
                    "domain": domain,
                    "confidence": confidence,
                    "evidence_strength": evidence_strength
                })

                # 统计域投票
                if domain not in domain_votes:
                    domain_votes[domain] = []
                domain_votes[domain].append(source_type)

        # 如果没有有效匹配源，返回0置信度
        if not valid_sources:
            logger.warning(f"[{self.name}] 没有有效的推理结果")
            self.state.final_root_cause = {
                "module": "unknown",
                "root_cause": "无法确定故障原因",
                "failure_domain": "unknown",
                "confidence": 0.0,
                "reasoning": "所有推理源均未能匹配到有效结果"
            }
            return

        # 选择最终失效域（基于投票数和证据强度）
        final_domain = "unknown"
        max_score = -1

        for domain, voters in domain_votes.items():
            # 投票数权重（优先）
            vote_weight = len(voters) * 100

            # 计算该域的加权证据强度
            strength_score = 0
            for source in valid_sources:
                if source["domain"] == domain:
                    strength_map = {"weak": 10, "medium": 30, "strong": 50}
                    strength_score += strength_map.get(source["evidence_strength"], 0)

            # 综合得分
            score = vote_weight + strength_score
            if score > max_score:
                max_score = score
                final_domain = domain

        # 计算最终置信度 - 基于证据强度分级
        valid_count = len(valid_sources)
        total_sources = len(results)

        # 统计各源的证据强度
        strength_counts = {"weak": 0, "medium": 0, "strong": 0}
        for source in valid_sources:
            if source["domain"] == final_domain:
                strength_counts[source["evidence_strength"]] += 1

        # 基于证据强度计算基准置信度
        if strength_counts["strong"] >= 2:
            # 至少2个强证据
            base_confidence = 0.85
        elif strength_counts["strong"] >= 1 and strength_counts["medium"] >= 1:
            # 1个强证据 + 1个中等证据
            base_confidence = 0.75
        elif strength_counts["strong"] >= 1:
            # 单个强证据
            base_confidence = 0.5
        elif strength_counts["medium"] >= 2:
            # 至少2个中等证据
            base_confidence = 0.6
        elif strength_counts["medium"] >= 1:
            # 单个中等证据
            base_confidence = 0.35
        elif strength_counts["weak"] >= 2:
            # 至少2个弱证据
            base_confidence = 0.2
        elif strength_counts["weak"] >= 1:
            # 单个弱证据
            base_confidence = 0.1
        else:
            base_confidence = 0.0

        # 一致性加成：所有源都指向同一域时加成
        if valid_count == total_sources and len(domain_votes) == 1:
            base_confidence += 0.1

        # 单源惩罚：只有1个源有效时，不再额外惩罚（已经通过强度分级体现）
        # 不一致性惩罚：部分源未匹配
        if valid_count < total_sources:
            consistency_ratio = valid_count / total_sources
            base_confidence *= (0.85 + 0.15 * consistency_ratio)

        # 域冲突惩罚：如果同一个域有多个不同的模块建议
        domain_modules = {}
        for source in valid_sources:
            if source["domain"] == final_domain:
                r = next((res for res in results if res.get("type") == source["type"]), {})
                module = r.get("result", {}).get("failure_module", "unknown")
                if final_domain not in domain_modules:
                    domain_modules[final_domain] = set()
                domain_modules[final_domain].add(module)

        if len(domain_modules.get(final_domain, set())) > 1:
            base_confidence *= 0.9

        # 确保置信度在合理范围内
        final_confidence = round(max(0.0, min(base_confidence, 0.95)), 4)

        # 选择最终失效模块（选择置信度最高的源建议的模块）
        final_module = "unknown"
        max_source_confidence = 0.0

        for source in valid_sources:
            if source["domain"] == final_domain and source["confidence"] > max_source_confidence:
                r = next((res for res in results if res.get("type") == source["type"]), {})
                final_module = r.get("result", {}).get("failure_module", "unknown")
                max_source_confidence = source["confidence"]

        # 查找根因
        root_cause = await self._find_root_cause(final_domain, final_module)

        # 构建推理说明
        reasoning_parts = [
            f"有效源: {valid_count}/{total_sources}",
            f"证据强度: 弱{strength_counts['weak']} 中{strength_counts['medium']} 强{strength_counts['strong']}",
            f"域投票: {domain_votes}"
        ]

        self.state.final_root_cause = {
            "module": final_module,
            "root_cause": root_cause,
            "failure_domain": final_domain,
            "confidence": final_confidence,
            "reasoning": " | ".join(reasoning_parts)
        }

        logger.info(f"[{self.name}] 推理融合完成 - 域: {final_domain}, 置信度: {final_confidence:.2f}, 证据强度: {strength_counts}")

    async def _find_root_cause(self, domain: str, module: str) -> str:
        """查找根因"""
        # 简化实现（实际应查询知识图谱）
        root_causes = {
            "compute": {
                "cpu": "CPU核心运算错误",
                "l3_cache": "L3缓存一致性错误",
                "other": "计算单元未知故障"
            },
            "cache": {
                "l3_cache": "L3缓存数据错误",
                "l2_cache": "L2缓存错误",
                "other": "缓存未知故障"
            },
            "interconnect": {
                "ha": "Home Agent一致性错误",
                "noc": "NoC路由错误",
                "other": "互连未知故障"
            },
            "memory": {
                "ddr": "DDR控制器错误",
                "hbm": "HBM控制器错误",
                "other": "内存未知故障"
            },
            "unknown": {
                "other": "未知类型故障"
            }
        }

        if domain in root_causes:
            if module in root_causes[domain]:
                return root_causes[domain][module]
            return root_causes[domain].get("other", "未知故障")

        return "未知类型故障"

    def _check_expert_intervention(self):
        """检查是否需要专家介入"""
        threshold = self.state.infer_threshold
        confidence = self.state.final_root_cause.get("confidence", 0.0)

        self.state.need_expert = confidence < threshold

        if self.state.need_expert:
            logger.warning(f"[{self.name}] 置信度 {confidence:.2f} < 阈值 {threshold} - 需要专家介入")

    async def generate_analysis_report(self):
        """生成分析报告 - 优先使用LLM，降级到模板"""
        logger.info(f"[{self.name}] 开始生成分析报告")

        # 准备报告数据
        from datetime import datetime
        report_data = {
            "analysis_id": self.state.session_id or "UNKNOWN",
            "chip_model": self.state.chip_model,
            "created_at": datetime.now().isoformat(),
            "fault_features": self.state.fault_features or {},
            "final_root_cause": self.state.final_root_cause or {},
            "delimit_results": self.state.delimit_results or [],
            "confidence": (self.state.final_root_cause or {}).get("confidence", 0.0)
        }

        # 首先尝试使用LLM生成报告
        logger.info(f"[{self.name}] 尝试使用LLM生成��告...")
        llm_report, token_info = await self._generate_llm_report(report_data)

        if llm_report:
            self.state.infer_report = llm_report
            self.state.report_type = "llm"
            # 保存token消耗信息
            if token_info:
                self.state.tokens_used = token_info.get("total_tokens", 0)
                self.state.token_usage = token_info
            logger.info(f"[{self.name}] LLM报告生成成功")
        else:
            # LLM失败，降级到模板生成
            logger.warning(f"[{self.name}] LLM报告生成失败，降级到模板生成")
            report_result = await self.report_generator.generate(
                self.state.session_id or "UNKNOWN",
                report_data,
                "html"
            )

            if report_result.get("success"):
                self.state.infer_report = report_result.get("report_path", "")
                self.state.report_type = "template"
            else:
                self.state.infer_report = "报告生成失败: " + report_result.get("error", "未知错误")
                self.state.report_type = "error"

        logger.info(f"[{self.name}] 报告生成完成 - 类型: {getattr(self.state, 'report_type', 'unknown')}")

    async def _generate_llm_report(self, report_data: dict) -> tuple[str | None, dict | None]:
        """
        使用LLM生成分析报告

        Returns:
            (报告内容, token使用信息) 元组
        """
        try:
            from src.config.settings import get_settings
            from src.mcp.tools.llm_tool import LLMTool

            settings = get_settings()

            # 检查是否配置了LLM API密钥
            if not settings.ANTHROPIC_API_KEY and not settings.OPENAI_API_KEY:
                logger.warning(f"[{self.name}] 未配置LLM API密钥")
                return None

            llm_tool = LLMTool()

            # 构建提示词
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
                    "content": self._build_llm_prompt(report_data)
                }
            ]

            # 确定使用的模型
            model = "glm-4.7" if settings.ANTHROPIC_API_KEY else "gpt-4"

            # 调用LLM
            logger.info(f"[{self.name}] 调用LLM生成报告 - 模型: {model}")
            result = await llm_tool.chat(messages, model=model, temperature=0.7, max_tokens=4000)

            if result.get("success"):
                content = result.get("content")
                token_info = result.get("usage", {})
                logger.info(f"[{self.name}] LLM报告生成成功 - Token消耗: {token_info.get('total_tokens', 0)}")
                return content, token_info
            else:
                logger.warning(f"[{self.name}] LLM调用失败: {result.get('error')}")
                return None, None

        except Exception as e:
            logger.error(f"[{self.name}] LLM报告生成异常: {str(e)}")
            return None, None

    def _build_llm_prompt(self, report_data: dict) -> str:
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

    def _record_inference_trace(self):
        """记录推理链路"""
        from datetime import datetime

        self.state.infer_trace = [
            {
                "step": "log_parsing",
                "description": "日志解析与特征提取",
                "timestamp": datetime.now().isoformat(),
                "result": {
                    "error_codes_count": len(self.state.fault_features.get("error_codes", [])),
                    "modules_count": len(self.state.fault_features.get("modules", []))
                }
            },
            {
                "step": "multi_source_reasoning",
                "description": "多源融合推理",
                "timestamp": datetime.now().isoformat(),
                "result": {
                    "sources_count": len(self.state.delimit_results),
                    "final_domain": self.state.final_root_cause.get("failure_domain"),
                    "final_module": self.state.final_root_cause.get("module"),
                    "confidence": self.state.final_root_cause.get("confidence")
                }
            },
            {
                "step": "expert_intervention_check",
                "description": "专家介入判断",
                "timestamp": datetime.now().isoformat(),
                "result": {
                    "need_expert": self.state.need_expert,
                    "confidence": self.state.final_root_cause.get("confidence", 0),
                    "threshold": self.state.infer_threshold
                }
            }
        ]

        if self.state.infer_report:
            self.state.infer_trace.append({
                "step": "report_generation",
                "description": "分析报告生成",
                "timestamp": datetime.now().isoformat(),
                "result": {
                    "report_length": len(self.state.infer_report)
                }
            })


# ============================================
# Agent1的各个子组件导入
# ============================================
from .log_parser import LogParserAgent
from .reasoning import ReasoningAgent
from .report_generator import ReportGenerator
