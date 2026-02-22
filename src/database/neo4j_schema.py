"""
芯片失效分析AI Agent系统 - Neo4j知识图谱Schema
支持CPU/L3/HA/NoC/DDR/HBM等模块类型
"""

from typing import Optional, List, Dict, Any
from neo4j import AsyncGraphDatabase
from datetime import datetime


# ============================================
# Neo4j连接配置
# ============================================
class Neo4jConfig:
    """Neo4j配置类"""

    def __init__(self):
        from src.config.settings import get_settings
        self.settings = get_settings()

    @property
    def uri(self) -> str:
        """获取连接URI"""
        return self.settings.NEO4J_URI

    @property
    def user(self) -> str:
        """获取用户名"""
        return self.settings.NEO4J_USER

    @property
    def password(self) -> str:
        """获取密码"""
        return self.settings.NEO4J_PASSWORD


# ============================================
# 全局Neo4j驱动实例
# ============================================
_neo4j_driver: Optional[AsyncGraphDatabase] = None


def get_neo4j_driver() -> AsyncGraphDatabase:
    """获取Neo4j驱动实例（单例模式）"""
    global _neo4j_driver
    if _neo4j_driver is None:
        config = Neo4jConfig()
        _neo4j_driver = AsyncGraphDatabase.authenticated(
            config.uri,
            config.user,
            config.password
        )
    return _neo4j_driver


async def close_neo4j():
    """关闭Neo4j连接"""
    global _neo4j_driver
    if _neo4j_driver:
        await _neo4j_driver.close()
        _neo4j_driver = None


# ============================================
# 知识图谱Schema定义
# ============================================

class KnowledgeGraphSchema:
    """知识图谱Schema管理类"""

    # ============================================
    # 节点类型定义
    # ============================================
    NODE_TYPES = {
        # 芯片相关
        'Chip': '芯片型号节点',
        'SoCSubsystem': '子系统节点',

        # 计算相关
        'CPUCore': 'CPU核心节点',
        'CPUCluster': 'CPU集群节点',
        'L2Cache': 'L2缓存节点',
        'L3Cache': 'L3缓存节点',

        # 一致性相关
        'HomeAgent': 'Home Agent（一致性代理）节点',
        'SnoopFilter': 'Snoop Filter节点',
        'Directory': 'Directory节点',

        # 互连相关
        'NoCRouter': 'NoC路由器节点',
        'NoCEndpoint': 'NoC端点节点',

        # 存储相关
        'DDRController': 'DDR控制器节点',
        'HBMController': 'HBM控制器节点',
        'MemoryChannel': '内存通道节点',

        # 故障相关
        'FailureMode': '失效模式节点',
        'RootCause': '根因节点',
        'ErrorCode': '错误码节点',
        'Symptom': '症状节点',
    }

    # ============================================
    # 关系类型定义
    # ============================================
    RELATIONSHIP_TYPES = {
        # 组成关系
        'HAS_SUBSYSTEM': '芯片包含子系统',
        'HAS_MODULE': '子系统包含模块',
        'HAS_CORE': '集群包含核心',
        'BELONGS_TO_CLUSTER': '核心属于集群',
        'HAS_L2': '核心包含L2缓存',
        'HAS_L3': '集群共享L3缓存',

        # 连接关系
        'CONNECTED_TO_HA': '模块连接到HA',
        'CONNECTED_VIA_NOC': '模块通过NoC连接',
        'CONNECTED_TO_MEMORY': '控制器连接到内存',

        # 一致性关系
        'MONITORED_BY_HA': '缓存被HA监控',
        'FILTERED_BY_SNOOP': '请求被Snoop Filter过滤',
        'SERVED_BY_DIRECTORY': '请求被Directory服务',

        # 故障关系
        'CAN_FAIL': '模块可能发生失效',
        'HAS_ERROR': '失效模式包含错误码',
        'CAUSED_BY': '根因导致失效',
        'INDICATES': '症状指示失效',

        # 层次关系
        'LOCATED_IN': '位于（物理位置）',
        'POWERED_BY': '供电域',
        'CLOCKED_BY': '时钟域',
    }

    @staticmethod
    def get_node_properties(node_type: str) -> Dict[str, str]:
        """获取节点属性定义"""
        properties = {
            'Chip': {
                'model': 'string',
                'series': 'string',
                'architecture': 'string',
                'process_node': 'string',
                'num_cores': 'integer',
                'release_date': 'date',
            },
            'SoCSubsystem': {
                'name': 'string',
                'type': 'string',  # compute/cache/interconnect/memory/io
                'description': 'string',
            },
            'CPUCore': {
                'core_id': 'integer',
                'cluster_id': 'string',
                'architecture': 'string',
                'frequency_mhz': 'integer',
            },
            'L3Cache': {
                'size_kb': 'integer',
                'associativity': 'integer',
                'banks': 'integer',
            },
            'HomeAgent': {
                'role': 'string',
                'protocol': 'string',  # MESI/MOESI/Dragon
                'snoop_filter_enabled': 'boolean',
            },
            'DDRController': {
                'protocol': 'string',
                'channels': 'integer',
                'capacity_gb': 'integer',
                'bandwidth_gbps': 'float',
            },
            'FailureMode': {
                'name': 'string',
                'category': 'string',  # timing/logic/power/physical
                'description': 'string',
            },
            'ErrorCode': {
                'code': 'string',
                'severity': 'string',
                'description': 'string',
            },
            'RootCause': {
                'name': 'string',
                'category': 'string',  # design/process/manufacturing/software
                'solution': 'string',
            },
        }
        return properties.get(node_type, {})


# ============================================
# 知识图谱初始化脚本
# ============================================
async def init_knowledge_graph(driver: AsyncGraphDatabase):
    """
    初始化知识图谱
    创建约束和索引
    """
    async with driver.session() as session:
        # ========================================
        # 创建唯一性约束
        # ========================================
        constraints = [
            "CREATE CONSTRAINT chip_model_unique IF NOT EXISTS FOR (c:Chip) REQUIRE c.model IS UNIQUE",
            "CREATE CONSTRAINT subsystem_name_unique IF NOT EXISTS FOR (s:SoCSubsystem) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT module_name_unique IF NOT EXISTS FOR (m:CPUCore) REQUIRE m.core_id IS UNIQUE",
            "CREATE CONSTRAINT module_name_unique2 IF NOT EXISTS FOR (m:L3Cache) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT error_code_unique IF NOT EXISTS FOR (e:ErrorCode) REQUIRE e.code IS UNIQUE",
        ]

        for constraint in constraints:
            try:
                await session.run(constraint)
            except Exception as e:
                if 'already exists' not in str(e):
                    raise

        # ========================================
        # 创建全文索引
        # ========================================
        indexes = [
            "CREATE INDEX chip_search IF NOT EXISTS FOR (c:Chip) USING FULLTEXT(c.model, c.architecture)",
            "CREATE INDEX module_search IF NOT EXISTS FOR (m:CPUCore) USING FULLTEXT(m.architecture)",
            "CREATE INDEX error_search IF NOT EXISTS FOR (e:ErrorCode) USING FULLTEXT(e.code, e.description)",
        ]

        for index in indexes:
            await session.run(index)


# ============================================
# 知识图谱查询接口
# ============================================
class KnowledgeGraphRepository:
    """知识图谱仓库类"""

    def __init__(self, driver: Optional[AsyncGraphDatabase] = None):
        self.driver = driver or get_neo4j_driver()

    # ============================================
    # 芯片相关查询
    # ============================================
    async def get_chip_by_model(self, chip_model: str) -> Optional[Dict]:
        """根据型号获取芯片信息"""
        query = """
        MATCH (c:Chip {model: $chip_model})
        RETURN c
        LIMIT 1
        """
        async with self.driver.session() as session:
            result = await session.run(query, chip_model=chip_model)
            record = await result.single()
            return record.data() if record else None

    async def get_chip_subsystems(self, chip_model: str) -> List[Dict]:
        """获取芯片的所有子系统"""
        query = """
        MATCH (c:Chip {model: $chip_model})-[:HAS_SUBSYSTEM]->(s:SoCSubsystem)
        RETURN s
        ORDER BY s.type, s.name
        """
        async with self.driver.session() as session:
            result = await session.run(query, chip_model=chip_model)
            records = await result.data()
            return [record['s'] for record in records]

    async def get_chip_modules(self, chip_model: str, subsystem_type: Optional[str] = None) -> List[Dict]:
        """获取芯片的所有模块"""
        query = """
        MATCH (c:Chip {model: $chip_model})-[:HAS_SUBSYSTEM]->(s:SoCSubsystem)
        -[:HAS_MODULE]->(m:CPUCore|L3Cache|HomeAgent|DDRController|NoCRouter)
        WHERE $subsystem_type IS NULL OR s.type = $subsystem_type
        RETURN m, s
        ORDER BY s.type, TYPE(m)
        """
        async with self.driver.session() as session:
            result = await session.run(
                query,
                chip_model=chip_model,
                subsystem_type=subsystem_type
            )
            records = await result.data()
            return [
                {
                    'id': str(record['m'].id),
                    'name': record['m'].get('name') or record['m'].get('core_id'),
                    'type': TYPE(record['m']).__name__,
                    'subsystem': record['s']['name'],
                    'subsystem_type': record['s']['type'],
                    'properties': dict(record['m'])
                }
                for record in records
            ]

    # ============================================
    # 故障推理相关查询
    # ============================================
    async def get_failure_modes_by_module(
        self,
        chip_model: str,
        module_type: str
    ) -> List[Dict]:
        """获取模块可能的失效模式"""
        query = """
        MATCH (c:Chip {model: $chip_model})-[:HAS_MODULE]->(m)
        WHERE TYPE(m) = $module_type
        MATCH (m)-[:CAN_FAIL]->(f:FailureMode)
        RETURN f.name AS failure_mode, f.category AS failure_category,
               f.description AS description
        ORDER BY f.name
        """
        async with self.driver.session() as session:
            result = await session.run(query, chip_model=chip_model, module_type=module_type)
            records = await result.data()
            return [record for record in records]

    async def get_root_causes_by_failure_mode(
        self,
        failure_mode: str
    ) -> List[Dict]:
        """获取失效模式对应的根因"""
        query = """
        MATCH (f:FailureMode {name: $failure_mode})-[:CAUSED_BY]->(r:RootCause)
        RETURN r.name AS root_cause, r.category AS category,
               r.solution AS solution
        ORDER BY r.category, r.name
        """
        async with self.driver.session() as session:
            result = await session.run(query, failure_mode=failure_mode)
            records = await result.data()
            return [record for record in records]

    async def get_error_codes_by_module(
        self,
        chip_model: str,
        module_type: str
    ) -> List[Dict]:
        """获取模块相关的错误码"""
        query = """
        MATCH (c:Chip {model: $chip_model})-[:HAS_MODULE]->(m)
        WHERE TYPE(m) = $module_type
        MATCH (m)-[:CAN_FAIL]->(f:FailureMode)-[:HAS_ERROR]->(e:ErrorCode)
        RETURN e.code AS error_code, e.severity AS severity,
               e.description AS description, f.name AS failure_mode
        ORDER BY e.code
        """
        async with self.driver.session() as session:
            result = await session.run(query, chip_model=chip_model, module_type=module_type)
            records = await result.data()
            return [record for record in records]

    # ============================================
    # HA（一致性代理）特定查询
    # ============================================
    async def get_ha_topology(self, chip_model: str) -> Dict:
        """获取HA拓扑信息（HA连接的CPU、L3缓存等）"""
        query = """
        MATCH (c:Chip {model: $chip_model})-[:HAS_MODULE]->(ha:HomeAgent)
        OPTIONAL MATCH (ha)-[:CONNECTED_TO_HA]->(cpu:CPUCore)
        OPTIONAL MATCH (ha)-[:CONNECTED_TO_HA]->(l3:L3Cache)
        OPTIONAL MATCH (ha)-[:CONNECTED_TO_HA]->(sf:SnoopFilter)
        RETURN ha {
            .name: ha.name,
            .role: ha.role,
            .protocol: ha.protocol,
            .connected_cores: collect(cpu.core_id),
            .connected_l3: l3.name,
            .snoop_filter: sf.name
        }
        """
        async with self.driver.session() as session:
            result = await session.run(query, chip_model=chip_model)
            record = await result.single()
            return record.data() if record else {}

    # ============================================
    # NoC路径查询
    # ============================================
    async def find_noc_path(
        self,
        chip_model: str,
        source_module: str,
        target_module: str
    ) -> List[Dict]:
        """查找NoC路径"""
        query = """
        MATCH (c:Chip {model: $chip_model})-[:HAS_MODULE]->(src)
        WHERE src.name = $source_module
        MATCH (c)-[:HAS_MODULE]->(tgt)
        WHERE tgt.name = $target_module
        MATCH path = shortestPath((src)-[:CONNECTED_VIA_NOC*]-(tgt))
        RETURN [node in nodes(path) WHERE node:NoCRouter|NoCEndpoint] AS noc_nodes,
               length(path) AS hop_count
        """
        async with self.driver.session() as session:
            result = await session.run(
                query,
                chip_model=chip_model,
                source_module=source_module,
                target_module=target_module
            )
            records = await result.data()
            return [record for record in records]

    # ============================================
    # 创建芯片数据
    # ============================================
    async def create_chip(
        self,
        model: str,
        series: Optional[str] = None,
        architecture: Optional[str] = None,
        process_node: Optional[str] = None,
        num_cores: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """创建芯片节点"""
        query = """
        CREATE (c:Chip)
        SET c = {
            .model: $model,
            .series: $series,
            .architecture: $architecture,
            .process_node: $process_node,
            .num_cores: $num_cores,
            .created_at: datetime()
        }
        RETURN c.id AS node_id
        """
        async with self.driver.session() as session:
            result = await session.run(
                query,
                model=model,
                series=series,
                architecture=architecture,
                process_node=process_node,
                num_cores=num_cores
            )
            record = await result.single()
            return str(record['node_id']) if record else None

    # ============================================
    # 创建模块数据
    # ============================================
    async def create_module(
        self,
        chip_model: str,
        module_type: str,
        properties: Dict,
        subsystem_name: Optional[str] = None
    ) -> str:
        """创建模块节点"""
        # 构建动态查询
        if subsystem_name:
            query = f"""
            MATCH (c:Chip {{model: $chip_model}})-[:HAS_SUBSYSTEM]->(s:SoCSubsystem {{name: $subsystem_name}})
            CREATE (c)-[:HAS_MODULE]->(m:{module_type} $properties)
            RETURN m.id AS node_id
            """
        else:
            query = f"""
            MATCH (c:Chip {{model: $chip_model}})
            CREATE (c)-[:HAS_MODULE]->(m:{module_type} $properties)
            RETURN m.id AS node_id
            """

        async with self.driver.session() as session:
            result = await session.run(
                query,
                chip_model=chip_model,
                subsystem_name=subsystem_name,
                properties=properties
            )
            record = await result.single()
            return str(record['node_id']) if record else None
