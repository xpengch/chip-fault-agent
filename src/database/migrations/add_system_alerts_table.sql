-- 创建系统告警表
CREATE TABLE IF NOT EXISTS system_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_id VARCHAR(100) UNIQUE NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_system_alerts_type ON system_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_system_alerts_severity ON system_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_system_alerts_created ON system_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_system_alerts_resolved ON system_alerts(resolved);

-- 添加注���
COMMENT ON TABLE system_alerts IS '系统告警表 - 存储系统监控告警';
COMMENT ON COLUMN system_alerts.alert_id IS '告警唯一标识';
COMMENT ON COLUMN system_alerts.alert_type IS '告警类型 (embedding_api_failed, knowledge_graph_failed, etc.)';
COMMENT ON COLUMN system_alerts.severity IS '严重程度 (info, warning, error, critical)';
COMMENT ON COLUMN system_alerts.resolved IS '是否已解决';
