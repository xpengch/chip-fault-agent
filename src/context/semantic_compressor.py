"""
语义日志压缩器 - 基于 BGE 向量的智能压缩
保留语义相关的日志，尽可能不丢失关键信息
"""

import re
import numpy as np
from typing import Dict, List, Any, Set, Tuple
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity


class SemanticLogCompressor:
    """
    基于语义的日志压缩器

    策略：
    1. 使用 BGE 模型计算每行日志的语义向量
    2. 计算与故障特征的语义相似度
    3. 保留高相似度 + 关键模式的日志
    4. 去除语义重复的日志
    """

    # 关键词模式（必须保留）
    CRITICAL_PATTERNS = [
        r'\bERROR\b', r'\bFAIL\b', r'\bException\b', r'\bfault\b',
        r'\b0X[0-9A-F]{4,}\b',  # 错误码
        r'\bregister\b', r'\breg\s*[:=]',  # 寄存器
        r'\bstack\s*trace\b', r'\bat\s+\w+',  # 栈信息
        r'\bcrash\b', r'\bpanic\b', r'\babort\b',
        r'\btimeout\b', r'\bdeadlock\b',
    ]

    # 上下文窗口：高相关行的周围行数
    CONTEXT_WINDOW = 2

    def __init__(
        self,
        target_size_kb: int = 35,
        similarity_threshold: float = 0.3,
        min_lines_to_preserve: int = 50
    ):
        """
        初始化语义压缩器

        Args:
            target_size_kb: 目标大小（KB）
            similarity_threshold: 相似度阈值，高于此值的行会被优先保留
            min_lines_to_preserve: 最少保留行数
        """
        self.target_size_kb = target_size_kb
        self.target_size_bytes = target_size_kb * 1024
        self.similarity_threshold = similarity_threshold
        self.min_lines_to_preserve = min_lines_to_preserve

        # 编译正则表达式
        self.critical_regex = [re.compile(p, re.IGNORECASE) for p in self.CRITICAL_PATTERNS]

        # 延迟加载 BGE 模型
        self._bge_model = None

    @property
    def bge_model(self):
        """延迟加载 BGE 模型"""
        if self._bge_model is None:
            from src.embedding import get_bge_model_manager
            from src.config.settings import get_settings

            settings = get_settings()
            model_manager = get_bge_model_manager()
            self._bge_model = model_manager.get_model(
                model_name=settings.EMBEDDING_MODEL,
                device=settings.EMBEDDING_DEVICE
            )
            logger.info("[SemanticCompressor] BGE 模型加载完成")

        return self._bge_model

    def compress(
        self,
        raw_log: str,
        fault_features: Dict = None,
        preserve_ratio: float = 0.5
    ) -> Dict[str, Any]:
        """
        语义压缩日志

        Args:
            raw_log: 原始日志
            fault_features: 故障特征（用于计算语义相关性）
            preserve_ratio: 保留比例（初步筛选）

        Returns:
            {
                "compressed_log": str,
                "compression_ratio": float,
                "preserved_critical": int,
                "preserved_semantic": int,
                "preserved_context": int,
                "metadata": Dict
            }
        """
        if not raw_log:
            return {
                "compressed_log": "",
                "compression_ratio": 0.0,
                "preserved_critical": 0,
                "preserved_semantic": 0,
                "preserved_context": 0,
                "metadata": {}
            }

        original_size = len(raw_log.encode('utf-8'))
        original_size_kb = original_size / 1024

        logger.info(f"[SemanticCompressor] 开始语义压缩 - 原始: {original_size_kb:.1f} KB")

        # 解析日志行
        lines = raw_log.split('\n')

        # 步骤1: 分析每行的重要性
        line_scores = self._analyze_lines(lines, fault_features or {})

        # 步骤2: 根据分数选择要保留的行
        selected_indices = self._select_lines(
            lines,
            line_scores,
            preserve_ratio=preserve_ratio
        )

        # 步骤3: 添加上下文窗口
        final_indices = self._add_context_window(selected_indices, len(lines))

        # 步骤4: 去除语义重复
        deduplicated_indices = self._deduplicate_semantic(
            lines, final_indices, fault_features or {}
        )

        # 步骤5: 构建压缩结果
        compressed_lines = [lines[i] for i in sorted(deduplicated_indices)]
        compressed_log = '\n'.join(compressed_lines)

        # 统计信息
        compressed_size = len(compressed_log.encode('utf-8'))
        compression_ratio = compressed_size / original_size if original_size > 0 else 0

        # 统计保留类型
        critical_count = sum(1 for i in deduplicated_indices if line_scores[i]['is_critical'])
        semantic_count = sum(1 for i in deduplicated_indices if line_scores[i].get('semantic_score', 0) > self.similarity_threshold)
        context_count = len(deduplicated_indices) - critical_count - semantic_count

        logger.info(
            f"[SemanticCompressor] 压缩完成: "
            f"{original_size_kb:.1f} KB -> {compressed_size / 1024:.1f} KB "
            f"({compression_ratio:.1%}), "
            f"保留: 关键={critical_count}, 语义={semantic_count}, 上下文={context_count}"
        )

        return {
            "compressed_log": compressed_log,
            "compression_ratio": compression_ratio,
            "preserved_critical": critical_count,
            "preserved_semantic": semantic_count,
            "preserved_context": context_count,
            "metadata": {
                "original_lines": len(lines),
                "compressed_lines": len(compressed_lines),
                "average_similarity": np.mean([s.get('semantic_score', 0) for s in line_scores.values()]) if line_scores else 0
            }
        }

    def _analyze_lines(self, lines: List[str], fault_features: Dict) -> Dict[int, Dict]:
        """分析每行的重要性"""
        line_scores = {}

        # 获取查询向量（故障特征的语义向量）
        query_embedding = self._get_query_embedding(fault_features)

        # 批量计算所有行的 embedding
        line_embeddings = []
        for line in lines:
            if line.strip():
                try:
                    emb = self.bge_model.encode(
                        line,
                        normalize_embeddings=True,
                        show_progress_bar=False
                    )
                    line_embeddings.append(emb)
                except Exception as e:
                    logger.warning(f"[SemanticCompressor] Embedding 失败: {e}")
                    line_embeddings.append(np.zeros(1024))  # BGE-large 的维度
            else:
                line_embeddings.append(np.zeros(1024))

        line_embeddings = np.array(line_embeddings)

        # 计算每行与查询的语义相似度
        if query_embedding is not None:
            similarities = cosine_similarity(
                line_embeddings.reshape(-1, 1),
                query_embedding.reshape(1, -1)
            ).flatten()
        else:
            similarities = np.zeros(len(lines))

        # 分析每行
        for idx, (line, embedding, similarity) in enumerate(zip(lines, line_embeddings, similarities)):
            # 检查是否包含关键模式
            is_critical = any(regex.search(line) for regex in self.critical_regex)

            # 计算综合分数
            score = {
                'index': idx,
                'content': line,
                'is_critical': is_critical,
                'semantic_score': float(similarity),
                'is_empty': not line.strip(),
                'embedding': embedding,
                'final_score': 0.0  # 将在后面计算
            }

            # 基础分数
            if is_critical:
                score['final_score'] = 1.0  # 关键信息优先级最高
            else:
                score['final_score'] = float(similarity)

            # 长度惩罚：太长的行降低优先级
            if len(line) > 200:
                score['final_score'] *= 0.8

            line_scores[idx] = score

        return line_scores

    def _get_query_embedding(self, fault_features: Dict) -> np.ndarray:
        """获取故障特征的语义向量"""
        query_parts = []

        # 添加错误码
        error_codes = fault_features.get('error_codes', [])
        if error_codes:
            query_parts.append(' '.join(error_codes[:10]))

        # 添加模块信息
        modules = fault_features.get('modules', [])
        if modules:
            query_parts.append(' '.join(modules))

        # 添加故障描述
        description = fault_features.get('fault_description', '')
        if description:
            query_parts.append(description)

        if not query_parts:
            return None

        query_text = ' '.join(query_parts)

        try:
            embedding = self.bge_model.encode(
                query_text,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return embedding
        except Exception as e:
            logger.warning(f"[SemanticCompressor] 查询 embedding 失败: {e}")
            return None

    def _select_lines(
        self,
        lines: List[str],
        line_scores: Dict[int, Dict],
        preserve_ratio: float = 0.5
    ) -> Set[int]:
        """根据分数选择要保留的行"""
        # 目标行数
        target_count = max(
            self.min_lines_to_preserve,
            int(len(lines) * preserve_ratio)
        )

        # 按分数排序
        sorted_scores = sorted(
            [(idx, score['final_score']) for idx, score in line_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # 优先选择高分行
        selected = set()
        for idx, score in sorted_scores[:target_count]:
            if not line_scores[idx]['is_empty']:
                selected.add(idx)

        # 确保所有关键行都被保留
        for idx, score in line_scores.items():
            if score['is_critical']:
                selected.add(idx)

        return selected

    def _add_context_window(self, selected_indices: Set[int], total_lines: int) -> Set[int]:
        """添加上下文窗口"""
        extended = set(selected_indices)

        for idx in selected_indices:
            # 添加前后的上下文
            for offset in range(-self.CONTEXT_WINDOW, self.CONTEXT_WINDOW + 1):
                target_idx = idx + offset
                if 0 <= target_idx < total_lines:
                    extended.add(target_idx)

        return extended

    def _deduplicate_semantic(
        self,
        lines: List[str],
        indices: Set[int],
        fault_features: Dict
    ) -> Set[int]:
        """去除语义重复的行"""
        if len(indices) <= self.min_lines_to_preserve:
            return indices

        # 获取选中行的 embedding
        selected_lines = [(i, lines[i]) for i in sorted(indices)]
        embeddings = []

        for idx, line in selected_lines:
            try:
                emb = self.bge_model.encode(
                    line,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                embeddings.append((idx, emb))
            except Exception as e:
                logger.warning(f"[SemanticCompressor] 去重 embedding 失败: {e}")
                embeddings.append((idx, np.zeros(1024)))

        if not embeddings:
            return indices

        # 计算相似度矩阵
        idx_list = [e[0] for e in embeddings]
        emb_matrix = np.array([e[1] for e in embeddings])

        similarity_matrix = cosine_similarity(emb_matrix)

        # 聚类去重
        deduplicated = set()

        # 使用贪心算法：选择相似度低的代表
        n_samples = len(idx_list)
        used = [False] * n_samples

        for i in range(n_samples):
            if used[i]:
                continue

            # 选择这个作为代表
            deduplicated.add(idx_list[i])
            used[i] = True

            # 标记相似的去掉
            for j in range(i + 1, n_samples):
                if not used[j] and similarity_matrix[i][j] > 0.95:  # 高相似度阈值
                    used[j] = True

        return deduplicated
