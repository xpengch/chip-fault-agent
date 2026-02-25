"""
Agent1 - 多源推理Agent
负责：
1. 调用多种MCP工具进行推理
2. 融合多源推理结果
3. 计算最终置信度
4. 判断是否需要专家介入
"""

from typing import Dict, List, Any, Optional
from langchain.tools import tool
from loguru import logger


class ReasoningAgent:
    """多源推理Agent类"""

    def __init__(self, default_threshold: float = 0.7):
        """初始化Agent

        Args:
            default_threshold: 默认专家介入阈值
        """
        self.name = "ReasoningAgent"
        self.description = "多源融合推理，判断失效域和根因"
        self.default_threshold = default_threshold

        # 多源结果权重配置
        self.weights = {
            "chip_tool": 0.4,
            "knowledge_graph": 0.3,
            "case_match": 0.3
        }

    @tool
    async def multi_source_reasoning(
        self,
        chip_model: str,
        fault_features: Dict[str, Any],
        infer_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        执行多源融合推理

        Args:
            chip_model: 芯片型号
            fault_features: 标准化故障特征
            infer_threshold: 专家介入阈值（覆盖默认值）

        Returns:
            推理结果字典
        """
        threshold = infer_threshold or self.default_threshold
        logger.info(f"[{self.name}] 开始多源推理 - 芯片: {chip_model}, 阈值: {threshold}")

        try:
            # 并行调用多源推理工具
            import asyncio
            results = await asyncio.gather(
                self._chip_tool_reasoning(chip_model, fault_features),
                self._knowledge_graph_reasoning(chip_model, fault_features),
                self._case_matching_reasoning(chip_model, fault_features),
                return_exceptions=True
            )

            # 解析各源结果
            tool_result, kg_result, case_result = results
            chip_tool_reasoning = tool_result.get("result", {})
            kg_reasoning = kg_result.get("result", {})
            case_match_result = case_result.get("result", {})

            # 融合多源结果
            fused_result = self._fuse_results({
                "chip_tool": chip_tool_reasoning,
                "knowledge_graph": kg_reasoning,
                "case_match": case_match_result
            }, fault_features)

            # 计算最终置信度
            final_confidence = self._calculate_confidence(fused_result)

            # 判断是否需要专家介入
            need_expert = final_confidence < threshold

            # 构建返回结果
            result = {
                "success": True,
                "agent": self.name,
                "chip_model": chip_model,
                "fault_features": fault_features,
                "reasoning_sources": {
                    "chip_tool": chip_tool_reasoning,
                    "knowledge_graph": kg_reasoning,
                    "case_match": case_match_result
                },
                "fused_result": fused_result,
                "final_confidence": final_confidence,
                "need_expert": need_expert,
                "infer_threshold": threshold
            }

            logger.info(f"[{self.name}] 推理完成 - 置信度: {final_confidence:.3f}, 需专家: {need_expert}")

            return result

        except Exception as e:
            logger.error(f"[{self.name}] 推理失败: {str(e)}")
            return {
                "success": False,
                "agent": self.name,
                "error": str(e),
                "chip_model": chip_model
            }

    async def _chip_tool_reasoning(
        self,
        chip_model: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于规则引擎的芯片工具推理"""
        logger.info("[ReasoningAgent] 执行芯片工具推理")

        # 推断失效域
        failure_domain = features.get("failure_domain", "unknown")
        error_codes = features.get("error_codes", [])

        # 基于错误码的详细推理
        reasoning_details = []
        for code in error_codes:
            if code.startswith("0XCO") or "CPU" in code:
                failure_domain = "compute"
                reasoning_details.append(f"错误码 {code} 指示CPU核心失效")
            elif code.startswith("0XLA") or "L3" in code:
                failure_domain = "cache"
                reasoning_details.append(f"错误码 {code} 指示L3缓存失效")
            elif code.startswith("0XHA") or "HA" in code:
                failure_domain = "interconnect"
                reasoning_details.append(f"错误码 {code} 指示一致性代理失效")
            elif code.startswith("0XME") or "DDR" in code:
                failure_domain = "memory"
                reasoning_details.append(f"错误码 {code} 指示DDR控制器失效")

        # 证据强度分级计算置信度
        error_codes = features.get("error_codes", [])
        evidence_strength = "none"

        if not reasoning_details:
            confidence = 0.0
            evidence_strength = "none"
        elif len(reasoning_details) == 1:
            # 单个前缀匹配 - 弱证据
            confidence = 0.15
            evidence_strength = "weak"
        elif len(reasoning_details) < len(error_codes):
            # 部分匹配 - 中等证据
            match_ratio = len(reasoning_details) / max(len(error_codes), 1)
            confidence = round(0.25 + (match_ratio * 0.15), 4)
            evidence_strength = "medium"
        else:
            # 全部匹配 - 强证据
            confidence = 0.45
            evidence_strength = "strong"

        return {
            "source": "chip_tool",
            "result": {
                "failure_domain": failure_domain,
                "possible_modules": features.get("modules", []),
                "reasoning": reasoning_details,
                "evidence_strength": evidence_strength
            },
            "confidence": confidence
        }

    async def _knowledge_graph_reasoning(
        self,
        chip_model: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于知识图谱的推理"""
        logger.info("[ReasoningAgent] 执行知识图谱推理")

        try:
            from src.mcp.server import get_mcp_server
            mcp_server = get_mcp_server()

            # 调用知识图谱查询工具
            error_codes = features.get("error_codes", [])
            modules = features.get("modules", [])
            fault_description = features.get("fault_description", "")

            # 查询失效模式
            kg_result = await mcp_server.call_tool(
                "kg_query",
                {
                    "query_type": "failure_modes",
                    "chip_model": chip_model,
                    "module_type": modules[0] if modules else None,
                    "failure_mode": fault_description
                }
            )

            import json
            parsed_result = json.loads(kg_result[0].text)

            # 解析结果
            failure_modes = parsed_result.get("failure_modes", [])
            root_causes = parsed_result.get("root_causes", [])

            if not failure_modes:
                return {
                    "source": "knowledge_graph",
                    "result": {
                        "failure_domain": "unknown",
                        "reasoning": ["知识图谱中未找到匹配的失效模式"],
                        "evidence_strength": "none"
                    },
                    "confidence": 0.0
                }

            # 获取最相关的失效模式
            primary_mode = failure_modes[0]

            # 根据匹配质量评估证据强度
            mode_confidence = primary_mode.get("confidence", 0.0)
            if mode_confidence >= 0.8:
                evidence_strength = "strong"
                confidence = 0.5
            elif mode_confidence >= 0.6:
                evidence_strength = "medium"
                confidence = 0.35
            else:
                evidence_strength = "weak"
                confidence = 0.15

            return {
                "source": "knowledge_graph",
                "result": {
                    "failure_domain": primary_mode.get("category", "unknown"),
                    "failure_mode": primary_mode.get("name", ""),
                    "root_causes": root_causes,
                    "reasoning": [f"知识图谱匹配到失效模式: {primary_mode.get('name')}"],
                    "evidence_strength": evidence_strength
                },
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"[ReasoningAgent] 知识图谱推理失败: {str(e)}")
            return {
                "source": "knowledge_graph",
                "result": {
                    "failure_domain": "unknown",
                    "reasoning": [f"知识图谱查询异常: {str(e)}"],
                    "evidence_strength": "none"
                },
                "confidence": 0.0
            }

    async def _case_matching_reasoning(
        self,
        chip_model: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于历史案例的推理"""
        logger.info("[ReasoningAgent] 执行案例匹配推理")

        try:
            from src.mcp.server import get_mcp_server
            mcp_server = get_mcp_server()

            # 生成特征向量（使用真实embedding模型）
            feature_vector = await self._generate_feature_vector(features)

            # 调用pgvector搜索工具
            search_result = await mcp_server.call_tool(
                "pgvector_search",
                {
                    "feature_vector": feature_vector,
                    "chip_model": chip_model,
                    "top_k": 5,
                    "threshold": 0.6
                }
            )

            import json
            parsed_result = json.loads(search_result[0].text)
            similar_cases = parsed_result.get("results", [])

            if not similar_cases:
                return {
                    "source": "case_match",
                    "result": {
                        "failure_domain": "unknown",
                        "reasoning": ["未找到相似的历史案例"],
                        "evidence_strength": "none"
                    },
                    "confidence": 0.0
                }

            # 计算证据强度
            case_count = len(similar_cases)
            avg_similarity = sum(c.get("similarity", 0.0) for c in similar_cases) / case_count

            # 证据强度分级
            if case_count >= 3 and avg_similarity >= 0.85:
                evidence_strength = "strong"
                confidence = round(avg_similarity * 0.8, 4)
            elif case_count >= 2 and avg_similarity >= 0.8:
                evidence_strength = "medium"
                confidence = round(avg_similarity * 0.6, 4)
            elif case_count >= 1:
                if avg_similarity >= 0.85:
                    evidence_strength = "medium"
                    confidence = round(avg_similarity * 0.5, 4)
                else:
                    evidence_strength = "weak"
                    confidence = round(avg_similarity * 0.3, 4)
            else:
                evidence_strength = "none"
                confidence = 0.0

            top_case = similar_cases[0]

            return {
                "source": "case_match",
                "result": {
                    "failure_domain": top_case.get("failure_domain", "unknown"),
                    "matched_case_id": top_case.get("case_id"),
                    "similarity": avg_similarity,
                    "match_count": case_count,
                    "root_cause": top_case.get("root_cause"),
                    "solution": top_case.get("solution"),
                    "reasoning": [f"匹配到{case_count}个相似案例 (平均相似度: {avg_similarity:.2f})"],
                    "evidence_strength": evidence_strength
                },
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"[ReasoningAgent] 案例匹配失败: {str(e)}")
            return {
                "source": "case_match",
                "result": {
                    "failure_domain": "unknown",
                    "reasoning": [f"案例匹配异常: {str(e)}"],
                    "evidence_strength": "none"
                },
                "confidence": 0.0
            }

    def _fuse_results(
        self,
        source_results: Dict[str, Dict],
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """融合多源推理结果"""

        # 提取各源结果
        chip_tool = source_results.get("chip_tool", {})
        kg_result = source_results.get("knowledge_graph", {})
        case_result = source_results.get("case_match", {})

        # 收集各源的置信度
        confidences = {
            "chip_tool": chip_tool.get("confidence", 0.0),
            "knowledge_graph": kg_result.get("confidence", 0.0),
            "case_match": case_result.get("confidence", 0.0)
        }

        # 检查结果冲突
        max_confidence = max(confidences.values())
        min_confidence = min([c for c in confidences.values() if c > 0])
        has_conflict = (max_confidence - min_confidence) < 0.1

        # 确定最终失效域
        failure_domains = []
        for source, result in source_results.items():
            if "result" in result and "failure_domain" in result["result"]:
                fd = result["result"]["failure_domain"]
                if fd and fd != "unknown":
                    failure_domains.append((source, fd, confidences[source]))

        # 投票选择（考虑权重）
        final_domain = self._select_final_domain(failure_domains, source_results, features)

        # 构建推理链路
        reasoning_trace = []
        for source, result in source_results.items():
            if "result" in result and "reasoning" in result["result"]:
                for reason in result["result"]["reasoning"]:
                    reasoning_trace.append(f"[{source}] {reason}")

        return {
            "final_domain": final_domain,
            "has_conflict": has_conflict,
            "confidence_scores": confidences,
            "reasoning_trace": reasoning_trace
        }

    def _select_final_domain(
        self,
        domains: List[tuple],
        source_results: Dict[str, Dict],
        features: Dict[str, Any]
    ) -> str:
        """选择最终失效域"""

        # 计算加权得分
        weighted_scores = {}
        for source, domain, conf in domains:
            weight = self.weights.get(source, 0.3)
            weighted_scores[source] = conf * weight

        # 选择得分最高的
        final_source = max(weighted_scores, key=weighted_scores.get)
        final_domain = domains[0][1]  # (source, domain, conf)

        # 验证合理性
        if final_domain == "unknown":
            # 尝试从特征中推断
            inferred = features.get("failure_domain", "unknown")
            if inferred != "unknown":
                final_domain = inferred

        return final_domain

    def _calculate_confidence(self, fused_result: Dict) -> float:
        """计算最终置信度 - 基于证据强度分级"""

        confidence_scores = fused_result.get("confidence_scores", {})
        has_conflict = fused_result.get("has_conflict", False)

        # 统计有效源（置信度 > 0）
        valid_scores = {s: c for s, c in confidence_scores.items() if c > 0}
        valid_count = len(valid_scores)
        total_count = len(confidence_scores)

        # 如果没有有效源，返回0
        if valid_count == 0:
            return 0.0

        # 基于置信度分布判断证据强度
        strong_count = sum(1 for c in valid_scores.values() if c >= 0.4)
        medium_count = sum(1 for c in valid_scores.values() if 0.2 <= c < 0.4)
        weak_count = sum(1 for c in valid_scores.values() if c < 0.2)

        # 证据强度分级计算基准置信度
        if strong_count >= 2:
            # 至少2个强证据
            base_confidence = 0.85
        elif strong_count >= 1 and medium_count >= 1:
            # 1个强证据 + 1个中等证据
            base_confidence = 0.75
        elif strong_count >= 1:
            # 单个强证据
            base_confidence = 0.5
        elif medium_count >= 2:
            # 至少2个中等证据
            base_confidence = 0.6
        elif medium_count >= 1:
            # 单个中等证据
            base_confidence = 0.35
        elif weak_count >= 2:
            # 至少2个弱证据
            base_confidence = 0.2
        elif weak_count >= 1:
            # 单个弱证据
            base_confidence = 0.1
        else:
            base_confidence = 0.0

        # 冲突惩罚
        if has_conflict:
            base_confidence *= 0.7

        # 一致性惩罚：部分源未匹配
        if valid_count < total_count:
            consistency_ratio = valid_count / total_count
            base_confidence *= (0.85 + 0.15 * consistency_ratio)

        # 确保置信度在合理范围内
        return round(max(0.0, min(base_confidence, 0.95)), 4)

    async def _generate_feature_vector(self, features: Dict[str, Any]) -> List[float]:
        """生成特征向量（使用真实embedding）"""
        from src.mcp.tools.llm_tool import LLMTool

        # 构建用于embedding的文本描述
        text_parts = []

        # 添加错误码
        error_codes = features.get("error_codes", [])
        if error_codes:
            text_parts.append(f"错误码: {', '.join(error_codes)}")

        # 添加模块信息
        modules = features.get("modules", [])
        if modules:
            text_parts.append(f"相关模块: {', '.join(modules)}")

        # 添加故障描述
        fault_desc = features.get("fault_description", "")
        if fault_desc:
            text_parts.append(f"故障描述: {fault_desc}")

        # 添加原始日志（截断）
        raw_log = features.get("raw_log", "")
        if raw_log:
            text_parts.append(f"日志: {raw_log[:1000]}")  # 限制长度

        # 组合成完整的文本
        feature_text = "\n".join(text_parts) if text_parts else "未知故障"

        logger.info(f"[ReasoningAgent] 生成特征向量 - 文本长度: {len(feature_text)}")

        try:
            # 使用LLMTool生成embedding
            llm_tool = LLMTool()
            embedding = await llm_tool.generate_embedding(feature_text)
            logger.info(f"[ReasoningAgent] 特征向量生成成功 - 维度: {len(embedding)}")
            return embedding
        except Exception as e:
            # 发送告警并重新抛出异常
            from src.monitoring import get_alert_manager, AlertSeverity, AlertType
            alert_manager = get_alert_manager()
            await alert_manager.send_alert(
                alert_type=AlertType.VECTOR_SEARCH_FAILED,
                severity=AlertSeverity.ERROR,
                title="特征向量生成失败",
                message=f"无法为故障特征生成语义向量: {str(e)}",
                details={
                    "feature_text_length": len(feature_text),
                    "error": str(e),
                    "impact": "案例匹配功能将不可用"
                }
            )
            raise RuntimeError(f"特征向量生成失败: {str(e)}")
