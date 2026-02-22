import React, { useState } from 'react';
import api from '../api';

export default function AnalyzePage({ chipModel, inferThreshold }) {
  const [inputMethod, setInputMethod] = useState('paste');
  const [rawLog, setRawLog] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState({
    stage: 0,
    message: '',
    elapsed: 0,
    eta: '计算中...',
    tokens: '--',
    tokenRate: '--'
  });
  const [result, setResult] = useState(null);
  const [sessionId, setSessionId] = useState('');

  // 进度阶段定义
  const progressStages = [
    { progress: 0.1, message: '📋 解析日志格式...', time: 2 },
    { progress: 0.2, message: '🔍 提取故障特征...', time: 5 },
    { progress: 0.4, message: '🧠 执行多源推理...', time: 12 },
    { progress: 0.6, message: '🔗 知识图谱查询...', time: 18 },
    { progress: 0.8, message: '📝 LLM生成分析报告...', time: 25 },
    { progress: 0.95, message: '✨ 融合推理结果...', time: 28 },
    { progress: 1.0, message: '✅ 分析完成', time: 30 }
  ];

  const canSubmit = chipModel && rawLog;

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadedFile(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        setRawLog(event.target.result);
      };
      reader.onerror = () => {
        alert(`✗ 文件读取失败: ${file.name}`);
      };
      reader.readAsText(file);
    }
  };

  const handleAnalyze = async () => {
    if (!canSubmit) {
      alert('⚠️ 请先填写芯片型号和日志内容');
      return;
    }

    setAnalyzing(true);
    setResult(null);
    setProgress({
      stage: 0,
      message: '🚀 初始化分析...',
      elapsed: 0,
      eta: '计算中...',
      tokens: '--',
      tokenRate: '--'
    });

    const startTime = Date.now();
    const estimatedDuration = 30;

    // 启动进度更新
    const progressInterval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;

      // 更新阶段
      let currentStage = progressStages[0];
      for (const stage of progressStages) {
        if (elapsed >= stage.time) {
          currentStage = stage;
        }
      }

      // 计算ETA
      const eta = Math.max(estimatedDuration - elapsed, 0);
      let etaText;
      if (eta > 60) {
        etaText = `${Math.floor(eta / 60)}m ${Math.floor(eta % 60)}s`;
      } else {
        etaText = `${Math.floor(eta)}s`;
      }

      // Token估算
      let tokens = '--';
      let tokenRate = '--';
      if (elapsed > 3) {
        let estimatedTokens;
        if (elapsed < 8) {
          estimatedTokens = Math.floor(elapsed * 35);
          tokenRate = '~35/s';
        } else if (elapsed < 15) {
          const baseTokens = 8 * 35;
          estimatedTokens = Math.floor(baseTokens + (elapsed - 8) * 75);
          tokenRate = '~75/s';
        } else {
          const baseTokens = 8 * 35 + 7 * 75;
          estimatedTokens = Math.floor(baseTokens + (elapsed - 15) * 120);
          tokenRate = '~120/s';
        }
        tokens = estimatedTokens.toLocaleString();
      }

      setProgress({
        stage: currentStage.progress,
        message: currentStage.message,
        elapsed: parseFloat(elapsed.toFixed(1)),
        eta: etaText,
        tokens,
        tokenRate
      });
    }, 300);

    // 提交分析请求
    try {
      const response = await api.submitAnalysis(chipModel, rawLog, inferThreshold);
      console.log('=== API 响应 ===');
      console.log('完整响应:', JSON.stringify(response, null, 2));
      console.log('success:', response.success);
      console.log('data:', response.data);
      if (response.data) {
        console.log('data keys:', Object.keys(response.data));
        console.log('session_id:', response.data.session_id);
        console.log('final_root_cause:', response.data.final_root_cause);
        console.log('infer_report length:', response.data.infer_report?.length || 0);
      }
      clearInterval(progressInterval);

      const finalElapsed = ((Date.now() - startTime) / 1000).toFixed(1);

      if (response.success && response.data) {
        const data = response.data;
        console.log('Analysis Data:', data); // 调试日志
        const tokensUsed = data.tokens_used || 0;
        const finalTokens = tokensUsed > 0 ? tokensUsed.toLocaleString() : progress.tokens;
        const finalRate = tokensUsed > 0 ? `${Math.floor(tokensUsed / parseFloat(finalElapsed))}/s` : progress.tokenRate;

        setProgress({
          stage: 1,
          message: '✅ 分析完成',
          elapsed: parseFloat(finalElapsed),
          eta: '完成',
          tokens: finalTokens,
          tokenRate: finalRate
        });

        const resultData = { success: true, data };
        console.log('Setting result:', resultData); // 调试日志
        setResult(resultData);
        if (data.session_id) {
          setSessionId(data.session_id);
        }

        // 刷新统计数据
        setTimeout(() => {
          window.dispatchEvent(new Event('stats-refresh'));
        }, 500);
      } else {
        console.error('API returned error:', response);
        setResult({ success: false, error: response.error, detail: response.detail });
      }
    } catch (error) {
      console.error('Request failed:', error);
      clearInterval(progressInterval);
      setResult({ success: false, error: '请求失败', detail: error.message });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSessionQuery = async () => {
    const querySessionId = prompt('请输入会话ID:');
    if (!querySessionId) return;

    const response = await api.getAnalysisResult(querySessionId);
    if (response.success && response.data) {
      setResult({ success: true, data: response.data });
    } else {
      alert(`无法获取分析结果: ${response.error || 'Unknown error'}`);
    }
  };

  return (
    <div>
      {/* 日志输入区域 */}
      <div className="card-elevated tech-border">
        <div className="card-title">📝 故障日志输入</div>
        <div className="card-subtitle">粘贴或上传芯片故障日志以开始智能分析</div>
      </div>

      {/* 输入方式选择 */}
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="radio"
              value="paste"
              checked={inputMethod === 'paste'}
              onChange={() => setInputMethod('paste')}
              style={{ accentColor: '#00d4ff' }}
            />
            <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>📋 直接粘贴</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="radio"
              value="upload"
              checked={inputMethod === 'upload'}
              onChange={() => setInputMethod('upload')}
              style={{ accentColor: '#00d4ff' }}
            />
            <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>📁 文件上传</span>
          </label>
        </div>

        {inputMethod === 'paste' ? (
          <textarea
            value={rawLog}
            onChange={(e) => setRawLog(e.target.value)}
            className="textarea"
            placeholder="在此粘贴芯片故障日志...

支持格式：
• 系统日志
• 错误日志
• 调试输出
• JSON格式日志"
            style={{ height: '180px', fontFamily: 'monospace' }}
          />
        ) : (
          <div>
            <input
              type="file"
              accept=".txt,.log,.json"
              onChange={handleFileUpload}
              className="input"
            />
            {uploadedFile && (
              <div style={{
                marginTop: '0.75rem',
                padding: '0.75rem',
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid #10b981',
                borderRadius: '8px',
                color: '#10b981',
                fontSize: '0.875rem'
              }}>
                ✓ 已加载: {uploadedFile.name}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 分析按钮 */}
      <div style={{ display: 'flex', justifyContent: 'center', margin: '1.5rem 0' }}>
        <button
          onClick={handleAnalyze}
          disabled={!canSubmit || analyzing}
          className="btn-primary"
          style={{ minWidth: '250px', fontSize: '1.1rem' }}
        >
          🚀 开始智能分析
        </button>
      </div>

      {/* 进度监控 */}
      {analyzing && (
        <div className="card-elevated tech-border" style={{
          background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(15, 23, 42, 0.9) 100%)',
          borderLeft: '4px solid #00d4ff'
        }}>
          <div className="card-title">⚡ 分析进度实时监控</div>

          {/* 进度条 */}
          <div className="progress-bar" style={{ marginBottom: '1.5rem' }}>
            <div
              className="progress-bar-fill"
              style={{ width: `${progress.stage * 100}%` }}
            />
          </div>

          {/* 指标卡片 */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
            <div className="metric-card">
              <div className="metric-label">已用时间</div>
              <div className="metric-value-primary" style={{
                fontSize: '1.6rem',
                color: '#00d4ff',
                textShadow: '0 0 15px rgba(0, 212, 255, 0.5)'
              }}>
                {progress.elapsed.toFixed(1)}s
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">预计剩余</div>
              <div className="metric-value-primary" style={{
                fontSize: '1.6rem',
                color: '#10b981',
                textShadow: '0 0 15px rgba(16, 185, 129, 0.5)'
              }}>
                {progress.eta}
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Token消耗</div>
              <div className="metric-value-primary" style={{
                fontSize: '1.6rem',
                color: '#f59e0b',
                textShadow: '0 0 15px rgba(245, 158, 11, 0.5)'
              }}>
                {progress.tokens}
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-label">Token速率</div>
              <div className="metric-value-primary" style={{
                fontSize: '1.6rem',
                color: '#a855f7',
                textShadow: '0 0 15px rgba(168, 85, 247, 0.5)'
              }}>
                {progress.tokenRate}
              </div>
            </div>
          </div>

          {/* 状态消息 */}
          <div className="status-card status-card-info" style={{ marginTop: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div className="pulse-dot" />
              <div style={{ fontSize: '0.875rem', color: '#ffffff' }}>
                {progress.message}
              </div>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.5rem' }}>
              进度: {Math.floor(progress.stage * 100)}% | 已耗时: {progress.elapsed.toFixed(1)}s
            </div>
          </div>
        </div>
      )}

      {/* 分析结果 */}
      {result && (
        <div style={{ marginTop: '1.5rem' }}>
          {/* 调试信息 - 总是显示 */}
          <div style={{
            padding: '1rem',
            background: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid #f59e0b',
            borderRadius: '8px',
            marginBottom: '1rem',
            fontSize: '0.875rem',
            color: '#f59e0b'
          }}>
            <strong>🔍 调试信息:</strong>
            <br />API响应状态: {result.success ? '✅ 成功' : '❌ 失败'}
            {result.success && result.data ? (
              <>
                <br />会话ID: {result.data.session_id || 'none'}
                <br />有final_root_cause: {result.data.final_root_cause ? '✅' : '❌'}
                <br />有infer_report: {result.data.infer_report ? `✅ (${result.data.infer_report.length} 字符)` : '❌'}
                {result.data.final_root_cause && (
                  <>
                    <br />失效域: {result.data.final_root_cause.failure_domain || 'none'}
                    <br />置信度: {(result.data.final_root_cause.confidence || 0) * 100}%
                  </>
                )}
                <br /><strong style={{color: '#00d4ff'}}>数据字段:</strong> {Object.keys(result.data).join(', ')}
              </>
            ) : (
              <>
                <br />错误: {result.error || '未知'}
                {result.detail && <><br />详情: {result.detail}</>}
              </>
            )}
          </div>

          {result.success ? (
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
                    {(result.data.final_root_cause?.failure_domain || result.data.failure_domain || '未知').toUpperCase()}
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-label">置信度</div>
                  <div className="metric-value-primary" style={{ fontSize: '1.8rem', color: '#10b981' }}>
                    {((result.data.final_root_cause?.confidence || result.data.confidence || 0) * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-label">分析状态</div>
                  <div className="metric-value-primary" style={{
                    fontSize: '1.8rem',
                    color: (result.data.need_expert ?? result.data.needs_expert_intervention) ? '#f59e0b' : '#10b981'
                  }}>
                    {(result.data.need_expert ?? result.data.needs_expert_intervention) ? '需专家确认' : '自动完成'}
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
                      {result.data.final_root_cause?.module || result.data.root_cause?.module || '未知'}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>失效域</div>
                    <div style={{ fontSize: '1rem', color: '#ffffff' }}>
                      {(result.data.final_root_cause?.failure_domain || result.data.failure_domain || '未知').toUpperCase()}
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
                  {result.data.final_root_cause?.root_cause || result.data.root_cause?.description || '暂无描述'}
                </div>

                {/* 推理依据 */}
                {result.data.final_root_cause?.reasoning && (
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
                    {result.data.final_root_cause.reasoning}
                  </div>
                )}
              </div>

              {/* AI分析报告 */}
              {result.data.infer_report && (
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
                    {result.data.infer_report}
                  </div>
                </div>
              )}

              {/* 会话信息 */}
              {result.data.session_id && (
                <div style={{
                  marginTop: '1rem',
                  padding: '0.75rem 1rem',
                  background: 'rgba(15, 23, 42, 0.5)',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  color: '#64748b'
                }}>
                  会话ID: {result.data.session_id}
                </div>
              )}
            </div>
          ) : (
            <div className="status-card status-card-error">
              <strong>❌ 分析失败</strong><br />
              {result.error}
              {result.detail && <div style={{ fontSize: '0.875rem', color: '#94a3b8', marginTop: '0.5rem' }}>{result.detail}</div>}
            </div>
          )}
        </div>
      )}

      {/* 会话查询 */}
      <div className="card" style={{ marginTop: '2rem' }}>
        <div className="card-title">🔍 会话查询</div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button
            onClick={handleSessionQuery}
            className="btn-secondary"
            style={{ fontSize: '0.875rem' }}
          >
            查询历史会话
          </button>
          <span style={{ fontSize: '0.875rem', color: '#64748b' }}>
            输入会话ID查看历史分析结果
          </span>
        </div>
        {sessionId && (
          <div style={{
            marginTop: '0.75rem',
            padding: '0.5rem 1rem',
            background: 'rgba(0, 212, 255, 0.1)',
            border: '1px solid rgba(0, 212, 255, 0.3)',
            borderRadius: '6px',
            fontSize: '0.875rem',
            color: '#00d4ff'
          }}>
            当前会话ID: {sessionId}
          </div>
        )}
      </div>
    </div>
  );
}
