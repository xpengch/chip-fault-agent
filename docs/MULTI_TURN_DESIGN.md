# 多轮对话与信息补充功能设计方案

> 创建时间：2026-02-22
> 状态：待实施

---

## 一、需求概述

### 1.1 核心需求
用户希望系统能够：
- **多次补充信息**：在一次分析会话中，用户可以分多次提供补充信息
- **累积分析**：系统基于所有历史输入的累积信息进行分析
- **信息纠正**：用户��以对之前输入的错误信息进行纠正
- **交互历史**：展示完整的交互历史和每次输入对应的分析结果

### 1.2 使用场景
```
场景1: 渐进式信息提供
用户: "芯片XC9000出现故障"
系统: 初步分析 → 请提供更多日志信息
用户: [补充日志] "ERROR: Memory access violation at 0x8000"
系统: 深入分析 → 确定失效域为memory
用户: [补充日志] "Temperature: 95°C, Voltage: 1.1V"
系统: 更新分析 → 结合温度和电压信息，推断根因

场景2: 信息纠正
用户: "芯片型号XC9000，错误码0x1234"
系统: 分析结果...
用户: "纠正：芯片型号实际是XC8000，错误码是0x5678"
系统: 重新分析，展示修正后的结果
```

---

## 二、系统架构设计

### 2.1 数据模型扩展

#### 2.1.1 新增数据表

```sql
-- 用户交互消息表
CREATE TABLE analysis_messages (
    message_id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(50) NOT NULL,  -- 'user_input', 'correction', 'system_response', 'analysis_result'
    sequence_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50),  -- 'text', 'log', 'correction_data'
    metadata JSONB,  -- 存储结构化数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_correction BOOLEAN DEFAULT FALSE,
    corrected_message_id BIGINT REFERENCES analysis_messages(message_id),
    FOREIGN KEY (session_id) REFERENCES analysis_results(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_analysis_messages_session ON analysis_messages(session_id);
CREATE INDEX idx_analysis_messages_sequence ON analysis_messages(session_id, sequence_number);

-- 信息快照表 (存储每次分析时的信息累积状态)
CREATE TABLE analysis_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message_id BIGINT NOT NULL,  -- 关联到触发的消息
    accumulated_context JSONB NOT NULL,  -- 累积的所有信息
    analysis_result JSONB NOT NULL,  -- 该次分析结果
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES analysis_results(session_id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES analysis_messages(message_id)
);
```

#### 2.1.2 扩展现有模型

```python
# src/database/models.py

class AnalysisMessage(Base):
    """用户交互消息"""
    __tablename__ = "analysis_messages"

    message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255))
    message_type: Mapped[str] = mapped_column(String(50))  # user_input, correction, system_response, analysis_result
    sequence_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[Optional[str]] = mapped_column(String(50))  # text, log, correction_data
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_correction: Mapped[bool] = mapped_column(Boolean, default=False)
    corrected_message_id: Mapped[Optional[int]] = mapped_column(BigInteger)

class AnalysisSnapshot(Base):
    """分析快照"""
    __tablename__ = "analysis_snapshots"

    snapshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255))
    message_id: Mapped[int] = mapped_column(BigInteger)
    accumulated_context: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    analysis_result: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### 2.2 API接口设计

#### 2.2.1 新增接口

```python
# src/api/multi_turn_routes.py

@router.post("/api/v1/analysis/{session_id}/message")
async def add_message(
    session_id: str,
    request: MessageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    添加用户消息并触发分析

    请求体:
    {
        "content": "补充的日志信息",
        "content_type": "log",  // text | log | correction
        "correction_target": null,  // 如果是纠正，指定要纠正的消息ID
        "metadata": {}  // 可选的结构化数据
    }
    """
    pass

@router.get("/api/v1/analysis/{session_id}/messages")
async def get_conversation(session_id: str):
    """获取会话的完整对话历史"""
    pass

@router.post("/api/v1/analysis/{session_id}/correct")
async def correct_information(
    session_id: str,
    request: CorrectionRequest
):
    """
    纠正之前输入的信息

    请求体:
    {
        "target_message_id": 123,
        "corrected_content": "纠正后的内容",
        "reason": "纠正原因"
    }
    """
    pass

@router.get("/api/v1/analysis/{session_id}/timeline")
async def get_analysis_timeline(session_id: str):
    """获取分析时间线（每次分析的结果变化）"""
    pass

@router.post("/api/v1/analysis/{session_id}/rollback")
async def rollback_to_message(
    session_id: str,
    request: RollbackRequest
):
    """回滚到指定消息状态（撤销后续所有操作）"""
    pass
```

#### 2.2.2 数据模型

```python
# src/api/schemas.py

class MessageRequest(BaseModel):
    content: str
    content_type: str = "text"  # text, log, correction
    correction_target: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class CorrectionRequest(BaseModel):
    target_message_id: int
    corrected_content: str
    reason: Optional[str] = None

class MessageResponse(BaseModel):
    message_id: int
    session_id: str
    message_type: str
    sequence_number: int
    content: str
    created_at: datetime
    is_correction: bool

class ConversationResponse(BaseModel):
    session_id: str
    messages: List[MessageResponse]
    current_analysis: Optional[AnalysisResult]
    total_messages: int

class TimelineEntry(BaseModel):
    snapshot_id: int
    sequence_number: int
    analysis_summary: Dict[str, Any]
    created_at: datetime
    confidence_change: Optional[float]

class RollbackRequest(BaseModel):
    to_message_id: int
    reason: Optional[str] = None
```

### 2.3 核心处理流程

#### 2.3.1 消息处理流程

```python
# src/agents/multi_turn_handler.py

class MultiTurnConversationHandler:
    """多轮对话处理器"""

    async def handle_user_message(
        self,
        session_id: str,
        content: str,
        content_type: str = "text",
        correction_target: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        处理用户消息的主流程
        """
        # 1. 获取会话上下文
        context = await self._get_conversation_context(session_id)

        # 2. 处理纠正消息
        if correction_target:
            context = await self._apply_correction(
                context,
                correction_target,
                content
            )

        # 3. 添加新消息到上下文
        context = await self._append_message(context, content, content_type)

        # 4. 触发重新分析
        analysis_result = await self._analyze_with_context(
            session_id,
            context
        )

        # 5. 保存快照
        await self._save_snapshot(session_id, context, analysis_result)

        # 6. 生成系统响应
        response = await self._generate_response(
            context,
            analysis_result
        )

        return {
            "success": True,
            "message_id": context["last_message_id"],
            "analysis_result": analysis_result,
            "system_response": response,
            "context_updated": True
        }

    async def _get_conversation_context(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """获取会话的累积上下文"""
        messages = await self.db.get_messages(session_id)

        # 构建累积上下文
        context = {
            "session_id": session_id,
            "messages": [],
            "accumulated_logs": [],
            "accumulated_features": {},
            "corrections": {},
            "last_sequence": 0
        }

        for msg in messages:
            if msg.is_correction and msg.corrected_message_id:
                # 记录纠正关系
                context["corrections"][msg.corrected_message_id] = msg
            elif not self._is_message_corrected(msg.message_id, context["corrections"]):
                # 累积未被纠正的消息内容
                context["messages"].append(msg)
                if msg.content_type == "log":
                    context["accumulated_logs"].append(msg.content)

            context["last_sequence"] = max(context["last_sequence"], msg.sequence_number)

        return context

    async def _apply_correction(
        self,
        context: Dict[str, Any],
        target_message_id: int,
        corrected_content: str
    ) -> Dict[str, Any]:
        """应用纠正到上下文"""
        # 1. 标记原消息被纠正
        # 2. 从累积信息中移除原内容
        # 3. 添加纠正后的内容
        pass

    async def _analyze_with_context(
        self,
        session_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于累积上下文进行分析"""
        # 1. 合并所有日志
        combined_log = "\n".join(context["accumulated_logs"])

        # 2. 提取累积特征
        accumulated_features = await self._extract_accumulated_features(context)

        # 3. 调用工作流分析
        workflow = get_workflow()
        result = await workflow.run(
            chip_model=context.get("chip_model", "XC9000"),
            raw_log=combined_log,
            session_id=session_id,
            user_id=context.get("user_id"),
            accumulated_features=accumulated_features,
            is_multi_turn=True
        )

        return result

    async def _generate_response(
        self,
        context: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> str:
        """生成系统响应"""
        # 基于分析结果生成对话式响应
        need_expert = analysis_result.get("need_expert", False)
        confidence = analysis_result.get("final_root_cause", {}).get("confidence", 0)

        if confidence < 0.5:
            return "当前信息不足以做出准确判断，请提供更多日志信息，如：错误码、寄存器值、时间戳等。"
        elif need_expert:
            return f"分析完成，置信度{confidence*100:.1f}%。由于置信度较低，建议专家介入确认。是否需要提供更多信息以提高分析准确性？"
        else:
            return f"分析完成，置信度{confidence*100:.1f}%。失效域为{analysis_result.get('final_root_cause', {}).get('failure_domain')}。如需补充信息，可继续提供。"
```

---

## 三、前端设计

### 3.1 UI组件结构

```jsx
// src/pages/MultiTurnAnalyzePage.jsx

export default function MultiTurnAnalyzePage() {
  const [messages, setMessages] = useState([]);  // 对话历史
  const [currentAnalysis, setCurrentAnalysis] = useState(null);  // 当前分析结果
  const [inputMode, setInputMode] = useState('append');  // append | correct
  const [targetMessage, setTargetMessage] = useState(null);  // 要纠正的消息

  return (
    <div className="multi-turn-container">
      {/* 左侧：对话区域 */}
      <ConversationPanel
        messages={messages}
        currentAnalysis={currentAnalysis}
        onCorrect={handleCorrect}
      />

      {/* 右侧：分析结果区域 */}
      <AnalysisResultPanel
        result={currentAnalysis}
        timeline={analysisTimeline}
      />

      {/* 底部：输入区域 */}
      <InputPanel
        mode={inputMode}
        targetMessage={targetMessage}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
```

### 3.2 消息展示组件

```jsx
// src/components/ConversationPanel.jsx

function ConversationPanel({ messages, currentAnalysis, onCorrect }) {
  return (
    <div className="conversation-panel">
      {messages.map((msg) => (
        <MessageBubble
          key={msg.message_id}
          message={msg}
          isCorrected={isMessageCorrected(msg.message_id)}
          onCorrect={onCorrect}
        />
      ))}

      {/* 系统分析结果消息 */}
      {currentAnalysis && (
        <AnalysisMessage result={currentAnalysis} />
      )}
    </div>
  );
}

function MessageBubble({ message, isCorrected, onCorrect }) {
  return (
    <div className={`message-bubble ${message.type} ${isCorrected ? 'corrected' : ''}`}>
      <div className="message-header">
        <span className="message-type">
          {message.type === 'user_input' ? '👤 用户' : '🤖 系统'}
        </span>
        <span className="message-time">
          {formatTime(message.created_at)}
        </span>
      </div>

      <div className="message-content">
        {message.content}
      </div>

      {isCorrected && (
        <div className="correction-badge">已被纠正</div>
      )}

      {message.type === 'user_input' && !isCorrected && (
        <button onClick={() => onCorrect(message)}>
          纠正
        </button>
      )}

      {message.is_correction && (
        <div className="correction-note">
          纠正了消息 #{message.corrected_message_id}
        </div>
      )}
    </div>
  );
}
```

### 3.3 输入面板组件

```jsx
// src/components/InputPanel.jsx

function InputPanel({ mode, targetMessage, onSubmit }) {
  const [content, setContent] = useState('');

  return (
    <div className="input-panel">
      {mode === 'correct' && (
        <div className="correction-mode">
          <span>正在纠正：</span>
          <div className="target-message">
            {targetMessage?.content}
          </div>
        </div>
      )}

      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={
          mode === 'correct'
            ? '输入纠正后的内容...'
            : '输入补充信息或日志...'
        }
      />

      <div className="input-actions">
        <button onClick={() => onSubmit({ content, mode })}>
          {mode === 'correct' ? '提交纠正' : '发送'}
        </button>
        {mode === 'correct' && (
          <button onClick={() => setMode('append')}>
            取消纠正
          </button>
        )}
      </div>
    </div>
  );
}
```

### 3.4 分析时间线组件

```jsx
// src/components/AnalysisTimeline.jsx

function AnalysisTimeline({ timeline }) {
  return (
    <div className="analysis-timeline">
      <h3>分析演进</h3>
      {timeline.map((entry, index) => (
        <TimelineEntry
          key={entry.snapshot_id}
          entry={entry}
          previous={timeline[index - 1]}
        />
      ))}
    </div>
  );
}

function TimelineEntry({ entry, previous }) {
  const confidenceChanged = previous && (
    entry.analysis_result.confidence !== previous.analysis_result.confidence
  );

  const domainChanged = previous && (
    entry.analysis_result.failure_domain !== previous.analysis_result.failure_domain
  );

  return (
    <div className="timeline-entry">
      <div className="entry-marker">
        <div className={`marker-dot ${confidenceChanged ? 'changed' : ''}`} />
      </div>

      <div className="entry-content">
        <div className="entry-time">
          {formatTime(entry.created_at)}
        </div>

        <div className="entry-summary">
          {domainChanged && (
            <span className="change-badge">
              失效域变更: {previous.analysis_result.failure_domain} → {entry.analysis_result.failure_domain}
            </span>
          )}

          <span className="confidence">
            置信度: {(entry.analysis_result.confidence * 100).toFixed(1)}%
            {confidenceChanged && (
              <span className="trend">
                {entry.analysis_result.confidence > previous.analysis_result.confidence ? '↑' : '↓'}
              </span>
            )}
          </span>
        </div>
      </div>
    </div>
  );
}
```

---

## 四、工作流扩展

### 4.1 修改现有工作流

```python
# src/agents/workflow.py

class AnalysisWorkflow:
    async def run(
        self,
        chip_model: str,
        raw_log: str,
        session_id: str,
        user_id: str,
        infer_threshold: float = 0.7,
        accumulated_features: Optional[Dict] = None,  # 新增
        is_multi_turn: bool = False  # 新增
    ) -> Dict[str, Any]:
        """
        执行分析工作流
        """
        # 如果是多轮对话，合并累积特征
        if is_multi_turn and accumulated_features:
            self._merge_accumulated_features(accumulated_features)

        # ... 原有分析逻辑 ...

        return result
```

### 4.2 增量特征提取

```python
# src/agents/incremental_processor.py

class IncrementalFeatureProcessor:
    """增量特征处理器"""

    async def process_new_input(
        self,
        new_input: str,
        existing_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理新输入，更新特征
        """
        # 1. 提取新输入的特征
        new_features = await self._extract_features(new_input)

        # 2. 合并到现有特征
        merged = self._merge_features(existing_features, new_features)

        # 3. 检测特征冲突
        conflicts = self._detect_conflicts(existing_features, new_features)

        # 4. 标记需要人工确认的冲突
        if conflicts:
            merged["conflicts"] = conflicts
            merged["need_confirmation"] = True

        return merged

    def _merge_features(
        self,
        existing: Dict,
        new: Dict
    ) -> Dict:
        """合并特征，处理数组类型的累积"""
        merged = existing.copy()

        # 数组类型合并（如错误码列表）
        for key, value in new.items():
            if isinstance(value, list) and key in merged:
                merged[key] = list(set(merged[key] + value))
            else:
                merged[key] = value

        return merged
```

---

## 五、实施计划

### 5.1 阶段划分

| 阶段 | 任务 | 优先级 | 预计工作量 |
|------|------|--------|------------|
| **Phase 1** | 数据库扩展 | 高 | 2天 |
| | - 创建新表 | | |
| | - 编写迁移脚本 | | |
| | - 扩展ORM模型 | | |
| **Phase 2** | 后端核心逻辑 | 高 | 3天 |
| | - 实现MultiTurnConversationHandler | | |
| | - 添加API路由 | | |
| | - 修改现有工作流支持累积特征 | | |
| **Phase 3** | 前端UI开发 | 中 | 3天 |
| | - 对话面板组件 | | |
| | - 输入面板组件 | | |
| | - 时间线组件 | | |
| **Phase 4** | 测试与优化 | 中 | 2天 |
| | - 单元测试 | | |
| | - 集成测试 | | |
| | - 性能优化 | | |

### 5.2 技术风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 上下文累积导致性能下降 | 高 | 设置消息数量上限，使用分页加载 |
| 纠正操作的数据一致性 | 高 | 使用事务确保原子性，添加版本控制 |
| 用户体验复杂度增加 | 中 | 提供清晰的UI引导，添加帮助提示 |
| 多轮对话的LLM token消耗 | 中 | 实现上下文压缩，只保留关键信息 |

---

## 六、数据示例

### 6.1 对话流程示例

```json
{
  "session_id": "session_20260222_abc123",
  "messages": [
    {
      "message_id": 1,
      "type": "user_input",
      "content": "芯片XC9000出现故障",
      "sequence": 1,
      "created_at": "2026-02-22T10:00:00Z"
    },
    {
      "message_id": 2,
      "type": "system_response",
      "content": "请提供更多日志信息，如错误码、故障现象等",
      "sequence": 2,
      "created_at": "2026-02-22T10:00:05Z"
    },
    {
      "message_id": 3,
      "type": "user_input",
      "content": "ERROR: Memory access violation at 0x8000",
      "content_type": "log",
      "sequence": 3,
      "created_at": "2026-02-22T10:01:00Z"
    },
    {
      "message_id": 4,
      "type": "analysis_result",
      "content": {
        "failure_domain": "memory",
        "confidence": 0.45,
        "need_expert": true
      },
      "sequence": 4,
      "created_at": "2026-02-22T10:01:10Z"
    },
    {
      "message_id": 5,
      "type": "correction",
      "content": "纠正：实际是CPU访问错误，不是Memory",
      "corrected_message_id": 3,
      "sequence": 5,
      "created_at": "2026-02-22T10:02:00Z"
    }
  ],
  "snapshots": [
    {
      "snapshot_id": 1,
      "message_id": 4,
      "accumulated_context": {
        "logs": ["ERROR: Memory access violation at 0x8000"],
        "features": {"error_codes": [], "modules": ["memory"]}
      },
      "analysis_result": {
        "failure_domain": "memory",
        "confidence": 0.45
      }
    }
  ]
}
```

---

## 七、后续优化方向

1. **智能提问引导**：系统根据当前分析状态，主动询问缺失的关键信息
2. **上下文压缩**：对长对话进行智能摘要，减少token消耗
3. **分支路径**：支持尝试性分析，用户可以选择不同分支
4. **模板化输入**：提供结构化输入模板，帮助用户规范提供信息
5. **协作分析**：支持多个用户/专家参与同一会话的分析

---

## 八、相关文件清单

### 需要创建的文件：
- `src/api/multi_turn_routes.py` - 多轮对话API路由
- `src/agents/multi_turn_handler.py` - 多轮对话处理器
- `src/agents/incremental_processor.py` - 增量特征处理器
- `src/database/multi_turn_models.py` - 数据模型定义
- `scripts/migrate_multi_turn.py` - 数据库迁移脚本
- `frontend-v2/src/pages/MultiTurnAnalyzePage.jsx` - 多轮分析页面
- `frontend-v2/src/components/ConversationPanel.jsx` - 对话面板
- `frontend-v2/src/components/InputPanel.jsx` - 输入面板
- `frontend-v2/src/components/AnalysisTimeline.jsx` - 分析时间线

### 需要修改的文件：
- `src/agents/workflow.py` - 支持累积特征
- `src/api/schemas.py` - 添加新的数据模型
- `src/database/connection.py` - 添加消息和快照的CRUD操作
- `frontend-v2/src/api.js` - 添加新的API调用方法
- `CHANGELOG.md` - 记录实施进度
