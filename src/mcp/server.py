"""
芯片失效分析AI Agent系统 - MCP服务器
基于Anthropic MCP协议实现标准化工具调用
"""

from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import json


class ChipFaultMCPServer:
    """芯片失效分析MCP服务器"""

    def __init__(self):
        """初始化MCP服务器"""
        self.server = Server("chip-fault-tools")
        self._register_tools()

    def _register_tools(self):
        """注册所有MCP工具"""

        # ========================================
        # 日志解析工具
        # ========================================
        self.server.add_tool(Tool(
            name="chip_log_parser",
            description="""
                解析芯片故障日志，提取标准化故障特征

                支持格式：JSON、CSV、纯文本日志
                提取信息：错误码、寄存器状态、故障描述、时间戳等

                输出：标准化的故障特征JSON
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "chip_model": {
                        "type": "string",
                        "description": "芯片型号（如：SoC-2024）"
                    },
                    "raw_log": {
                        "type": "string",
                        "description": "原始故障日志内容"
                    },
                    "log_format": {
                        "type": "string",
                        "enum": ["json", "csv", "text", "auto"],
                        "description": "日志格式，auto表示自动检测"
                    }
                },
                "required": ["chip_model", "raw_log"]
            }
        ))

        # ========================================
        # 知识图谱查询工具
        # ========================================
        self.server.add_tool(Tool(
            name="kg_query",
            description="""
                查询知识图谱，获取芯片结构、失效模式、根因等信息

                支持查询：
                - 芯片结构（子系统、模块关系）
                - 失效模式（模块可能失效方式）
                - 根因推理（失效原因及解决方案）
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["chip_structure", "failure_modes", "root_causes", "module_info"],
                        "description": "查询类型"
                    },
                    "chip_model": {
                        "type": "string",
                        "description": "芯片型号"
                    },
                    "module_type": {
                        "type": "string",
                        "enum": ["cpu", "l3_cache", "ha", "noc_router", "ddr_controller", "hbm_controller"],
                        "description": "模块类型"
                    },
                    "module_name": {
                        "type": "string",
                        "description": "模块名称"
                    },
                    "failure_mode": {
                        "type": "string",
                        "description": "失效模式"
                    }
                },
                "required": ["query_type", "chip_model"]
            }
        ))

        # ========================================
        # PostgreSQL数据库操作工具
        # ========================================
        self.server.add_tool(Tool(
            name="pg_store",
            description="""
                存储分析结果到PostgreSQL数据库

                存储：
                - 分析结果（故障特征、推理结果）
                - 特征向量（用于相似案例匹配）
                - 推理链路（可追溯）
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "enum": ["analysis_results", "failure_cases", "inference_rules"],
                        "description": "目标表名"
                    },
                    "data": {
                        "type": "object",
                        "description": "要存储的数据（JSON对象）"
                    }
                },
                "required": ["table_name", "data"]
            }
        ))

        self.server.add_tool(Tool(
            name="pg_query",
            description="""
                从PostgreSQL数据库查询历史数据

                支持查询：
                - 历史分析结果
                - 失效案例库
                - 推理规则
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "查询表名"
                    },
                    "filters": {
                        "type": "object",
                        "description": "过滤条件（JSON对象）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制",
                        "default": 10
                    }
                },
                "required": ["table_name"]
            }
        ))

        self.server.add_tool(Tool(
            name="pgvector_search",
            description="""
                使用pgvector进行向量相似度搜索

                基于故障特征向量，从案例库中查找相似历史案例

                返回：最相似的K个案例及相似度分数
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_vector": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "特征向量"
                    },
                    "chip_model": {
                        "type": "string",
                        "description": "芯片型号"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回Top-K结果",
                        "default": 5
                    },
                    "threshold": {
                        "type": "number",
                        "description": "相似度阈值（0-1）",
                        "default": 0.7
                    }
                },
                "required": ["feature_vector", "chip_model"]
            }
        ))

        # ========================================
        # 通用工具
        # ========================================
        self.server.add_tool(Tool(
            name="llm_chat",
            description="""
                调用大语言模型进行对话

                用途：
                - 分析报告生成
                - 推理结果解释
                - 边缘案例特征补全

                支持的模型：
                - gpt-4: OpenAI GPT-4
                - claude-3-opus: Anthropic Claude 3 Opus
                - glm-4.7: 智谱GLM-4系列
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "description": "对话消息列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                                "content": {"type": "string"}
                            },
                            "required": ["role", "content"]
                        }
                    },
                    "model": {
                        "type": "string",
                        "description": "使用的模型",
                        "enum": ["gpt-4", "gpt-4-turbo", "claude-3-opus", "claude-3-sonnet", "glm-4.7", "glm-4"],
                        "default": "gpt-4"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "温度参数（0-1）",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.7
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "最大token数",
                        "default": 4000
                    }
                },
                "required": ["messages"]
            }
        ))

        self.server.add_tool(Tool(
            name="report_generate",
            description="""
                生成分析报告（HTML格式）

                生成内容：
                - 故障特征分析
                - 推理结果展示
                - 相似案例参考
                - 解决方案建议
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis_id": {
                        "type": "string",
                        "description": "分析ID"
                    },
                    "report_type": {
                        "type": "string",
                        "enum": ["html", "pdf"],
                        "description": "报告类型"
                    },
                    "template": {
                        "type": "string",
                        "description": "报告模板名称"
                    }
                },
                "required": ["analysis_id"]
            }
        ))

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """调用MCP工具"""

        try:
            # 路由到具体的工具实现
            if tool_name == "chip_log_parser":
                return await self._chip_log_parser(**arguments)
            elif tool_name == "kg_query":
                return await self._kg_query(**arguments)
            elif tool_name == "pg_store":
                return await self._pg_store(**arguments)
            elif tool_name == "pg_query":
                return await self._pg_query(**arguments)
            elif tool_name == "pgvector_search":
                return await self._pgvector_search(**arguments)
            elif tool_name == "llm_chat":
                return await self._llm_chat(**arguments)
            elif tool_name == "report_generate":
                return await self._report_generate(**arguments)
            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {tool_name}"
                )]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error executing {tool_name}: {str(e)}"
            )]

    # ========================================
    # 工具实现方法
    # ========================================

    async def _chip_log_parser(
        self,
        chip_model: str,
        raw_log: str,
        log_format: str = "auto"
    ) -> List[TextContent]:
        """日志解析工具实现"""
        from src.mcp.tools.log_parser import LogParserTool
        tool = LogParserTool()
        result = await tool.parse(chip_model, raw_log, log_format)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    async def _kg_query(
        self,
        query_type: str,
        chip_model: str,
        **kwargs
    ) -> List[TextContent]:
        """知识图谱查询工具实现"""
        from src.mcp.tools.knowledge_graph import KnowledgeGraphTool
        tool = KnowledgeGraphTool()
        result = await tool.query(query_type, chip_model, **kwargs)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    async def _pg_store(
        self,
        table_name: str,
        data: Dict
    ) -> List[TextContent]:
        """PostgreSQL存储工具实现"""
        from src.mcp.tools.database_tools import DatabaseTool
        tool = DatabaseTool()
        result = await tool.store(table_name, data)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    async def _pg_query(
        self,
        table_name: str,
        filters: Optional[Dict] = None,
        limit: int = 10
    ) -> List[TextContent]:
        """PostgreSQL查询工具实现"""
        from src.mcp.tools.database_tools import DatabaseTool
        tool = DatabaseTool()
        result = await tool.query(table_name, filters, limit)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    async def _pgvector_search(
        self,
        feature_vector: List[float],
        chip_model: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[TextContent]:
        """pgvector相似度搜索实现"""
        from src.mcp.tools.database_tools import DatabaseTool
        tool = DatabaseTool()
        result = await tool.vector_search(feature_vector, chip_model, top_k, threshold)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    async def _llm_chat(
        self,
        messages: List[Dict],
        model: str = "gpt-4",
        **kwargs
    ) -> List[TextContent]:
        """LLM对话工具实现"""
        from src.mcp.tools.llm_tool import LLMTool
        tool = LLMTool()
        result = await tool.chat(messages, model, **kwargs)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    async def _report_generate(
        self,
        analysis_id: str,
        report_type: str = "html",
        template: str = "default"
    ) -> List[TextContent]:
        """报告生成工具实现"""
        from src.mcp.tools.report_tool import ReportTool
        tool = ReportTool()
        result = await tool.generate(analysis_id, report_type, template)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


# ============================================
# 全局MCP服务器实例
# ============================================
_mcp_server: Optional[ChipFaultMCPServer] = None


def get_mcp_server() -> ChipFaultMCPServer:
    """获取MCP服务器实例（单例模式）"""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = ChipFaultMCPServer()
    return _mcp_server
