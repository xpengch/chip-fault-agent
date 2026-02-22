import React, { useState, useEffect } from 'react';
import api from '../api';

export default function HistoryPage({ showHistoryDialog, setShowHistoryDialog, onViewDetail }) {
  const [filters, setFilters] = useState({
    chipModel: '',
    date: '',
    limit: 50
  });
  const [records, setRecords] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const result = await api.getHistory(
        filters.limit,
        0,
        filters.chipModel || null,
        filters.date ? `${filters.date}T00:00:00` : null,
        filters.date ? `${filters.date}T23:59:59` : null
      );
      setRecords(result.records || []);
      setTotalCount(result.total_count || 0);
    } catch (error) {
      console.error('获取历史记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [filters]);

  const getStatusBadge = (statusValue) => {
    const config = {
      completed: { color: '#10b981', bg: 'rgba(16, 185, 129, 0.2)', border: '#10b981', label: '✓ 已完成' },
      pending: { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.2)', border: '#f59e0b', label: '⏳ 进行中' },
      failed: { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.2)', border: '#ef4444', label: '✗ 失败' }
    };
    const statusConfig = config[statusValue] || config.pending;
    return (
      <span style={{
        padding: '4px 10px',
        backgroundColor: statusConfig.bg,
        border: '1px solid ' + statusConfig.border,
        color: statusConfig.color,
        borderRadius: '4px',
        fontSize: '11px',
        fontWeight: '600',
        textTransform: 'uppercase'
      }}>
        {statusConfig.label}
      </span>
    );
  };

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
          📜 历史记录
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
          浏览和搜索历史芯片故障分析记录
        </p>
      </div>

      {/* 筛选区域 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
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
            <input
              type="text"
              value={filters.chipModel}
              onChange={(e) => setFilters({ ...filters, chipModel: e.target.value })}
              className="input"
              placeholder="例如: XC9000"
              style={{ fontSize: '0.875rem' }}
            />
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
              日期
            </label>
            <input
              type="date"
              value={filters.date}
              onChange={(e) => setFilters({ ...filters, date: e.target.value })}
              className="input"
              style={{ fontSize: '0.875rem' }}
            />
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
              显示数量
            </label>
            <select
              value={filters.limit}
              onChange={(e) => setFilters({ ...filters, limit: parseInt(e.target.value) })}
              className="select"
              style={{ fontSize: '0.875rem' }}
            >
              <option value={10}>10条</option>
              <option value={20}>20条</option>
              <option value={50}>50条</option>
              <option value={100}>100条</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem' }}>
            <button
              onClick={fetchHistory}
              disabled={loading}
              className="btn-secondary"
              style={{ flex: 1, fontSize: '0.875rem' }}
            >
              {loading ? '加载中...' : '🔄 刷新'}
            </button>
          </div>
        </div>

        <div style={{
          marginTop: '1rem',
          fontSize: '0.875rem',
          color: '#94a3b8'
        }}>
          显示 <span style={{ color: '#00d4ff', fontFamily: 'monospace' }}>{records.length}</span> 条记录，
          共 <span style={{ color: '#00d4ff', fontFamily: 'monospace' }}>{totalCount}</span> 条
        </div>
      </div>

      {/* 记录列表 */}
      {loading && records.length === 0 ? (
        <div style={{
          padding: '3rem',
          textAlign: 'center',
          color: '#64748b'
        }}>
          <div className="spinner" style={{ margin: '0 auto 1rem' }} />
          <div>加载中...</div>
        </div>
      ) : records.length === 0 ? (
        <div className="card" style={{
          padding: '3rem',
          textAlign: 'center',
          color: '#64748b'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
          <div>暂无历史记录</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {records.map((record) => (
            <div
              key={record.session_id}
              className="card"
              style={{ padding: '1rem 1.25rem', margin: 0 }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* 头部 */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                    <span style={{
                      fontFamily: 'monospace',
                      color: '#00d4ff',
                      fontSize: '0.875rem',
                      fontWeight: '600'
                    }}>
                      {record.chip_model}
                    </span>

                    {getStatusBadge(record.status)}

                    {record.confidence && (
                      <span style={{
                        fontSize: '0.8125rem',
                        fontFamily: 'monospace',
                        color: record.confidence >= 0.8 ? '#10b981' : '#f59e0b'
                      }}>
                        {(record.confidence * 100).toFixed(0)}% 置信度
                      </span>
                    )}
                  </div>

                  {/* 元信息 */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    fontSize: '0.75rem',
                    color: '#64748b',
                    marginBottom: '0.5rem'
                  }}>
                    <span>
                      📅 {new Date(record.created_at).toLocaleString('zh-CN')}
                    </span>
                    {record.processing_duration && (
                      <span>
                        ⏱️ {record.processing_duration.toFixed(1)}s
                      </span>
                    )}
                  </div>

                  {/* 根因 */}
                  {record.root_cause && (
                    <p style={{
                      fontSize: '0.875rem',
                      color: '#e2e8f0',
                      lineHeight: '1.5',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {record.root_cause}
                    </p>
                  )}

                  {/* 会话ID */}
                  <div style={{
                    fontSize: '0.75rem',
                    fontFamily: 'monospace',
                    color: '#64748b',
                    marginTop: '0.5rem'
                  }}>
                    会话ID: {record.session_id.slice(0, 12)}...
                  </div>
                </div>

                <button
                  onClick={() => onViewDetail(record.session_id)}
                  className="btn-secondary"
                  style={{ fontSize: '0.8125rem', padding: '0.5rem 1rem', whiteSpace: 'nowrap' }}
                >
                  查看详情
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
