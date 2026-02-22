import React, { useState, useEffect } from 'react';
import api from '../api';

export default function DashboardStats() {
  const [stats, setStats] = useState({
    today_analyses: 0,
    success_rate: 0,
    avg_duration: 0,
    expert_interventions: 0,
    today_change: 0,
    duration_change: 0,
    expert_change: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      const data = await api.getStats();
      setStats(data);
      setLoading(false);
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="metric-card">
            <div style={{ height: '60px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div className="spinner" style={{ width: '24px', height: '24px' }} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const {
    today_analyses,
    success_rate,
    avg_duration,
    expert_interventions,
    today_change,
    duration_change,
    expert_change
  } = stats;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
      {/* 今日分析 */}
      <div className="metric-card">
        <div className="metric-label">今日分析</div>
        <div className="metric-value-primary">{today_analyses}</div>
        <div className={`metric-change ${today_change >= 0 ? 'metric-change-positive' : 'metric-change-negative'}`}>
          <span>{today_change >= 0 ? '↑' : '↓'}</span> {Math.abs(today_change).toFixed(1)}%
        </div>
      </div>

      {/* 成功率 */}
      <div className="metric-card">
        <div className="metric-label">成功率</div>
        <div className="metric-value-primary" style={{ color: '#10b981', textShadow: '0 0 15px rgba(16, 185, 129, 0.5)' }}>
          {success_rate.toFixed(1)}%
        </div>
        <div className="metric-change metric-change-positive">
          <span>↑</span> 0.0%
        </div>
      </div>

      {/* 平均耗时 */}
      <div className="metric-card">
        <div className="metric-label">平均耗时</div>
        <div className="metric-value-primary" style={{ color: '#a855f7', textShadow: '0 0 15px rgba(168, 85, 247, 0.5)' }}>
          {avg_duration.toFixed(1)}s
        </div>
        <div className={`metric-change ${duration_change <= 0 ? 'metric-change-positive' : 'metric-change-negative'}`}>
          <span>{duration_change <= 0 ? '↓' : '↑'}</span> {Math.abs(duration_change).toFixed(1)}%
        </div>
      </div>

      {/* 专家介入 */}
      <div className="metric-card">
        <div className="metric-label">专家介入</div>
        <div className="metric-value-primary" style={{ color: '#f59e0b', textShadow: '0 0 15px rgba(245, 158, 11, 0.5)' }}>
          {expert_interventions}
        </div>
        <div className={`metric-change ${expert_change <= 0 ? 'metric-change-positive' : 'metric-change-negative'}`}>
          <span>{expert_change <= 0 ? '↓' : '↑'}</span> {Math.abs(expert_change).toFixed(1)}%
        </div>
      </div>
    </div>
  );
}
