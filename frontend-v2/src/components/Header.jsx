import React from 'react';

export default function Header() {
  return (
    <div style={{ padding: '1.5rem 2rem 1rem' }}>
      <div style={{
        fontSize: '2.5rem',
        fontWeight: 700,
        color: '#ffffff',
        marginBottom: '0.5rem',
        letterSpacing: '-0.5px',
        lineHeight: '1.2',
        textShadow: '0 0 30px rgba(0, 212, 255, 0.5)',
        position: 'relative',
        zIndex: 1
      }}>
        🔬 芯片失效分析AI Agent系统
      </div>
      <div style={{
        fontSize: '1rem',
        color: '#00d4ff',
        marginBottom: '2rem',
        fontWeight: 500,
        letterSpacing: '0.5px',
        textShadow: '0 0 10px rgba(0, 212, 255, 0.3)',
        position: 'relative',
        zIndex: 1,
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        企业级智能故障诊断与分析平台
        <span style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: '#10b981',
          boxShadow: '0 0 10px rgba(16, 185, 129, 0.8)'
        }} />
        API在线
      </div>
    </div>
  );
}
