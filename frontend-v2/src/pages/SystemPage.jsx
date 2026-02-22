import React from 'react';

const supportedChips = [
  { model: 'XC9000', process: '7nm', arch: 'ARMv9', desc: '高性能服务��处理器' },
  { model: 'XC8000', process: '12nm', arch: 'ARMv8', desc: '标准企业级处理器' },
  { model: 'XC7000', process: '14nm', arch: 'ARMv8', desc: '入门级企业处理器' },
  { model: 'XC6000', process: '16nm', arch: 'ARMv8', desc: '嵌入式应用处理器' },
];

const supportedModules = [
  { name: '计算子系��', icon: '🧮', desc: 'CPU核心、执行单元、流水线' },
  { name: '内存子系统', icon: '💾', desc: 'DDR控制器、PHY、训练序列' },
  { name: '缓存子系统', icon: '🗄️', desc: 'L1/L2/L3缓存、ECC、一致性' },
  { name: '互连子系统', icon: '🔗', desc: 'NoC路由、交叉开关、DMA' },
];

export default function SystemPage() {
  return (
    <div>
      {/* 头部 */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{
          fontSize: '1.75rem',
          fontWeight: 700,
          color: '#ffffff',
          marginBottom: '0.5rem'
        }}>
          ⚙️ 系统信息
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
          平台能力和系统状态
        </p>
      </div>

      {/* 系统状态 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '1rem',
        marginBottom: '1.5rem'
      }}>
        <div className="status-card status-card-success" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#ffffff' }}>API服务器</h3>
            <span style={{ width: '16px', height: '16px', borderRadius: '50%', background: '#10b981' }}>✓</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>http://localhost:8889</p>
          <p style={{ fontSize: '0.8125rem', fontWeight: '600', color: '#10b981', marginTop: '0.25rem' }}>在线</p>
        </div>

        <div className="status-card status-card-success" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#ffffff' }}>数据库</h3>
            <span style={{ width: '16px', height: '16px', borderRadius: '50%', background: '#10b981' }}>✓</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>PostgreSQL + Neo4j</p>
          <p style={{ fontSize: '0.8125rem', fontWeight: '600', color: '#10b981', marginTop: '0.25rem' }}>在线</p>
        </div>

        <div className="status-card status-card-success" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#ffffff' }}>LLM服务</h3>
            <span style={{ width: '16px', height: '16px', borderRadius: '50%', background: '#10b981' }}>✓</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>GLM-4.7 / Claude</p>
          <p style={{ fontSize: '0.8125rem', fontWeight: '600', color: '#10b981', marginTop: '0.25rem' }}>在线</p>
        </div>
      </div>

      {/* 支持的模块 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{
          fontSize: '1.125rem',
          fontWeight: 'bold',
          color: '#ffffff',
          marginBottom: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          📦 支持的模块
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
          {supportedModules.map((module) => (
            <div
              key={module.name}
              style={{
                padding: '1rem',
                background: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem'
              }}
            >
              <span style={{ fontSize: '1.5rem' }}>{module.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.9375rem', fontWeight: '600', color: '#ffffff', marginBottom: '0.25rem' }}>
                  {module.name}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  {module.desc}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 支持的芯片 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{
          fontSize: '1.125rem',
          fontWeight: 'bold',
          color: '#ffffff',
          marginBottom: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          💻 支持的芯片
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
          {supportedChips.map((chip) => (
            <div
              key={chip.model}
              style={{
                padding: '1.25rem',
                background: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '12px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <h3 style={{
                  fontSize: '1.25rem',
                  fontWeight: 'bold',
                  fontFamily: 'monospace',
                  color: '#00d4ff'
                }}>
                  {chip.model}
                </h3>
                <span style={{
                  padding: '4px 10px',
                  backgroundColor: 'rgba(16, 185, 129, 0.2)',
                  border: '1px solid #10b981',
                  color: '#10b981',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: '600',
                  fontFamily: 'monospace'
                }}>
                  生产环境
                </span>
              </div>

              <p style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '0.5rem' }}>
                {chip.desc}
              </p>

              <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#64748b' }}>
                <span>{chip.process}</span>
                <span>{chip.arch}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 系统详情 */}
      <div className="card">
        <h2 style={{
          fontSize: '1.125rem',
          fontWeight: 'bold',
          color: '#ffffff',
          marginBottom: '1.25rem'
        }}>
          🔧 系统详情
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {[
            { label: '系统版本', value: '企业版 v2.0.0' },
            { label: 'Agent引擎', value: 'LangGraph v1.0.8' },
            { label: '知识库', value: 'Neo4j v5.x' },
            { label: '向量存储', value: 'pgvector with PostgreSQL' },
            { label: '缓存层', value: 'Redis v7.x' },
            { label: 'LLM提供商', value: 'OpenAI GPT-4, Anthropic Claude' },
            { label: '最大日志大小', value: '10MB' },
            { label: '分析超时', value: '60秒' },
          ].map((item) => (
            <div
              key={item.label}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '0.75rem 0',
                borderBottom: '1px solid #1e293b',
                fontSize: '0.875rem'
              }}
            >
              <span style={{ color: '#64748b' }}>{item.label}</span>
              <span style={{ fontFamily: 'monospace', color: '#e2e8f0' }}>{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
