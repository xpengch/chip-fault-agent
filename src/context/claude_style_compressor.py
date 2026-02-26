"""
Claude Code 风格的上下文压缩器
使用智��优先级系统和 token 预算管理
"""

import re
import numpy as np
from typing import Dict, List, Any, Set, Tuple, Optional
from loguru import logger

from .token_budget import (
    TokenBudgetManager,
    ContextToken,
    Priority,
    get_token_budget_manager
)


class ClaudeStyleCompressor:
    """
    Claude Code 风格的上下文压缩器

    特点：
    1. 基于 token 预算管理
    2. 优先级系统（CRITICAL > HIGH > MEDIUM > LOW）
    3. 智能截断：保留信息密度高的部分
    4. 滑动窗口：保留最近的高优先级内容
    5. 语义去重：去除重复但保留不同信息
    """

    # 关键模式（自动分配 CRITICAL 优先级）
    CRITICAL_PATTERNS = [
        (r'\b0X[0-9A-F]{4,}\b', 'error_code'),      # 错误码
        (r'\bERROR\b', 'error'),                      # 错误
        (r'\bFAIL\w*', 'failure'),                    # 失败
        (r'\bException\b', 'exception'),              # 异常
        (r'\bcrash\b', 'crash'),                      # 崩溃
        (r'\bpanic\b', 'panic'),                      # 恐慌
        (r'\bregister\b', 'register'),                # 寄存器
        (r'\breg\s*[:=]', 'register'),                # 寄存器
        (r'\bstack\s*trace\b', 'stack_trace'),       # 栈跟踪
        (r'\bat\s+\w+\(', 'call_stack'),             # 调用栈
        (r'\btimeout\b', 'timeout'),                  # 超时
        (r'\bdeadlock\b', 'deadlock'),                # 死锁
        (r'\babort\b', 'abort'),                      # 中止
        (r'\b0x[0-9a-f]{8,}\b', 'memory_address'),   # 内存地址
    ]

    # 高价值模式（自动分配 HIGH 优先级）
    HIGH_VALUE_PATTERNS = [
        (r'\bwarning\b', 'warning'),
        (r'\bretry\b', 'retry'),
        (r'\brecover\b', 'recovery'),
        (r'\bfallback\b', 'fallback'),
        (r'\brollback\b', 'rollback'),
        (r'\brestart\b', 'restart'),
    ]

    # 噪音模式（自动分配 MINIMAL 优先级）
    NOISE_PATTERNS = [
        r'^\s*$',                                    # 空行
        r'^[=\-]{3,}$',                             # 分隔线
        r'^\s*\*{3,}\s*$',                          # 星号线
        r'^\s*#{3,}\s*$',                           # 井号线
        r'^\[DEBUG\]',                              # 调试标记（可选）
    ]

    def __init__(
        self,
        token_budget_manager: Optional[TokenBudgetManager] = None,
        target_tokens: int = 18000,
        enable_semantic: bool = True,
        similarity_threshold: float = 0.3
    ):
        """
        初始化压缩器

        Args:
            token_budget_manager: Token 预算管理器
            target_tokens: 目标 token 数量
            enable_semantic: 是否启用语义分析
            similarity_threshold: 语义相似度阈值
        """
        self.token_manager = token_budget_manager or get_token_budget_manager()
        self.target_tokens = target_tokens
        self.enable_semantic = enable_semantic
        self.similarity_threshold = similarity_threshold

        # 编译正则表达式
        self.critical_regex = [(re.compile(p, re.IGNORECASE), name) for p, name in self.CRITICAL_PATTERNS]
        self.high_value_regex = [(re.compile(p, re.IGNORECASE), name) for p, name in self.HIGH_VALUE_PATTERNS]
        self.noise_regex = [re.compile(p) for p in self.NOISE_PATTERNS]

        # 延迟加载 BGE 模型
        self._bge_model = None

    @property
    def bge_model(self):
        """延迟加载 BGE 模型"""
        if self._bge_model is None and self.enable_semantic:
            from src.embedding import get_bge_model_manager
            from src.config.settings import get_settings

            try:
                settings = get_settings()
                model_manager = get_bge_model_manager()
                self._bge_model = model_manager.get_model(
                    model_name=settings.EMBEDDING_MODEL,
                    device=settings.EMBEDDING_DEVICE
                )
                logger.info("[ClaudeStyleCompressor] BGE 模型加载完成")
            except Exception as e:
                logger.warning(f"[ClaudeStyleCompressor] BGE 模型加载失败: {e}")
                self.enable_semantic = False

        return self._bge_model

    def compress(
        self,
        raw_log: str,
        fault_features: Dict = None,
        preserve_ratio: float = 0.6
    ) -> Dict[str, Any]:
        """
        Claude Code 风格的压缩

        Args:
            raw_log: 原始日志
            fault_features: 故障特征
            preserve_ratio: 初始保留比例

        Returns:
            压缩结果
        """
        if not raw_log:
            return self._empty_result()

        # 计算原始大小
        original_tokens = self.token_manager.calculate_tokens(raw_log)
        original_size_kb = len(raw_log.encode('utf-8')) / 1024

        logger.info(
            f"[ClaudeStyleCompressor] 开始压缩: "
            f"{original_tokens} tokens / {original_size_kb:.1f} KB"
        )

        # 解析日志行
        lines = raw_log.split('\n')

        # 步骤1: 为每行分配优先级和 token 计数
        line_tokens = self._analyze_and_prioritize(lines, fault_features or {})

        # 步骤2: 智能选择（参考 Claude Code 的选择策略）
        selected = self._intelligent_selection(line_tokens, preserve_ratio)

        # 步骤3: 添加上下文窗口
        extended = self._add_context_window(selected, len(lines))

        # 步骤4: 语义去重（如果启用）
        if self.enable_semantic:
            deduplicated = self._semantic_deduplication(lines, extended, fault_features or {})
        else:
            deduplicated = extended

        # 步骤5: 构建结果
        compressed_lines = [lines[i] for i in sorted(deduplicated)]
        compressed_log = '\n'.join(compressed_lines)

        # 统计
        compressed_tokens = self.token_manager.calculate_tokens(compressed_log)
        compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 0

        # 按优先级统计
        priority_stats = self._count_by_priority(lines, deduplicated, line_tokens)

        logger.info(
            f"[ClaudeStyleCompressor] 压缩完成: "
            f"{original_tokens} -> {compressed_tokens} tokens "
            f"({compression_ratio:.1%}), "
            f"保留: {priority_stats}"
        )

        return {
            "compressed_log": compressed_log,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_ratio": compression_ratio,
            "priority_stats": priority_stats,
            "metadata": {
                "original_lines": len(lines),
                "compressed_lines": len(compressed_lines),
                "method": "claude_style_semantic" if self.enable_semantic else "claude_style_rule"
            }
        }

    def _analyze_and_prioritize(
        self,
        lines: List[str],
        fault_features: Dict
    ) -> List[Dict]:
        """
        分析每行并分配优先级

        返回每行的信息：
        {
            'index': int,
            'content': str,
            'priority': Priority,
            'tokens': int,
            'is_critical': bool,
            'is_noise': bool,
            'semantic_score': float,
            'match_patterns': List[str]
        }
        """
        line_info = []

        # 获取查询向量（如果启用语义）
        query_embedding = None
        if self.enable_semantic:
            query_embedding = self._get_query_embedding(fault_features)

        # 批量计算 embedding（如果启用）
        line_embeddings = None
        if self.enable_semantic and query_embedding is not None:
            line_embeddings = self._batch_encode_lines(lines)

        for idx, line in enumerate(lines):
            info = {
                'index': idx,
                'content': line,
                'priority': Priority.LOW,
                'tokens': self.token_manager.calculate_tokens(line),
                'is_critical': False,
                'is_noise': False,
                'semantic_score': 0.0,
                'match_patterns': []
            }

            # 检查关键模式
            for regex, pattern_name in self.critical_regex:
                if regex.search(line):
                    info['priority'] = Priority.CRITICAL
                    info['is_critical'] = True
                    info['match_patterns'].append(pattern_name)
                    break  # 找到一个关键模式就够了

            # 如果不是关键，检查高价值模式
            if info['priority'] == Priority.LOW:
                for regex, pattern_name in self.high_value_regex:
                    if regex.search(line):
                        info['priority'] = Priority.HIGH
                        info['match_patterns'].append(pattern_name)
                        break

            # 检查噪音
            if any(regex.search(line) for regex in self.noise_regex):
                info['is_noise'] = True
                if info['priority'] == Priority.LOW:
                    info['priority'] = Priority.MINIMAL

            # 计算语义分数（如果启用）
            if self.enable_semantic and line_embeddings is not None and idx < len(line_embeddings):
                if query_embedding is not None:
                    similarity = float(np.dot(line_embeddings[idx], query_embedding))
                    info['semantic_score'] = similarity

                    # 语义分数可以提升优先级
                    if similarity > self.similarity_threshold and info['priority'] <= Priority.MEDIUM:
                        info['priority'] = Priority.MEDIUM
                elif info['is_critical']:
                    # 关键行也要有合理的语义分数
                    info['semantic_score'] = 1.0

            line_info.append(info)

        return line_info

    def _intelligent_selection(
        self,
        line_tokens: List[Dict],
        preserve_ratio: float = 0.6
    ) -> Set[int]:
        """
        智能选择要保留的行

        参考 Claude Code 的策略：
        1. 优先级是主要考虑因素
        2. 在相同优先级内，考虑语义分数
        3. 确保高优先级内容全部保留
        4. 对于低优先级内容，使用预算管理
        """
        # 按优先级分组
        by_priority: Dict[Priority, List[int]] = {p: [] for p in Priority}
        for idx, info in enumerate(line_tokens):
            by_priority[info['priority']].append(idx)

        # 必须保留：CRITICAL 和 HIGH
        must_preserve = set(by_priority[Priority.CRITICAL] + by_priority[Priority.HIGH])

        # 剩余预算
        remaining_tokens = self.target_tokens - sum(
            line_tokens[idx]['tokens'] for idx in must_preserve
        )

        if remaining_tokens <= 0:
            logger.warning("[ClaudeStyleCompressor] 预算已用完，只保留关键内容")
            return must_preserve

        # 对于 MEDIUM 和 LOW，使用贪心算法
        candidates = by_priority[Priority.MEDIUM] + by_priority[Priority.LOW]

        # 按语义分数排序（降序）
        candidates_with_score = [
            (idx, line_tokens[idx]['semantic_score'], line_tokens[idx]['tokens'])
            for idx in candidates
        ]
        candidates_with_score.sort(key=lambda x: x[1], reverse=True)

        # 贪心选择
        selected = set(must_preserve)
        for idx, score, tokens in candidates_with_score:
            if tokens <= remaining_tokens:
                selected.add(idx)
                remaining_tokens -= tokens
            elif remaining_tokens > 0 and score > self.similarity_threshold:
                # 即使超出预算，高语义分数的行也要尝试保留
                selected.add(idx)
                remaining_tokens = max(0, remaining_tokens - tokens)

        return selected

    def _add_context_window(
        self,
        selected_indices: Set[int],
        total_lines: int,
        window_size: int = 2
    ) -> Set[int]:
        """添加上下文窗口"""
        extended = set(selected_indices)

        for idx in selected_indices:
            # 添加前后的上下文
            for offset in range(-window_size, window_size + 1):
                target_idx = idx + offset
                if 0 <= target_idx < total_lines:
                    extended.add(target_idx)

        return extended

    def _semantic_deduplication(
        self,
        lines: List[str],
        indices: Set[int],
        fault_features: Dict
    ) -> Set[int]:
        """语义去重"""
        if len(indices) <= 50 or not self.enable_semantic:
            return indices

        # 获取选中行的 embedding
        selected_list = [(i, lines[i]) for i in sorted(indices)]

        embeddings = []
        for idx, line in selected_list:
            try:
                emb = self.bge_model.encode(
                    line,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                embeddings.append((idx, emb))
            except Exception as e:
                logger.warning(f"[ClaudeStyleCompressor] 去重 embedding 失败: {e}")
                embeddings.append((idx, np.zeros(1024)))

        if not embeddings:
            return indices

        # 计算相似度矩阵
        idx_list = [e[0] for e in embeddings]
        emb_matrix = np.array([e[1] for e in embeddings])

        from sklearn.metrics.pairwise import cosine_similarity
        similarity_matrix = cosine_similarity(emb_matrix)

        # 聚类去重
        deduplicated = set()
        n_samples = len(idx_list)
        used = [False] * n_samples

        for i in range(n_samples):
            if used[i]:
                continue

            # 优先保留高优先级的
            deduplicated.add(idx_list[i])
            used[i] = True

            # 标记相似的
            for j in range(i + 1, n_samples):
                if not used[j] and similarity_matrix[i][j] > 0.95:
                    used[j] = True

        return deduplicated

    def _batch_encode_lines(self, lines: List[str]) -> np.ndarray:
        """批量编码日志行"""
        embeddings = []

        for line in lines:
            if line.strip():
                try:
                    emb = self.bge_model.encode(
                        line,
                        normalize_embeddings=True,
                        show_progress_bar=False
                    )
                    embeddings.append(emb)
                except Exception as e:
                    logger.warning(f"[ClaudeStyleCompressor] Embedding 失败: {e}")
                    embeddings.append(np.zeros(1024))
            else:
                embeddings.append(np.zeros(1024))

        return np.array(embeddings)

    def _get_query_embedding(self, fault_features: Dict) -> Optional[np.ndarray]:
        """获取故障特征的语义向量"""
        query_parts = []

        error_codes = fault_features.get('error_codes', [])
        if error_codes:
            query_parts.append(' '.join(error_codes[:10]))

        modules = fault_features.get('modules', [])
        if modules:
            query_parts.append(' '.join(modules))

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
            logger.warning(f"[ClaudeStyleCompressor] 查询 embedding 失败: {e}")
            return None

    def _count_by_priority(
        self,
        lines: List[str],
        selected_indices: Set[int],
        line_info: List[Dict]
    ) -> Dict[str, int]:
        """统计按优先级的保留数量"""
        stats = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }

        for idx in selected_indices:
            priority = line_info[idx]['priority']
            if priority >= Priority.CRITICAL:
                stats['critical'] += 1
            elif priority >= Priority.HIGH:
                stats['high'] += 1
            elif priority >= Priority.MEDIUM:
                stats['medium'] += 1
            else:
                stats['low'] += 1

        return stats

    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "compressed_log": "",
            "original_tokens": 0,
            "compressed_tokens": 0,
            "compression_ratio": 0.0,
            "priority_stats": {},
            "metadata": {"method": "empty"}
        }
