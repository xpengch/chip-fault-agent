"""
芯片失效分析AI Agent系统 - 知识图谱MCP工具
基于Neo4j实现知识查询和推理
"""

from typing import Dict, List, Optional, Any
from neo4j import AsyncGraphDatabase
import json


class KnowledgeGraphTool:
    """知识图谱工具类"""

    def __init__(self):
        """初始化工具"""
        from src.database.neo4j_schema import get_neo4j_driver
        self.driver = get_neo4j_driver()

    async def query(
        self,
        query_type: str,
        chip_model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行知识图谱查询

        Args:
            query_type: 查询类型
                - chip_structure: 芯片结构
                - failure_modes: 失效模式
                - root_causes: 根因
                - module_info: 模块信息
            chip_model: 芯片型号
            **kwargs: 其他查询参数

        Returns:
            查询结果
        """

        if query_type == "chip_structure":
            return await self._query_chip_structure(chip_model, **kwargs)
        elif query_type == "failure_modes":
            return await self._query_failure_modes(chip_model, **kwargs)
        elif query_type == "root_causes":
            return await self._query_root_causes(chip_model, **kwargs)
        elif query_type == "module_info":
            return await self._query_module_info(chip_model, **kwargs)
        else:
            raise ValueError(f"Unknown query type: {query_type}")

    async def _query_chip_structure(
        self,
        chip_model: str,
        subsystem_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询芯片结构

        Returns:
            {
                "chip": {...},
                "subsystems": [...],
                "modules": [...]
            }
        """

        query = """
            MATCH (c:Chip {model: $chip_model})
            OPTIONAL MATCH (c)-[:HAS_SUBSYSTEM]->(s:SoCSubsystem)
        """

        params = {"chip_model": chip_model}

        if subsystem_type:
            query += " WHERE s.type = $subsystem_type"
            params["subsystem_type"] = subsystem_type

        query += """
            RETURN c, s
            ORDER BY s.type, s.name
        """

        async with self.driver.session() as session:
            result = await session.run(query, params)

            subsystems = []
            modules = []
            chip_info = None

            for record in result:
                if record["c"]:
                    chip_info = {
                        "model": record["c"]["model"],
                        "architecture": record["c"].get("architecture"),
                        "series": record["c"].get("series"),
                        "num_cores": record["c"].get("num_cores")
                    }

                if record["s"]:
                    subsystems.append({
                        "id": record["s"].id,
                        "name": record["s"]["name"],
                        "type": record["s"]["type"],
                        "description": record["s"].get("description")
                    })

            return {
                "chip": chip_info,
                "subsystems": subsystems,
                "modules": modules
            }

    async def _query_failure_modes(
        self,
        chip_model: str,
        module_type: Optional[str] = None,
        module_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询失效模式

        Returns:
            {
                "failure_modes": [...],
                "error_codes": [...]
            }
        """

        query = """
            MATCH (c:Chip {model: $chip_model})-[:HAS_SUBSYSTEM]->()-[:HAS_MODULE]->(m:SoCModule)
            WHERE $module_type IS NULL OR m.type = $module_type
        """

        params = {"chip_model": chip_model, "module_type": module_type}

        if module_name:
            query += " AND m.name = $module_name"
            params["module_name"] = module_name

        query += """
            MATCH (m)-[:CAN_FAIL]->(fm:FailureMode)
            MATCH (fm)-[:HAS_ERROR]->(ec:ErrorCode)
            RETURN fm.name AS failure_mode, fm.category AS category,
                   ec.code AS error_code, ec.severity AS severity
            ORDER BY fm.name, ec.code
        """

        async with self.driver.session() as session:
            result = await session.run(query, params)

            failure_modes = {}
            error_codes = []

            for record in result:
                mode = record["failure_mode"]
                if mode not in failure_modes:
                    failure_modes[mode] = {
                        "name": mode,
                        "category": record["category"],
                        "error_codes": []
                    }
                failure_modes[mode]["error_codes"].append({
                    "code": record["error_code"],
                    "severity": record["severity"]
                })

            return {
                "failure_modes": failure_modes,
                "error_codes": error_codes
            }

    async def _query_root_causes(
        self,
        chip_model: str,
        failure_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询根因

        Returns:
            {
                "root_causes": [...]
            }
        """

        query = """
            MATCH (c:Chip {model: $chip_model})-[:HAS_SUBSYSTEM]->()-[:HAS_MODULE]->(m:SoCModule)
        """

        params = {"chip_model": chip_model}

        if failure_mode:
            query += " MATCH (m)-[:CAN_FAIL]->(fm:FailureMode {name: $failure_mode})"
            params["failure_mode"] = failure_mode

        query += """
            MATCH (fm)-[:CAUSED_BY]->(rc:RootCause)
            RETURN rc.name AS root_cause, rc.category AS category,
                   rc.solution AS solution
            ORDER BY rc.category, rc.name
        """

        async with self.driver.session() as session:
            result = await session.run(query, params)

            root_causes = {}
            for record in result:
                root_causes[record["root_cause"]] = {
                    "category": record["category"],
                    "solution": record["solution"]
                }

            return {"root_causes": root_causes}

    async def _query_module_info(
        self,
        chip_model: str,
        module_type: str,
        module_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询模块信息

        Returns:
            {
                "module": {...},
                "connections": [...]
            }
        """

        query = """
            MATCH (c:Chip {model: $chip_model})-[:HAS_SUBSYSTEM]->(s:SoCSubsystem)
            MATCH (s)-[:HAS_MODULE]->(m:SoCModule {type: $module_type})
        """

        params = {"chip_model": chip_model, "module_type": module_type}

        if module_name:
            query += " WHERE m.name = $module_name"
            params["module_name"] = module_name

        query += """
            MATCH (m)-[CONNECTED_VIA_NOC]->(connected:SoCModule)
            RETURN m, s, connected
        """

        async with self.driver.session() as session:
            result = await session.run(query, params)

            module_info = None
            connections = []

            for record in result:
                if not module_info:
                    module_info = {
                        "name": record["m"]["name"],
                        "type": record["m"]["type"],
                        "subsystem": record["s"]["name"],
                        "subsystem_type": record["s"]["type"],
                        "attributes": record["m"].get("attributes", {})
                    }

                if record["connected"]:
                    connections.append({
                        "name": record["connected"]["name"],
                        "type": record["connected"]["type"]
                    })

            return {
                "module": module_info,
                "connections": connections
            }

    async def infer_failure_domain(
        self,
        chip_model: str,
        error_codes: List[str],
        symptoms: str
    ) -> Dict[str, Any]:
        """
        基于错误码和症状推断失效域

        Returns:
            {
                "domain": "compute/storage/interconnect/...",
                "confidence": 0.0-1.0,
                "reasoning": "..."
            }
        """

        # 基于错误码前缀判断
        for code in error_codes:
            if code.startswith(("0xCO", "0xDAT")):
                return {"domain": "compute", "confidence": 0.9, "reasoning": "Error code indicates compute unit failure"}
            elif code.startswith(("0xL2", "0xL3")):
                return {"domain": "cache", "confidence": 0.9, "reasoning": "Error code indicates cache failure"}
            elif code.startswith(("0xHA", "0xNOC")):
                return {"domain": "interconnect", "confidence": 0.9, "reasoning": "Error code indicates interconnect failure"}
            elif code.startswith(("0xDDR", "0xHBM")):
                return {"domain": "memory", "confidence": 0.9, "reasoning": "Error code indicates memory failure"}

        # 基于症状关键词判断
        symptoms_lower = symptoms.lower()
        if any(kw in symptoms_lower for kw in ["hang", "freeze", "timeout"]):
            return {"domain": "interconnect", "confidence": 0.6, "reasoning": "Symptoms indicate interconnect issue"}
        elif any(kw in symptoms_lower for kw in ["corruption", "ecc", "parity"]):
            return {"domain": "memory", "confidence": 0.7, "reasoning": "Symptoms indicate memory issue"}
        elif any(kw in symptoms_lower for kw in ["crash", "exception", "trap"]):
            return {"domain": "compute", "confidence": 0.6, "reasoning": "Symptoms indicate compute issue"}

        # 未知情况
        return {
            "domain": "unknown",
            "confidence": 0.3,
            "reasoning": "Unable to determine domain from available information"
        }

    async def get_related_cases(
        self,
        chip_model: str,
        module_type: str,
        failure_mode: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查询相关历史案例

        Returns:
            相关案例列表
        """

        query = """
            MATCH (c:Chip {model: $chip_model})-[:HAS_SUBSYSTEM]->()-[:HAS_MODULE]->(m:SoCModule {type: $module_type})
            MATCH (m)-[:CAN_FAIL]->(fm:FailureMode {name: $failure_mode})
            MATCH (c)-[:HAS_SUBSYSTEM]->()-[:HAS_MODULE]->()-[:CAN_FAIL]->(fm2:FailureMode {name: $failure_mode})
            MATCH (c)-[:HAS_SUBSYSTEM]->(sub)-[:HAS_MODULE]->(m2)-[:CAN_FAIL]->(fm)
            WHERE fm2.name = $failure_mode
            MATCH (c)-[:HAS_SUBSYSTEM]->()-[:HAS_MODULE]->(m2)-[:HAS_CASE]->(fc:FailureCase)
            RETURN fc.case_id, fc.symptoms, fc.error_codes, fc.root_cause, fc.solution
            ORDER BY fc.created_at DESC
            LIMIT $limit
        """

        async with self.driver.session() as session:
            result = await session.run(
                query,
                {
                    "chip_model": chip_model,
                    "module_type": module_type,
                    "failure_mode": failure_mode,
                    "limit": limit
                }
            )

            cases = []
            for record in result:
                cases.append({
                    "case_id": record["fc.case_id"],
                    "symptoms": record["fc.symptoms"],
                    "error_codes": record["fc.error_codes"],
                    "root_cause": record["fc.root_cause"],
                    "solution": record["fc.solution"]
                })

            return cases
