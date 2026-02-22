import React from 'react';
import { useNavigate } from 'react-router-dom';

const CHIP_MODELS = ['XC9000', 'XC8000', 'XC7000', 'XC6000', '自定义型号'];
const PAGES = [
  { id: '日志分析', label: '📋 日志分析', path: '/analyze' },
  { id: '历史记录', label: '📜 历史记录', path: '/history' },
  { id: '案例库', label: '📚 案例库', path: '/cases' },
  { id: '系统信息', label: '⚙️ 系统信息', path: '/system' },
];

export default function Sidebar({
  apiUrl,
  setApiUrl,
  chipModel,
  setChipModel,
  customChipModel,
  setCustomChipModel,
  inferThreshold,
  setInferThreshold,
  currentPage,
  onPageChange,
  apiStatus,
  onCheckApi
}) {
  const navigate = useNavigate();

  const handlePageClick = (page) => {
    onPageChange(page.label);
    const pageData = PAGES.find(p => p.id === page.id);
    if (pageData) {
      navigate(pageData.path);
    }
  };

  return (
    <div style={{
      width: '280px',
      background: 'linear-gradient(180deg, #0a0f1a 0%, #0f172a 100%)',
      borderRight: '1px solid rgba(0, 212, 255, 0.1)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'auto',
      position: 'relative',
      zIndex: 2
    }}>
      {/* Logo区域 */}
      <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
        <div style={{
          width: '60px',
          height: '60px',
          margin: '0 auto 1rem',
          background: 'linear-gradient(135deg, #00d4ff 0%, #0066cc 100%)',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 20px rgba(0, 212, 255, 0.4)',
          fontSize: '2rem'
        }}>
          🔬
        </div>
        <div style={{
          fontSize: '1.125rem',
          fontWeight: 700,
          color: '#ffffff',
          marginBottom: '0.25rem'
        }}>
          Chip Fault AI
        </div>
        <div style={{ fontSize: '0.75rem', color: '#00d4ff' }}>
          Enterprise Edition v2.0
        </div>
      </div>

      {/* 分隔线 */}
      <div className="tech-divider" style={{ margin: '0 1rem' }} />

      {/* API配置 */}
      <div style={{ padding: '1.5rem 1rem 0.5rem' }}>
        <div style={{
          fontSize: '0.75rem',
          fontWeight: 600,
          color: '#00d4ff',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginBottom: '0.75rem'
        }}>
          🔌 API配置
        </div>
        <input
          type="text"
          value={apiUrl}
          onChange={(e) => setApiUrl(e.target.value)}
          className="input"
          placeholder="API地址"
          style={{ fontSize: '0.875rem' }}
        />
      </div>

      {/* 芯片配置 */}
      <div style={{ padding: '1.5rem 1rem 0.5rem' }}>
        <div style={{
          fontSize: '0.75rem',
          fontWeight: 600,
          color: '#00d4ff',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginBottom: '0.75rem'
        }}>
          💼 芯片配置
        </div>
        <select
          value={chipModel}
          onChange={(e) => setChipModel(e.target.value)}
          className="select"
          style={{ marginBottom: chipModel === '自定义型号' ? '0.75rem' : 0 }}
        >
          {CHIP_MODELS.map(model => (
            <option key={model} value={model}>{model}</option>
          ))}
        </select>
        {chipModel === '自定义型号' && (
          <input
            type="text"
            value={customChipModel}
            onChange={(e) => setCustomChipModel(e.target.value)}
            className="input"
            placeholder="例如: XC5000"
            style={{ fontSize: '0.875rem' }}
          />
        )}
      </div>

      {/* 分析参数 */}
      <div style={{ padding: '1.5rem 1rem 0.5rem' }}>
        <div style={{
          fontSize: '0.75rem',
          fontWeight: 600,
          color: '#00d4ff',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginBottom: '0.75rem'
        }}>
          ⚙️ 分析参数
        </div>
        <div style={{ marginBottom: '0.5rem' }}>
          <div style={{
            fontSize: '0.875rem',
            color: '#94a3b8',
            marginBottom: '0.5rem'
          }}>
            置信度阈值: {inferThreshold.toFixed(2)}
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={inferThreshold}
            onChange={(e) => setInferThreshold(parseFloat(e.target.value))}
            style={{
              width: '100%',
              height: '6px',
              borderRadius: '3px',
              background: 'rgba(0, 212, 255, 0.2)',
              outline: 'none',
              WebkitAppearance: 'none'
            }}
          />
        </div>
      </div>

      {/* 系统状态 */}
      <div style={{ padding: '1.5rem 1rem 0.5rem' }}>
        <div style={{
          fontSize: '0.75rem',
          fontWeight: 600,
          color: '#00d4ff',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginBottom: '0.75rem'
        }}>
          📊 系统状态
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={onCheckApi}
            className="btn-secondary"
            style={{ flex: 1, fontSize: '0.875rem', padding: '0.5rem' }}
          >
            检查
          </button>
          <button
            onClick={() => window.location.reload()}
            className="btn-secondary"
            style={{ flex: 1, fontSize: '0.875rem', padding: '0.5rem' }}
          >
            刷新
          </button>
        </div>
        {apiStatus !== 'unknown' && (
          <div style={{
            marginTop: '0.75rem',
            padding: '0.5rem',
            borderRadius: '6px',
            fontSize: '0.875rem',
            textAlign: 'center',
            background: apiStatus === 'online'
              ? 'rgba(16, 185, 129, 0.15)'
              : 'rgba(239, 68, 68, 0.15)',
            color: apiStatus === 'online' ? '#10b981' : '#ef4444',
            border: `1px solid ${apiStatus === 'online' ? '#10b981' : '#ef4444'}`
          }}>
            {apiStatus === 'online' ? '✓ 在线' : '✗ 离线'}
          </div>
        )}
      </div>

      {/* 分隔线 */}
      <div className="tech-divider" style={{ margin: '1.5rem 1rem' }} />

      {/* 导航菜单 */}
      <div style={{ padding: '0 1rem 1.5rem' }}>
        {PAGES.map((page) => {
          const isActive = page.id === currentPage;
          return (
            <button
              key={page.id}
              onClick={() => handlePageClick(page)}
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                marginBottom: '0.5rem',
                background: isActive ? 'rgba(0, 212, 255, 0.2)' : 'transparent',
                border: isActive ? '1px solid #00d4ff' : '1px solid transparent',
                borderRadius: '8px',
                color: isActive ? '#00d4ff' : '#94a3b8',
                fontSize: '0.875rem',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                textAlign: 'left'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.target.style.background = 'rgba(30, 41, 59, 0.5)';
                  e.target.style.borderColor = '#334155';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.target.style.background = 'transparent';
                  e.target.style.borderColor = 'transparent';
                }
              }}
            >
              {page.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
