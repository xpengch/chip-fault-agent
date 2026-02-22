"""
芯片失效分析AI Agent系统 - LLM工具
支持OpenAI和Anthropic Claude API
"""

from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import anthropic
from loguru import logger
import json


class LLMTool:
    """大语言模型工具类"""

    def __init__(self):
        """初始化LLM工具"""
        self.name = "LLMTool"
        self.description = "调用大语言模型进行对话和文本生成"

        # 初始化客户端（懒加载）
        self._openai_client: Optional[AsyncOpenAI] = None
        self._anthropic_client: Optional[anthropic.AsyncAnthropic] = None

    def _get_openai_client(self) -> AsyncOpenAI:
        """获取OpenAI客户端"""
        from src.config.settings import get_settings
        settings = get_settings()

        if self._openai_client is None and settings.OPENAI_API_KEY:
            self._openai_client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
        return self._openai_client

    def _get_anthropic_client(self) -> Optional[anthropic.AsyncAnthropic]:
        """获取Anthropic客户端"""
        from src.config.settings import get_settings
        settings = get_settings()

        if self._anthropic_client is None and settings.ANTHROPIC_API_KEY:
            self._anthropic_client = anthropic.AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                base_url=settings.ANTHROPIC_BASE_URL
            )
        return self._anthropic_client

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        LLM对话

        Args:
            messages: 对话消息列表
                [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            model: 使用的模型（gpt-4/claude-3-opus/glm-4.7）
            temperature: 温度参数（0-1）
            max_tokens: 最大token数

        Returns:
            LLM响应结果
        """
        logger.info(f"[{self.name}] LLM对话 - 模型: {model}")

        try:
            # 根据模型选择客户端
            if model.startswith("gpt"):
                response = await self._chat_openai(messages, model, temperature, max_tokens)
            elif model.startswith("claude") or model.startswith("glm"):
                # glm系列模型使用Anthropic兼容API
                response = await self._chat_anthropic(messages, model, temperature, max_tokens)
            else:
                raise ValueError(f"Unsupported model: {model}")

            logger.info(f"[{self.name}] LLM对话完成 - 消耗tokens: {response.get('usage', {}).get('total_tokens', 0)}")

            return response

        except Exception as e:
            logger.error(f"[{self.name}] LLM对话失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": "LLM调用失败，请检查配置和API密钥"
            }

    async def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """OpenAI对话"""
        client = self._get_openai_client()
        if not client:
            raise ValueError("OpenAI API key not configured")

        # 转换消息格式
        openai_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in messages
                ]

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return {
                "success": True,
                "model": model,
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] OpenAI调用失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _chat_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Anthropic对话"""
        client = self._get_anthropic_client()
        if not client:
            raise ValueError("Anthropic API key not configured")

        try:
            # 转换消息格式为Anthropic格式
            anthropic_messages = []
            system_message = None
            for m in messages:
                if m["role"] == "system":
                    system_message = m["content"]
                elif m["role"] == "user":
                    anthropic_messages.append({"role": "user", "content": m["content"]})
                elif m["role"] == "assistant":
                    anthropic_messages.append({"role": "assistant", "content": m["content"]})

            # 调用Anthropic API
            if system_message:
                response = await client.messages.create(
                    model=model,
                    system=system_message,
                    messages=anthropic_messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                response = await client.messages.create(
                    model=model,
                    messages=anthropic_messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

            return {
                "success": True,
                "model": model,
                "content": response.content[0].text,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }

        except Exception as e:
            logger.error(f"[{self.name}] Anthropic调用失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_analysis_report(
        self,
        analysis_data: Dict[str, Any],
        model: str = "claude-3-opus"
    ) -> str:
        """
        生成分析报告

        Args:
            analysis_data: 分析数据
            model: 使用的模型

        Returns:
            生成的报告文本
        """
        logger.info(f"[{self.name}] 生成分析报告 - 模型: {model}")

        # 构建提示词
        prompt = self._build_report_prompt(analysis_data)

        messages = [
            {"role": "system", "content": "你是一位专业的芯片失效分析专家，擅长编写清晰、准确的分析报告。"},
            {"role": "user", "content": prompt}
        ]

        # 调用LLM
        result = await self.chat(messages, model=model)

        if not result.get("success", False):
            # 返回基础格式
            return self._generate_fallback_report(analysis_data)

        return result["content"]

    def _build_report_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """构建报告生成提示词"""

        features = analysis_data.get("fault_features", {})
        reasoning = analysis_data.get("reasoning_result", {})

        return f"""请基于以下芯片失效分析数据，生成一份专业的分析报告。

## 分析信息
- 分析ID: {analysis_data.get('analysis_id', 'N/A')}
- 芯片型号: {analysis_data.get('chip_model', 'N/A')}
- 分析时间: {analysis_data.get('analysis_timestamp', 'N/A')}

## 故障特征
- 错误码: {', '.join(features.get('error_codes', []))}
- 故障描述: {features.get('fault_description', 'N/A')}
- 时间戳: {features.get('timestamp', 'N/A')}
- 模块: {', '.join(features.get('modules', []))}
- 失效域: {features.get('failure_domain', 'Unknown')}

## 推理结果
- 失效域: {reasoning.get('failure_domain', 'Unknown')}
- 根本原因: {reasoning.get('root_cause', 'Unknown')}
- 根因分类: {reasoning.get('root_cause_category', 'Unknown')}
- 置信度: {reasoning.get('confidence', 0):.0%}

## 推理过程
{self._format_reasoning_process(reasoning.get('reasoning_sources', {}))}

## 相似案例
{self._format_similar_cases(analysis_data.get('similar_cases', []))}

请生成结构清晰、易于理解的分析报告，使用Markdown格式，包含以上所有信息。
"""

    def _format_reasoning_process(self, sources: Dict[str, Any]) -> str:
        """格式化推理过程"""

        process = []

        if sources.get("chip_tool", {}).get("used"):
            tool_result = sources["chip_tool"]["result"]
            process += f"1. 芯片工具推理：{tool_result.get('failure_domain', '未知域')}\n"
            for reason in tool_result.get("reasoning", []):
                process += f"   - {reason}\n"

        if sources.get("knowledge_graph", {}).get("used"):
            kg_result = sources["knowledge_graph"]["result"]
            process += f"2. 知识图谱推理：{kg_result.get('failure_domain', '未知域')}\n"
            for reason in kg_result.get("reasoning", []):
                process += f"   - {reason}\n"

        if sources.get("case_match", {}).get("used"):
            case_result = sources["case_match"]["result"]
            similarity = case_result.get("similarity", 0.0)
            process += f"3. 历史案例匹配：相似度 {similarity:.2f}\n"
            if case_result.get("root_cause"):
                process += f"   - 匹配案例根因：{case_result['root_cause']}\n"

        return process or "推理过程数据不可用"

    def _format_similar_cases(self, cases: List[Dict]) -> str:
        """格式化相似案例"""

        if not cases:
            return "未找到相似案例"

        formatted = ""
        for i, case in enumerate(cases[:5], 1):  # 最多显示5个
            formatted += f"{i}. 案例ID: {case.get('case_id', 'N/A')}\n"
            formatted += f"   相似度: {case.get('similarity', 0):.2f}\n"
            formatted += f"   失效域: {case.get('failure_domain', 'Unknown')}\n"
            formatted += f"   根因: {case.get('root_cause', 'N/A')}\n"
            if case.get("solution"):
                formatted += f"   解决方案: {case['solution']}\n"
            formatted += "\n"

        return formatted

    def _generate_fallback_report(self, analysis_data: Dict[str, Any]) -> str:
        """生成备用基础报告"""

        return f"""
# 芯片失效分析报告

## 基本信息
- 分析ID: {analysis_data.get('analysis_id', 'N/A')}
- 芯片型号: {analysis_data.get('chip_model', 'N/A')}
- 分析时间: {analysis_data.get('analysis_timestamp', 'N/A')}

## 故障特征
- 错误码: {', '.join(analysis_data.get('fault_features', {}).get('error_codes', []))}
- 故障描述: {analysis_data.get('fault_features', {}).get('fault_description', 'N/A')}

## 推理结果
- 失效域: {analysis_data.get('reasoning_result', {}).get('failure_domain', 'Unknown')}
- 根本原因: {analysis_data.get('reasoning_result', {}).get('root_cause', 'Unknown')}
- 置信度: {analysis_data.get('reasoning_result', {}).get('confidence', 0):.0%}

## 说明
由于LLM服务不可用，显示基础分析结果。请检查API配置。

---
系统版本: 1.0.0
生成时间: {analysis_data.get('analysis_timestamp', 'N/A')}
"""
