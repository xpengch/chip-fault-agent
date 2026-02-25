"""
芯片失效分析AI Agent系统 - 配置管理
"""
import os
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # ============================================
    # 应用配置
    # ============================================
    APP_NAME: str = Field(default="chip-fault-agent", description="应用名称")
    APP_ENV: str = Field(default="development", description="运行环境")
    APP_DEBUG: bool = Field(default=False, description="调试模式")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    API_HOST: str = Field(default="0.0.0.0", description="API监听地址")
    API_PORT: int = Field(default=8000, description="API监听端口")
    API_PREFIX: str = Field(default="/api/v1", description="API前缀")

    # ============================================
    # 数据库配置
    # ============================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/chip_analysis",
        description="数据库连接URL"
    )
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL主机")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL端口")
    POSTGRES_DB: str = Field(default="chip_analysis", description="PostgreSQL数据库")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL用户")
    POSTGRES_PASSWORD: str = Field(default="postgres", description="PostgreSQL密码")

    # ============================================
    # Neo4j配置
    # ============================================
    NEO4J_URI: str = Field(default="bolt://localhost:7687", description="Neo4j连接URI")
    NEO4J_USER: str = Field(default="neo4j", description="Neo4j用户")
    NEO4J_PASSWORD: str = Field(default="neo4j", description="Neo4j密码")

    # ============================================
    # Redis配置
    # ============================================
    REDIS_HOST: str = Field(default="localhost", description="Redis主机")
    REDIS_PORT: int = Field(default=6379, description="Redis端口")
    REDIS_DB: int = Field(default=0, description="Redis数据库")
    REDIS_PASSWORD: str = Field(default="", description="Redis密码")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="Redis最大连接数")

    @property
    def REDIS_URL(self) -> str:
        """构建Redis URL"""
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ============================================
    # LLM配置
    # ============================================
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API密钥")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", description="OpenAI API地址")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo", description="OpenAI模型")
    OPENAI_TEMPERATURE: float = Field(default=0.7, description="OpenAI温度")
    OPENAI_MAX_TOKENS: int = Field(default=4000, description="OpenAI最大token数")

    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API密钥")
    ANTHROPIC_BASE_URL: str = Field(default="https://api.anthropic.com", description="Anthropic API地址")
    ANTHROPIC_MODEL: str = Field(default="claude-3-opus-20240229", description="Anthropic模型")
    ANTHROPIC_MAX_TOKENS: int = Field(default=4000, description="Anthropic最大token数")

    # ============================================
    # 向量嵌入配置
    # ============================================
    EMBEDDING_BACKEND: str = Field(
        default="bge",
        description="Embedding后端: openai, bge"
    )
    EMBEDDING_MODEL: str = Field(
        default="BAAI/bge-large-zh-v1.5",
        description="BGE模型名称 (BAAI/bge-large-zh-v1.5, BAAI/bge-base-zh-v1.5)"
    )
    EMBEDDING_DEVICE: str = Field(default="cpu", description="BGE推理设备: cpu, cuda, mps")
    EMBEDDING_DIMENSIONS: int = Field(default=1024, description="嵌入维度 (bge-large: 1024, bge-base: 768)")
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding模型 (当backend=openai时使用)"
    )

    # ============================================
    # 分析配置
    # ============================================
    DEFAULT_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7,
        description="默认置信度阈值"
    )
    MAX_LOG_SIZE_KB: int = Field(default=100, description="最大日志大小(KB)")
    MAX_BATCH_SIZE: int = Field(default=100, description="最大批量大小")
    ANALYSIS_TIMEOUT_SECONDS: int = Field(default=30, description="分析超时时间")

    # ============================================
    # JWT配置
    # ============================================
    JWT_SECRET_KEY: str = Field(default="your-secret-key", description="JWT密钥")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT算法")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="JWT访问token过期时间")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, description="JWT刷新token过期时间")

    # ============================================
    # 文件存储配置
    # ============================================
    UPLOAD_DIR: str = Field(default="./data/uploads", description="上传文件目录")
    REPORTS_DIR: str = Field(default="./data/reports", description="报告存储目录")
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, description="最大上传文件大小")

    # ============================================
    # 日志配置
    # ============================================
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_DIR: str = Field(default="./data/logs", description="日志目录")
    LOG_ROTATION: str = Field(default="500 MB", description="日志轮转大小")
    LOG_RETENTION: str = Field(default="30 days", description="日志保留时间")

    # ============================================
    # CORS配置
    # ============================================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="CORS允许的源"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="CORS允许凭据")
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"], description="CORS允许的方法")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], description="CORS允许的头部")

    class Config:
        """配置类"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()
