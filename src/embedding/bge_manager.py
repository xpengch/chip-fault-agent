"""
BGE模型管理器
单例模式，缓存已加载的模型
"""
from typing import Optional
from sentence_transformers import SentenceTransformer
from loguru import logger
from threading import Lock


class BGEModelManager:
    """BGE模型管理器 - 单例模式"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._model = None
                    cls._instance._model_name = None
                    cls._instance._device = None
        return cls._instance

    def __init__(self):
        """初始化"""
        self.name = "BGEModelManager"

    def get_model(
        self,
        model_name: str = "BAAI/bge-large-zh-v1.5",
        device: str = "cpu"
    ) -> SentenceTransformer:
        """
        获取BGE模型（使用缓存）

        Args:
            model_name: 模型名称
            device: 设备类型 (cpu, cuda, mps)

        Returns:
            SentenceTransformer 模型实例
        """
        # 检查是否需要重新加载
        if (self._model is None or
            self._model_name != model_name or
            self._device != device):

            with self._lock:
                # 双重检查
                if (self._model is None or
                    self._model_name != model_name or
                    self._device != device):

                    logger.info(f"[BGEModelManager] 加载BGE模型: {model_name}, 设备: {device}")

                    # 释放旧模型
                    if self._model is not None:
                        del self._model

                    # 加载新模型
                    self._model = SentenceTransformer(model_name, device=device)
                    self._model_name = model_name
                    self._device = device

                    logger.success(f"[BGEModelManager] BGE模型加载完成 - 维度: {self._model.get_sentence_embedding_dimension()}")

        return self._model

    def get_embedding_dimension(self) -> Optional[int]:
        """获取当前模型的向量维度"""
        if self._model is not None:
            return self._model.get_sentence_embedding_dimension()
        return None

    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._model is not None

    def unload(self):
        """卸载模型，释放内存"""
        with self._lock:
            if self._model is not None:
                del self._model
                self._model = None
                self._model_name = None
                self._device = None
                logger.info("[BGEModelManager] BGE模型已卸载")


# 全局实例
bge_model_manager = BGEModelManager()


def get_bge_model_manager() -> BGEModelManager:
    """获取BGE模型管理器单例"""
    return bge_model_manager
