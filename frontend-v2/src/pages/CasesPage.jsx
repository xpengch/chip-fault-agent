import React, { useState, useEffect } from 'react';
import api from '../api';

const severityConfig = {
  critical: { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', label: '严重' },
  high: { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', label: '高' },
  medium: { color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', label: '中' },
  low: { color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', label: '低' },
};

const domainConfig = {
  compute: { color: '#a855f7', bg: 'rgba(168, 85, 247, 0.15)', label: '计算' },
  cache: { color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', label: '缓存' },
  memory: { color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', label: '内存' },
  interconnect: { color: '#ec4899', bg: 'rgba(236, 72, 153, 0.15)', label: '互连' },
};

export default function CasesPage() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedCase, setExpandedCase] = useState(null);
  const [chipFilter, setChipFilter] = useState('all');
  const [domainFilter, setDomainFilter] = useState('all');

  const fetchCases = async () => {
    setLoading(true);
    try {
      const result = await api.getCases();
      setCases(result.data || []);
    } catch (error) {
      console.error('获取案例库失败:', error);
      // 使用演示数据作为后备
      setCases([
        {
          id: 'CASE-001',
          chip_model: 'XC9000',
          failure_domain: 'compute',
          severity: 'critical',
          root_cause: 'CPU核心执行超时，由于L2缓存一致性失败',
          description: '在高负载条件下，CPU核心#3在访问共享L2缓存时经历执行超时。',
          solution: '应用微码更新v2.3.1，强制执行正确的内存屏障顺序。',
          error_code: '0XCO001',
          affected_modules: ['cpu', 'l2_cache'],
          verified: true,
        },
        {
          id: 'CASE-002',
          chip_model: 'XC9000',
          failure_domain: 'cache',
          severity: 'high',
          root_cause: 'L3缓存ECC多比特错误在bank 5',
          description: 'L3缓存bank 5在密集缓存操作期间经历不可纠正的ECC错误。',
          solution: '更换受影响的CPU模块。��排预防性维护。',
          error_code: '0XLA001',
          affected_modules: ['l3_cache'],
          verified: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const filteredCases = cases.filter(c => {
    if (chipFilter !== 'all' && c.chip_model !== chipFilter) return false;
    if (domainFilter !== 'all' && c.failure_domain !== domainFilter) return false;
    return true;
  });

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
          📚 案例库
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
          历史故障案例与已验证解决方案
        </p>
      </div>

      {/* 筛选区域 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.75rem',
              fontWeight: '600',
              color: '#94a3b8',
              marginBottom: '0.5rem',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              芯片型号
            </label>
            <select
              value={chipFilter}
              onChange={(e) => setChipFilter(e.target.value)}
              className="select"
              style={{ fontSize: '0.875rem' }}
            >
              <option value="all">全部型号</option>
              <option value="XC9000">XC9000</option>
              <option value="XC8000">XC8000</option>
              <option value="XC7000">XC7000</option>
            </select>
          </div>

          <div>
            <label style={{
              display: 'block',
              fontSize: '0.75rem',
              fontWeight: '600',
              color: '#94a3b8',
              marginBottom: '0.5rem',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              失效域
            </label>
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="select"
              style={{ fontSize: '0.875rem' }}
            >
              <option value="all">全部域</option>
              <option value="compute">计算</option>
              <option value="cache">缓存</option>
              <option value="memory">内存</option>
              <option value="interconnect">互连</option>
            </select>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'flex-end',
            fontSize: '0.875rem',
            color: '#94a3b8'
          }}>
            显示 <span style={{ color: '#00d4ff', margin: '0 4px', fontFamily: 'monospace' }}>{filteredCases.length}</span> 个案例
          </div>
        </div>
      </div>

      {/* 案例列表 */}
      {loading ? (
        <div style={{
          padding: '3rem',
          textAlign: 'center',
          color: '#64748b'
        }}>
          <div className="spinner" style={{ margin: '0 auto 1rem' }} />
          <div>加载中...</div>
        </div>
      ) : filteredCases.length === 0 ? (
        <div className="card" style={{
          padding: '3rem',
          textAlign: 'center',
          color: '#64748b'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
          <div>暂无案例</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {filteredCases.map((case_) => {
            const isExpanded = expandedCase === case_.id;
            const severity = severityConfig[case_.severity] || severityConfig.medium;
            const domain = domainConfig[case_.failure_domain] || { color: '#64748b', bg: 'rgba(100, 116, 139, 0.15)', label: '未知' };

            return (
              <div
                key={case_.id}
                className="card"
                style={{ padding: 0, margin: 0, overflow: 'hidden' }}
              >
                {/* 头部 */}
                <button
                  onClick={() => setExpandedCase(isExpanded ? null : case_.id)}
                  style={{
                    width: '100%',
                    padding: '1rem 1.25rem',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    textAlign: 'left',
                    color: 'inherit'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                        <span style={{
                          fontFamily: 'monospace',
                          color: '#00d4ff',
                          fontSize: '0.875rem',
                          fontWeight: '600'
                        }}>
                          {case_.chip_model}
                        </span>

                        <span style={{
                          padding: '4px 10px',
                          backgroundColor: domain.bg,
                          color: domain.color,
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: '600',
                          textTransform: 'uppercase',
                          border: `1px solid ${domain.color}`
                        }}>
                          {domain.label}
                        </span>

                        <span style={{
                          padding: '4px 10px',
                          backgroundColor: severity.bg,
                          color: severity.color,
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: '600',
                          textTransform: 'uppercase',
                          border: `1px solid ${severity.color}`
                        }}>
                          {severity.label}
                        </span>
                      </div>

                      <p style={{
                        fontSize: '0.9375rem',
                        fontWeight: '500',
                        color: '#f1f5f9',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {case_.root_cause}
                      </p>

                      {case_.error_code && (
                        <span style={{
                          fontSize: '0.75rem',
                          fontFamily: 'monospace',
                          color: '#64748b',
                          marginTop: '0.25rem',
                          display: 'inline-block'
                        }}>
                          {case_.error_code}
                        </span>
                      )}
                    </div>

                    <span style={{ color: '#94a3b8', fontSize: '1.25rem' }}>
                      {isExpanded ? '▲' : '▼'}
                    </span>
                  </div>
                </button>

                {/* 展开内容 */}
                {isExpanded && (
                  <div style={{
                    borderTop: '1px solid #334155',
                    padding: '1.25rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1rem'
                  }}>
                    {case_.description && (
                      <div>
                        <h4 style={{
                          fontSize: '0.75rem',
                          fontWeight: '600',
                          textTransform: 'uppercase',
                          color: '#64748b',
                          marginBottom: '0.5rem'
                        }}>
                          描述
                        </h4>
                        <p style={{ fontSize: '0.875rem', color: '#e2e8f0', lineHeight: '1.6' }}>
                          {case_.description}
                        </p>
                      </div>
                    )}

                    {case_.solution && (
                      <div>
                        <h4 style={{
                          fontSize: '0.75rem',
                          fontWeight: '600',
                          textTransform: 'uppercase',
                          color: '#64748b',
                          marginBottom: '0.5rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.375rem'
                        }}>
                          💡 解决方案
                        </h4>
                        <div style={{
                          padding: '0.75rem 1rem',
                          backgroundColor: 'rgba(16, 185, 129, 0.1)',
                          border: '1px solid rgba(16, 185, 129, 0.3)',
                          borderRadius: '8px'
                        }}>
                          <p style={{ fontSize: '0.875rem', color: '#d1fae5', lineHeight: '1.6', margin: 0 }}>
                            {case_.solution}
                          </p>
                        </div>
                      </div>
                    )}

                    {case_.affected_modules && case_.affected_modules.length > 0 && (
                      <div>
                        <h4 style={{
                          fontSize: '0.75rem',
                          fontWeight: '600',
                          textTransform: 'uppercase',
                          color: '#64748b',
                          marginBottom: '0.5rem'
                        }}>
                          受影响模块
                        </h4>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          {case_.affected_modules.map((module) => (
                            <span
                              key={module}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: '#0f172a',
                                border: '1px solid #334155',
                                color: '#94a3b8',
                                borderRadius: '6px',
                                fontSize: '0.75rem',
                                fontFamily: 'monospace'
                              }}
                            >
                              {module}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      fontSize: '0.75rem',
                      color: '#64748b',
                      paddingTop: '0.75rem',
                      borderTop: '1px solid #334155'
                    }}>
                      <span>案例ID: {case_.id}</span>
                      {case_.verified && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#10b981' }}>
                          ✓ 已验证
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
