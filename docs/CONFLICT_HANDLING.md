# 多轮对话中的冲突处理策略

> 创建时间：2026-02-22
> 状态：设计方案补充

---

## 一、冲突类型分类

### 1.1 直接冲突
```
用户第1条: "芯片型号: XC9000"
用户第3条: "芯片型号: XC8000"

同一字段出现不同值
```

### 1.2 间接冲突
```
用户第1条: "错误码: 0x1001 (内存错误)"
用户第3条: "错误码: 0x2001 (CPU错误)"

错误码不同，导致失效域判断冲突
```

### 1.3 时序冲突
```
用户第1条: "故障发生在10:00"
用户第3条: "故障发生在14:00"

时间信息不一致
```

### 1.4 因果冲突
```
用户第1条: "电压正常"
用户第3条: "电压降到了0.8V导致故障"

前后的因果关系不一致
```

---

## 二、冲突检测机制

### 2.1 实时检测（在增量特征提取时）

```python
# src/agents/conflict_detector.py

class ConflictDetector:
    """冲突检测器"""

    def __init__(self):
        # 定义冲突规则
        self.conflict_rules = {
            "chip_model": {
                "type": "single_value",
                "priority": "latest",  # latest | first | confirm
                "confirm_threshold": 0.5  # 相似度阈值
            },
            "error_codes": {
                "type": "multi_value",
                "merge_strategy": "union"  # union | replace | confirm
            },
            "timestamps": {
                "type": "range",
                "tolerance": 300  # 允许5分钟误差
            }
        }

    async def detect_conflicts(
        self,
        existing_context: Dict,
        new_input: Dict,
        new_input_features: Dict
    ) -> List[ConflictInfo]:
        """
        检测新输入与现有上下文的冲突

        返回: ConflictInfo列表
        """
        conflicts = []

        # 1. 检测芯片型号冲突
        if "chip_model" in existing_context:
            existing_model = existing_context["chip_model"]
            new_model = new_input_features.get("chip_model")

            if new_model and new_model != existing_model:
                conflicts.append(ConflictInfo(
                    type="direct",
                    field="chip_model",
                    existing_value=existing_model,
                    new_value=new_model,
                    severity="high",
                    suggestion="confirm"
                ))

        # 2. 检测错误码冲突
        existing_codes = set(existing_context.get("error_codes", []))
        new_codes = set(new_input_features.get("error_codes", []))

        # 检查是否有互斥的错误码
        mutually_exclusive = self._check_mutually_exclusive(
            existing_codes, new_codes
        )
        if mutually_exclusive:
            conflicts.append(ConflictInfo(
                type="indirect",
                field="error_codes",
                existing_value=list(existing_codes),
                new_value=list(new_codes),
                severity="medium",
                suggestion="merge"
            ))

        # 3. 检测时间冲突
        existing_time = existing_context.get("fault_time")
        new_time = new_input_features.get("fault_time")

        if existing_time and new_time:
            time_diff = abs(existing_time - new_time)
            if time_diff > self.conflict_rules["timestamps"]["tolerance"]:
                conflicts.append(ConflictInfo(
                    type="temporal",
                    field="fault_time",
                    existing_value=existing_time,
                    new_value=new_time,
                    severity="low",
                    suggestion="range"
                ))

        return conflicts

    def _check_mutually_exclusive(
        self,
        set1: Set[str],
        set2: Set[str]
    ) -> bool:
        """检查两组错误码是否互斥"""
        # 定义互斥规则
        exclusive_groups = {
            "memory": {"cpu": set1, "gpu": set2},
            # ...
        }
        # 实现检测逻辑
        return False
```

### 2.2 冲突信息模型

```python
# src/api/schemas.py

class ConflictInfo(BaseModel):
    """冲突信息"""
    type: str  # direct | indirect | temporal | causal
    field: str
    existing_value: Any
    new_value: Any
    severity: str  # high | medium | low
    suggestion: str  # confirm | merge | replace | ignore
    detected_at: datetime = Field(default_factory=datetime.utcnow)

class ConflictResolution(BaseModel):
    """冲突解决方案"""
    conflict_id: str
    resolution: str  # use_existing | use_new | merge | manual
    resolved_value: Optional[Any] = None
    reason: Optional[str] = None
```

---

## 三、冲突处理策略

### 3.1 自动处理规则

| 冲突类型 | 严重程度 | 默认策略 | 说明 |
|---------|---------|---------|------|
| 芯片型号 | 高 | 询问用户 | 必须确认 |
| 错误码 | 中 | 合并 | 取并集 |
| 时间戳 | 低 | 取范围 | 记录时间区间 |
| 故障现象 | 中 | 追加 | 都保留 |

### 3.2 用户确认流程

```python
# src/agents/conflict_resolver.py

class ConflictResolver:
    """冲突解决器"""

    async def resolve_with_user(
        self,
        conflicts: List[ConflictInfo],
        session_id: str
    ) -> Dict[str, Any]:
        """
        处理冲突，需要用户确认的返回询问
        """
        auto_resolved = {}
        needs_confirmation = []

        for conflict in conflicts:
            if conflict.severity == "low":
                # 低严重度自动处理
                auto_resolved[conflict.field] = self._auto_resolve(conflict)
            else:
                # 高严重度需要用户确认
                needs_confirmation.append(conflict)

        if needs_confirmation:
            # 返回需要确认的冲突
            return {
                "status": "needs_confirmation",
                "conflicts": needs_confirmation,
                "auto_resolved": auto_resolved,
                "message": f"检测到{len(needs_confirmation)}处信息冲突，请确认"
            }
        else:
            # 全部自动解决
            return {
                "status": "resolved",
                "resolutions": auto_resolved,
                "message": "信息冲突已自动处理"
            }

    def _auto_resolve(self, conflict: ConflictInfo) -> Any:
        """自动解决冲突"""
        if conflict.suggestion == "merge":
            # 合并策略
            if isinstance(conflict.existing_value, list):
                return list(set(conflict.existing_value + conflict.new_value))
        elif conflict.suggestion == "latest":
            # 使用最新值
            return conflict.new_value
        elif conflict.suggestion == "range":
            # 使用范围
            return {
                "min": min(conflict.existing_value, conflict.new_value),
                "max": max(conflict.existing_value, conflict.new_value)
            }
        return conflict.existing_value
```

---

## 四、前端UI设计

### 4.1 冲突提示组件

```jsx
// src/components/ConflictDialog.jsx

export default function ConflictDialog({ conflicts, onResolve }) {
  return (
    <div className="conflict-dialog">
      <h3>⚠️ 检测到信息冲突</h3>
      <p>系统检测到{conflicts.length}处信息可能存在冲突，请确认：</p>

      {conflicts.map((conflict) => (
        <ConflictCard
          key={conflict.conflict_id}
          conflict={conflict}
          onSelect={(resolution) => onResolve(conflict, resolution)}
        />
      ))}
    </div>
  );
}

function ConflictCard({ conflict, onSelect }) {
  return (
    <div className={`conflict-card ${conflict.severity}`}>
      <div className="conflict-header">
        <span className="conflict-type">{conflict.field}</span>
        <span className={`severity-badge ${conflict.severity}`}>
          {conflict.severity === 'high' ? '高' :
           conflict.severity === 'medium' ? '中' : '低'}
        </span>
      </div>

      <div className="conflict-content">
        <div className="conflict-side">
          <label>之前的信息:</label>
          <div className="value">{formatValue(conflict.existing_value)}</div>
        </div>

        <div className="conflict-divider">vs</div>

        <div className="conflict-side">
          <label>新的信息:</label>
          <div className="value">{formatValue(conflict.new_value)}</div>
        </div>
      </div>

      <div className="conflict-actions">
        <button onClick={() => onSelect('use_existing')}>
          使用之前的信息
        </button>
        <button onClick={() => onSelect('use_new')}>
          使用新的信息
        </button>
        {conflict.suggestion === 'merge' && (
          <button onClick={() => onSelect('merge')}>
            合并两者
          </button>
        )}
      </div>
    </div>
  );
}
```

### 4.2 信息源追踪

```jsx
// 在消息气泡中显示信息来源

function MessageBubble({ message }) {
  return (
    <div className="message-bubble">
      <div className="message-header">
        <span>👤 用户</span>
        <span>{formatTime(message.created_at)}</span>
      </div>

      <div className="message-content">{message.content}</div>

      {/* 显示此消息提供了哪些信息 */}
      <div className="info-contributions">
        <span>📋 提供了:</span>
        {message.metadata.fields.map((field) => (
          <InfoTag key={field} field={field} />
        ))}
      </div>

      {/* 如果此信息被后续纠正，显示标记 */}
      {message.is_corrected && (
        <div className="corrected-badge">已被纠正</div>
      )}
    </div>
  );
}
```

---

## 五、增强的数据模型

### 5.1 扩展消息表

```sql
-- 添加字段追踪信息来源和状态
ALTER TABLE analysis_messages ADD COLUMN IF NOT EXISTS:
    extracted_fields JSONB,          -- 从此消息提取的字段
    is_conflicted BOOLEAN DEFAULT FALSE,
    is_superseded BOOLEAN DEFAULT FALSE,
    superseded_by BIGINT,             -- 被哪条消息替代
    confidence_score FLOAT,           -- 信息的置信度
```

### 5.2 添加冲突记录表

```sql
CREATE TABLE analysis_conflicts (
    conflict_id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    conflict_type VARCHAR(50) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    existing_message_id BIGINT NOT NULL,
    new_message_id BIGINT NOT NULL,
    existing_value JSONB,
    new_value JSONB,
    severity VARCHAR(20) NOT NULL,
    resolution VARCHAR(50),           -- 如何解决
    resolved_value JSONB,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES analysis_results(session_id),
    FOREIGN KEY (existing_message_id) REFERENCES analysis_messages(message_id),
    FOREIGN KEY (new_message_id) REFERENCES analysis_messages(message_id)
);
```

---

## 六、处理流程图

```
用户输入新信息
      ↓
提取特征
      ↓
检测冲突 → 无冲突 → 直接添加到上下文
      ↓
    有冲突
      ↓
┌─────────────────────┐
│ 评估冲突严重程度     │
└─────────────────────┘
      ↓
   高严重度? ──是──→ 提示用户确认
      │                  ↓
      否            用户选择解决方案
      │                  ↓
      │            更新上下文
      ↓                  ↓
   自动处理 ←─────────────┘
      ↓
   触发重新分析
```

---

## 七、实现优先级

| 功能 | 优先级 | 复杂度 | 预计工作量 |
|------|--------|--------|------------|
| 基本冲突检测 | 高 | 中 | 2天 |
| 用户确认UI | 高 | 中 | 2天 |
| 冲突记录存储 | 中 | 低 | 1天 |
| 信息来源追踪 | 中 | 中 | 1天 |
| 智能冲突解决 | 低 | 高 | 3天 |

---

## 八、使用示例

```
场景：芯片型号冲突

用户: [输入] "芯片XC9000出现内存错误"
系统: → 提取 chip_model: XC9000
     → 分析完成

用户: [输入] "抱歉，我看错了，实际是XC8000"
系统: → 检测到chip_model冲突
     → 显示确认对话框

┌─────────────────────────────────┐
│ ⚠️ 检测到信息冲突               │
├─────────────────────────────────┤
│ 字段: 芯片型号                  │
│                                 │
│ 之前的信息: XC9000              │
│ 新的信息:   XC8000              │
│                                 │
│ ○ 使用之前的信息 (XC9000)       │
│ ● 使用新的信息 (XC8000)         │
│                                 │
│ [确认选择]                      │
└─────────────────────────────────┘

用户: 选择"使用新的信息"
系统: → 更新上下文 chip_model: XC8000
     → 重新基于XC8000分析
     → 返回新结果
```
