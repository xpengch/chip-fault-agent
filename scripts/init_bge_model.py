"""
初始化BGE模型
首次运行时下载BGE模型到本地缓存
"""
import asyncio
from loguru import logger
from sentence_transformers import SentenceTransformer


async def init_bge_model():
    """初始化BGE模型"""
    from src.config.settings import get_settings
    settings = get_settings()

    model_name = settings.EMBEDDING_MODEL
    device = settings.EMBEDDING_DEVICE

    logger.info(f"[BGE Init] 开始下载BGE模型: {model_name}")
    logger.info(f"[BGE Init] 设备: {device}")
    logger.info("[BGE Init] 首次下载可能需要几分钟，请稍候...")

    def _load_model():
        return SentenceTransformer(model_name, device=device)

    # 在线程池中加载模型
    loop = asyncio.get_event_loop()
    model = await loop.run_in_executor(None, _load_model)

    # 测试embedding
    test_text = "芯片失效分析测试文本"
    embedding = model.encode(test_text, normalize_embeddings=True)

    logger.success(f"[BGE Init] BGE模型初始化成功!")
    logger.success(f"[BGE Init] 模型: {model_name}")
    logger.success(f"[BGE Init] 向量维度: {len(embedding)}")
    logger.success(f"[BGE Init] 设备: {device}")

    # 测试向量相似度
    import numpy as np
    vec1 = model.encode("DDR错误", normalize_embeddings=True)
    vec2 = model.encode("内存故障", normalize_embeddings=True)
    similarity = np.dot(vec1, vec2)
    logger.info(f"[BGE Init] 相似度测试: DDR错误 vs 内存故障 = {similarity:.4f}")

    return model


if __name__ == "__main__":
    asyncio.run(init_bge_model())
