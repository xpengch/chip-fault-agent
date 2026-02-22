import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import './App.css';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardStats from './components/DashboardStats';
import AnalyzePage from './pages/AnalyzePage';
import HistoryPage from './pages/HistoryPage';
import CasesPage from './pages/CasesPage';
import SystemPage from './pages/SystemPage';
import api from './api';

function App() {
  const location = useLocation();

  // 页面状态
  const [currentPage, setCurrentPage] = useState('日志分析');
  const [showHistoryDialog, setShowHistoryDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [detailResult, setDetailResult] = useState(null);

  // 侧边栏配置状态
  const [apiUrl, setApiUrl] = useState('http://localhost:8889');
  const [chipModel, setChipModel] = useState('XC9000');
  const [customChipModel, setCustomChipModel] = useState('');
  const [inferThreshold, setInferThreshold] = useState(0.7);
  const [apiStatus, setApiStatus] = useState('unknown');

  // 检查API健康状态
  const checkApiHealth = async () => {
    const isOnline = await api.checkHealth();
    setApiStatus(isOnline ? 'online' : 'offline');
    return isOnline;
  };

  // 初始化时检查API状态
  useEffect(() => {
    checkApiHealth();
  }, []);

  // 根据路径更新当前页面状态
  useEffect(() => {
    const pathMap = {
      '/analyze': '日志分析',
      '/history': '历史记录',
      '/cases': '案例库',
      '/system': '系统信息'
    };
    setCurrentPage(pathMap[location.pathname] || '日志分析');
  }, [location.pathname]);

  // 处理页面导航
  const handlePageChange = (page) => {
    // 移除表情符号，获取页面名称
    const pageName = page.split(' ').slice(1).join(' ') || page.split(' ')[0];
    setCurrentPage(pageName);
  };

  // 处理详情查看
  const handleViewDetail = async (sessionId) => {
    const result = await api.getAnalysisResult(sessionId);
    if (result.success && result.data) {
      setDetailResult(result.data);
      setShowDetailDialog(true);
    } else {
      alert(`无法获取分析结果: ${result.error || 'Unknown error'}`);
    }
  };

  // 关闭详情对话框
  const handleCloseDetail = () => {
    setShowDetailDialog(false);
    setDetailResult(null);
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#070a14' }}>
      {/* 背景网格效果 */}
      <div className="bg-grid" />

      <div style={{ display: 'flex', minHeight: '100vh', position: 'relative', zIndex: 1 }}>
        {/* 侧边栏 */}
        <Sidebar
          apiUrl={apiUrl}
          setApiUrl={setApiUrl}
          chipModel={chipModel}
          setChipModel={setChipModel}
          customChipModel={customChipModel}
          setCustomChipModel={setCustomChipModel}
          inferThreshold={inferThreshold}
          setInferThreshold={setInferThreshold}
          currentPage={currentPage}
          onPageChange={handlePageChange}
          apiStatus={apiStatus}
          onCheckApi={checkApiHealth}
        />

        {/* 主内容区 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* 头部 */}
          <Header />

          {/* 内容区域 */}
          <div style={{ flex: 1, overflow: 'auto', padding: '1rem 2rem' }}>
            {/* 仪表板统计 */}
            <DashboardStats />

            <Routes>
              <Route path="/" element={<Navigate to="/analyze" replace />} />
              <Route
                path="/analyze"
                element={
                  <AnalyzePage
                    chipModel={chipModel === '自定义型号' ? customChipModel : chipModel}
                    inferThreshold={inferThreshold}
                  />
                }
              />
              <Route
                path="/history"
                element={
                  <HistoryPage
                    showHistoryDialog={showHistoryDialog}
                    setShowHistoryDialog={setShowHistoryDialog}
                    onViewDetail={handleViewDetail}
                  />
                }
              />
              <Route path="/cases" element={<CasesPage />} />
              <Route path="/system" element={<SystemPage />} />
            </Routes>

            {/* 页脚 */}
            <div style={{
              textAlign: 'center',
              padding: '3rem 1rem',
              color: '#64748b',
              fontSize: '0.875rem',
              marginTop: '2rem'
            }}>
              <div style={{ marginBottom: '0.5rem', color: '#00d4ff' }}>
                © 2024 芯片失效分析AI Agent系统 | 企业版 v2.0
              </div>
              <div style={{ fontSize: '0.75rem' }}>
                技术支持: support@chipfault.ai | 官网: www.chipfault.ai
              </div>
              <div style={{ marginTop: '1rem', fontSize: '0.7rem', color: '#475569' }}>
                Powered by LangGraph + GLM-4.7 + Claude
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 详情对话框 */}
      {showDetailDialog && detailResult && (
        <DetailDialog
          result={detailResult}
          onClose={handleCloseDetail}
        />
      )}
    </div>
  );
}

// 详情对话框组件
function DetailDialog({ result, onClose }) {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '2rem'
    }}>
      <div style={{
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(12px)',
        borderRadius: '20px',
        border: '1px solid rgba(0, 212, 255, 0.3)',
        boxShadow: '0 0 50px rgba(0, 0, 0, 0.5)',
        maxWidth: '900px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        padding: '2rem'
      }}>
        {/* 标题 */}
        <div style={{
          fontSize: '1.5rem',
          fontWeight: 'bold',
          color: '#ffffff',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          📄 分析结果详情
        </div>

        {/* 显示结果 - 复用结果显示组件 */}
        <ResultDisplay result={result} />

        {/* 关闭按钮 */}
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '2rem' }}>
          <button
            onClick={onClose}
            className="btn-primary"
            style={{ minWidth: '200px' }}
          >
            ✖ 返回
          </button>
        </div>
      </div>
    </div>
  );
}

// 结果显示组件
function ResultDisplay({ result }) {
  if (!result || !result.success) {
    return (
      <div className="status-card status-card-error">
        <strong>❌ 分析失败</strong><br />
        {result?.error || '未知错误'}
      </div>
    );
  }

  const data = result.data || {};
  // 兼容新旧API格式
  const finalRootCause = data.final_root_cause || {};
  const failureDomain = finalRootCause.failure_domain || data.failure_domain || '未知';
  const confidence = finalRootCause.confidence || data.confidence || 0;
  const needsExpert = data.need_expert ?? data.needs_expert_intervention ?? false;
  const rootCauseModule = finalRootCause.module || data.root_cause?.module || '未知';
  const rootCauseDesc = finalRootCause.root_cause || data.root_cause?.description || '暂无描述';
  const reasoning = finalRootCause.reasoning || null;
  const aiAnalysis = data.infer_report || data.ai_analysis_report || '';

  return (
    <div>
      {/* 成功横幅 */}
      <div style={{
        padding: '1.5rem',
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.05) 100%)',
        borderLeft: '4px solid #10b981',
        borderRadius: '12px',
        marginBottom: '1.5rem',
        color: '#10b981',
        fontSize: '1.1rem',
        fontWeight: '600',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        ✅ 分析完成！
      </div>

      {/* 概览卡片 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="metric-card">
          <div className="metric-label">失效域</div>
          <div className="metric-value-primary" style={{ fontSize: '1.8rem' }}>
            {failureDomain.toUpperCase()}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">置信度</div>
          <div className="metric-value-primary" style={{ fontSize: '1.8rem', color: '#10b981' }}>
            {(confidence * 100).toFixed(0)}%
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">分析状态</div>
          <div className="metric-value-primary" style={{
            fontSize: '1.8rem',
            color: needsExpert ? '#f59e0b' : '#10b981'
          }}>
            {needsExpert ? '需专家确认' : '自动完成'}
          </div>
        </div>
      </div>

      {/* 根因分析 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-title">🔍 根因分析</div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>故障模块</div>
            <div style={{ fontSize: '1rem', color: '#ffffff' }}>
              {rootCauseModule}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>失效域</div>
            <div style={{ fontSize: '1rem', color: '#ffffff' }}>
              {failureDomain.toUpperCase()}
            </div>
          </div>
        </div>

        <div style={{
          padding: '1rem',
          background: '#0f172a',
          borderRadius: '8px',
          border: '1px solid #1e293b',
          color: '#e2e8f0',
          lineHeight: '1.6'
        }}>
          {rootCauseDesc}
        </div>

        {/* 推理依据 */}
        {reasoning && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            background: 'rgba(0, 212, 255, 0.05)',
            borderRadius: '8px',
            border: '1px solid rgba(0, 212, 255, 0.2)',
            color: '#94a3b8',
            fontSize: '0.875rem',
            lineHeight: '1.6'
          }}>
            <div style={{ color: '#00d4ff', marginBottom: '0.5rem', fontWeight: '600' }}>🔗 推理依据</div>
            {reasoning}
          </div>
        )}
      </div>

      {/* AI分析报告 */}
      {aiAnalysis ? (
        <div className="card">
          <div className="card-title">🤖 AI分析报告</div>

          <div style={{
            padding: '1rem',
            background: '#0f172a',
            borderRadius: '8px',
            border: '1px solid #1e293b',
            color: '#e2e8f0',
            lineHeight: '1.8',
            whiteSpace: 'pre-wrap',
            maxHeight: '500px',
            overflow: 'auto'
          }}>
            {aiAnalysis}
          </div>
        </div>
      ) : (
        /* 当没有AI报告时，显示推理步骤 */
        data.infer_trace && data.infer_trace.length > 0 && (
          <div className="card">
            <div className="card-title">🔬 分析推理步骤</div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {data.infer_trace.map((step, index) => (
                <div
                  key={index}
                  style={{
                    padding: '1rem',
                    background: '#0f172a',
                    borderRadius: '8px',
                    border: '1px solid #1e293b',
                    borderLeft: '3px solid #00d4ff'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      background: '#00d4ff',
                      color: '#0f172a',
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      {index + 1}
                    </span>
                    <span style={{ color: '#ffffff', fontWeight: '600' }}>
                      {step.description}
                    </span>
                  </div>

                  {step.result && typeof step.result === 'object' && (
                    <div style={{ marginLeft: '2rem', fontSize: '0.875rem', color: '#94a3b8' }}>
                      {Object.entries(step.result).map(([key, value]) => (
                        <div key={key}>
                          <span style={{ color: '#64748b' }}>{key}:</span> {String(value)}
                        </div>
                      ))}
                    </div>
                  )}

                  {step.timestamp && (
                    <div style={{ marginLeft: '2rem', fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
                      ⏱️ {new Date(step.timestamp).toLocaleString('zh-CN')}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div style={{
              marginTop: '1rem',
              padding: '0.75rem',
              background: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '6px',
              fontSize: '0.875rem',
              color: '#f59e0b',
              textAlign: 'center'
            }}>
              ⚠️ 详细AI分析报告暂不可用，以上为分析推理步骤记录
            </div>
          </div>
        )
      )}

      {/* 会话信息 */}
      {data.session_id && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem 1rem',
          background: 'rgba(15, 23, 42, 0.5)',
          borderRadius: '8px',
          fontSize: '0.875rem',
          color: '#64748b'
        }}>
          会话ID: {data.session_id}
        </div>
      )}
    </div>
  );
}

export default App;
