import React, { useState, useEffect, useRef } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export default function AnalyzePage({ chipModel, inferThreshold }) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState('');
  const [currentResult, setCurrentResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState({ stage: 0, message: '' });
  const [realTimeStats, setRealTimeStats] = useState({
    stage: '',
    progress: 0,
    elapsed: '0s',
    eta: '计算中...',
    tokens: '--',
    tokenRate: '--'
  });
  const messagesEndRef = useRef(null);
  const progressIntervalRef = useRef(null);
  const fileInputRef = useRef(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [availableSessions, setAvailableSessions] = useState([]);
  const [showSessionDropdown, setShowSessionDropdown] = useState(false);
  // 专家反馈相关状态
  const [showCorrectionForm, setShowCorrectionForm] = useState(false);
  const [correctionSubmitting, setCorrectionSubmitting] = useState(false);
  const [correctionData, setCorrectionData] = useState({
    failure_domain: '',
    module: '',
    root_cause: '',
    confidence: 1.0,
    correction_reason: ''
  });

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, []);

  // 加载会话历史
  const loadConversation = async (sessionId) => {
    try {
      const response = await fetch(`http://localhost:8889/api/v1/analysis/${sessionId}/messages`);
      if (response.ok) {
        const data = await response.json();
        const loadedMessages = data.messages || [];

        // 将服务器消息转换为聊天格式
        const chatMessages = loadedMessages.map(msg => ({
          message_id: msg.message_id,
          message_type: msg.message_type,
          content: msg.content,
          created_at: msg.created_at
        }));

        // 添加当前分析结果
        if (data.current_analysis) {
          setCurrentResult(data.current_analysis);
          chatMessages.push({
            message_id: `analysis-${Date.now()}`,
            message_type: 'analysis_result',
            content: '',
            analysis_data: data.current_analysis,
            created_at: new Date().toISOString()
          });
        }

        setMessages(chatMessages);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  // 初始分析进度模拟（约30秒）
  const startProgressSimulation = () => {
    const stages = [
      { progress: 0.15, message: '📋 解析日志格式...', time: 2, tokens: 0 },
      { progress: 0.35, message: '🔍 提取故障特征...', time: 6, tokens: 200 },
      { progress: 0.55, message: '🧠 执行多源推理...', time: 15, tokens: 500 },
      { progress: 0.70, message: '📝 LLM生成分析报告...', time: 25, tokens: 1200 },
      { progress: 0.85, message: '✨ 融合推理结果...', time: 28, tokens: 1500 },
      { progress: 1.0, message: '✅ 分析完成', time: 30, tokens: 1600 }
    ];

    let currentStage = 0;
    let stageProgress = stages[0].progress; // 当前阶段的进度值
    const startTime = Date.now();
    const totalDuration = stages[stages.length - 1].time;

    const interval = setInterval(() => {
      const elapsed = ((Date.now() - startTime) / 1000);

      // 根据已用时间计算当前应该显示的进度
      let currentProgress = 0;
      let currentMessage = stages[0].message;
      let currentTokens = 0;

      for (let i = 0; i < stages.length; i++) {
        if (elapsed <= stages[i].time) {
          // 在当前阶段内，计算该阶段的相对进度
          const prevTime = i > 0 ? stages[i - 1].time : 0;
          const stageDuration = stages[i].time - prevTime;
          const stageElapsed = elapsed - prevTime;
          const prevProgress = i > 0 ? stages[i - 1].progress : 0;
          currentProgress = prevProgress + (stages[i].progress - prevProgress) * (stageElapsed / stageDuration);
          currentMessage = stages[i].message;
          currentTokens = stages[i].tokens > 0 ? Math.floor(stages[i].tokens * (stageElapsed / stageDuration)) : 0;
          break;
        }
      }

      // 确保进度不超过1
      currentProgress = Math.min(currentProgress, 1.0);

      // 更新显示
      const eta = Math.max(0, totalDuration - elapsed).toFixed(1);
      const tokenRate = currentTokens > 0 && elapsed > 0 ? (currentTokens / elapsed).toFixed(1) : '--';

      setRealTimeStats({
        stage: currentMessage,
        progress: currentProgress,
        elapsed: elapsed.toFixed(1) + 's',
        eta: eta > 0 ? `约${eta}秒` : '即将完成',
        tokens: currentTokens > 0 ? currentTokens : '--',
        tokenRate: tokenRate !== '--' ? `${tokenRate} token/s` : '--'
      });

      setProgress({
        stage: currentProgress,
        message: currentMessage
      });

      // 如果达到总时长，停止模拟
      if (elapsed >= totalDuration) {
        clearInterval(interval);
      }
    }, 100); // 更新频率提高到100ms，使进度更平滑

    progressIntervalRef.current = interval;
    return interval;
  };

  // 多轮对话进度模拟（较短，约18秒）
  const startMultiTurnProgressSimulation = () => {
    const stages = [
      { progress: 0.25, message: '📋 解析补充信息...', time: 3, tokens: 0 },
      { progress: 0.45, message: '🔍 更新故障特征...', time: 6, tokens: 100 },
      { progress: 0.65, message: '🧠 重新执行推理...', time: 10, tokens: 300 },
      { progress: 0.75, message: '📝 LLM更新分析报告...', time: 15, tokens: 600 },
      { progress: 1.0, message: '✅ 分析更新完成', time: 18, tokens: 800 }
    ];

    const startTime = Date.now();
    const baseTokens = currentResult?.tokens_used || 0;
    const totalDuration = stages[stages.length - 1].time;

    const interval = setInterval(() => {
      const elapsed = ((Date.now() - startTime) / 1000);

      // 根据已用时间计算当前应该显示的进度
      let currentProgress = 0;
      let currentMessage = stages[0].message;
      let currentTokens = 0;

      for (let i = 0; i < stages.length; i++) {
        if (elapsed <= stages[i].time) {
          // 在当前阶段内，计算该阶段的相对进度
          const prevTime = i > 0 ? stages[i - 1].time : 0;
          const stageDuration = stages[i].time - prevTime;
          const stageElapsed = elapsed - prevTime;
          const prevProgress = i > 0 ? stages[i - 1].progress : 0;
          currentProgress = prevProgress + (stages[i].progress - prevProgress) * (stageElapsed / stageDuration);
          currentMessage = stages[i].message;
          currentTokens = baseTokens + (stages[i].tokens > 0 ? Math.floor(stages[i].tokens * (stageElapsed / stageDuration)) : 0);
          break;
        }
      }

      // 确保进度不超过1
      currentProgress = Math.min(currentProgress, 1.0);

      // 更新显示
      const eta = Math.max(0, totalDuration - elapsed).toFixed(1);
      const tokenRate = currentTokens > baseTokens && elapsed > 0 ? ((currentTokens - baseTokens) / elapsed).toFixed(1) : '--';

      setRealTimeStats({
        stage: currentMessage,
        progress: currentProgress,
        elapsed: elapsed.toFixed(1) + 's',
        eta: eta > 0 ? `约${eta}秒` : '即将完成',
        tokens: currentTokens,
        tokenRate: tokenRate !== '--' ? `${tokenRate} token/s` : '--'
      });

      setProgress({
        stage: currentProgress,
        message: currentMessage
      });

      // 如果达到总时长，停止模拟
      if (elapsed >= totalDuration) {
        clearInterval(interval);
      }
    }, 100); // 更新频率提高到100ms，使进度更平滑

    progressIntervalRef.current = interval;
    return interval;
  };

  // 解析用户输入，提取芯片型号和日志
  const parseUserInput = (text) => {
    const lines = text.split('\n').map(l => l.trim()).filter(l => l);
    let chip = '';
    let log = '';

    // 尝试解析芯片型号（格式如 "芯片型号: XC9000" 或 "chip: XC9000"）
    for (const line of lines) {
      const chipMatch = line.match(/(?:芯片型号|chip|型号)[\s:：]+([A-Za-z0-9_\-]+)/i);
      if (chipMatch) {
        chip = chipMatch[1];
        lines.splice(lines.indexOf(line), 1);
        break;
      }
    }

    // 如果没有找到芯片型号，使用默认或传入的芯片型号
    if (!chip && chipModel) {
      chip = chipModel;
    }

    // 剩余内容作为日志
    log = lines.join('\n');

    return { chip, log };
  };

  // 处理文件上传
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadedFile(file);

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target.result;
      // 将文件内容追加到输入框
      setInputText(prev => prev ? `${prev}\n\n${content}` : content);
    };
    reader.onerror = () => {
      setMessages(prev => [...prev, {
        message_id: `error-${Date.now()}`,
        message_type: 'error',
        content: `文件读取失败: ${file.name}`,
        created_at: new Date().toISOString()
      }]);
    };
    reader.readAsText(file);
  };

  // 触发文件选择
  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputText.trim() || sending) return;

    const userMessage = {
      message_id: `user-${Date.now()}`,
      message_type: 'user_input',
      content: inputText,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setSending(true);

    try {
      // 检查是否有会话
      if (!currentSessionId) {
        // 首次分析 - 解析输入
        const { chip, log } = parseUserInput(inputText);

        if (!chip) {
          setMessages(prev => [...prev, {
            message_id: `error-${Date.now()}`,
            message_type: 'error',
            content: '请在输入中包含芯片型号，例如："芯片型号: XC9000"',
            created_at: new Date().toISOString()
          }]);
          setSending(false);
          return;
        }

        setAnalyzing(true);
        setProgress({ stage: 0, message: '🚀 初始化分析...' });
        setRealTimeStats({
          stage: '🚀 初始化分析...',
          progress: 0,
          elapsed: '0s',
          eta: '计算中...',
          tokens: 0,
          tokenRate: '--'
        });

        // 添加进度消息
        const progressMessageId = `progress-${Date.now()}`;
        setMessages(prev => [...prev, {
          message_id: progressMessageId,
          message_type: 'progress',
          content: '',
          progress_data: { stage: 0, message: '🚀 初始化分析...' },
          created_at: new Date().toISOString()
        }]);

        // 启动进度模拟
        const progressInterval = startProgressSimulation();

        // 调用分析API
        const response = await fetch('http://localhost:8889/api/v1/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chip_model: chip,
            raw_log: log
          })
        });

        clearInterval(progressInterval);

        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            setCurrentSessionId(data.data.session_id);
            setCurrentResult(data.data);

            // 更新最终统计数据 - 报告已生成完毕
            setRealTimeStats({
              stage: '✅ 分析完成',
              progress: 1.0,
              elapsed: '完成',
              eta: '--',
              tokens: data.data.tokens_used || data.data.token_usage?.total || '--',
              tokenRate: '--'
            });

            // 先添加分析结果，再移除进度卡片
            setMessages(prev => [
              ...prev.filter(m => m.message_id !== progressMessageId),
              {
                message_id: `analysis-${Date.now()}`,
                message_type: 'analysis_result',
                content: '',
                analysis_data: data.data,
                created_at: new Date().toISOString()
              }
            ]);

            // 短暂延迟后移除进度卡片
            setTimeout(() => {
              setAnalyzing(false);
              setRealTimeStats(prev => ({
                ...prev,
                stage: '✅ 分析完成'
              }));
            }, 100);
          } else {
            setAnalyzing(false);
            setMessages(prev => [...prev.filter(m => m.message_id !== progressMessageId), {
              message_id: `error-${Date.now()}`,
              message_type: 'error',
              content: `分析失败: ${data.error || '未知错误'}`,
              created_at: new Date().toISOString()
            }]);
          }
        } else {
          setAnalyzing(false);
          setMessages(prev => [...prev.filter(m => m.message_id !== progressMessageId), {
            message_id: `error-${Date.now()}`,
            message_type: 'error',
            content: '分析失败: 网络错误',
            created_at: new Date().toISOString()
          }]);
        }
      } else {
        // 继续对话 - 启动动态进度模拟
        setAnalyzing(true);
        setRealTimeStats({
          stage: '🔄 处理补充信息...',
          progress: 0.1,
          elapsed: '0s',
          eta: '计算中...',
          tokens: currentResult?.tokens_used || '--',
          tokenRate: '--'
        });

        // 为多轮对话添加进度消息
        const progressMessageId = `progress-${Date.now()}`;
        setMessages(prev => [...prev, {
          message_id: progressMessageId,
          message_type: 'progress',
          content: '',
          progress_data: { stage: 0.1, message: '🔄 处理补充信息...' },
          created_at: new Date().toISOString()
        }]);

        // 启动多轮对话的进度模拟（较短，约15秒）
        const multiTurnProgressInterval = startMultiTurnProgressSimulation();

        const response = await fetch(`http://localhost:8889/api/v1/analysis/${currentSessionId}/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content: inputText,
            content_type: 'text'
          })
        });

        // 清除进度模拟
        clearInterval(multiTurnProgressInterval);

        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            setCurrentResult(data.analysis_result);

            // 更新实时统计 - 显示更新完成
            const totalTokens = data.analysis_result?.tokens_used || currentResult?.tokens_used || '--';
            setRealTimeStats({
              stage: '✅ 分析更新完成，正在生成报告...',
              progress: 1.0,
              elapsed: '完成',
              eta: '--',
              tokens: totalTokens,
              tokenRate: '--'
            });

            // 先添加分析结果，再移除进度卡片
            setMessages(prev => [
              ...prev.filter(m => m.message_id !== progressMessageId),
              {
                message_id: `system-${Date.now()}`,
                message_type: 'system_response',
                content: data.system_response || '',
                created_at: new Date().toISOString()
              },
              {
                message_id: `analysis-${Date.now()}`,
                message_type: 'analysis_result',
                content: '',
                analysis_data: data.analysis_result,
                created_at: new Date().toISOString()
              }
            ]);

            // 短暂延迟后移除进度卡片
            setTimeout(() => {
              setAnalyzing(false);
              setRealTimeStats(prev => ({
                ...prev,
                stage: '✅ 分析更新完成'
              }));
            }, 100);
          } else {
            setAnalyzing(false);
            setMessages(prev => [...prev, {
              message_id: `error-${Date.now()}`,
              message_type: 'error',
              content: `发送失败: ${data.error || '未知错误'}`,
              created_at: new Date().toISOString()
            }]);
          }
        } else {
          setAnalyzing(false);
          setMessages(prev => [...prev, {
            message_id: `error-${Date.now()}`,
            message_type: 'error',
            content: '发送失败: 网络错误',
            created_at: new Date().toISOString()
          }]);
        }
      }
    } catch (error) {
      setAnalyzing(false);
      setMessages(prev => [...prev, {
        message_id: `error-${Date.now()}`,
        message_type: 'error',
        content: `错误: ${error.message}`,
        created_at: new Date().toISOString()
      }]);
    } finally {
      setSending(false);
    }
  };

  // 开始新对话
  const handleNewChat = () => {
    setMessages([]);
    setInputText('');
    setCurrentSessionId('');
    setCurrentResult(null);
    setAnalyzing(false);
    setRealTimeStats({
      stage: '',
      progress: 0,
      elapsed: '0s',
      eta: '计算中...',
      tokens: '--',
      tokenRate: '--'
    });
    setShowSessionDropdown(false);
  };

  // 获取历史会话列表
  const fetchSessions = async () => {
    try {
      const response = await fetch('http://localhost:8889/api/v1/history?limit=100');
      if (response.ok) {
        const data = await response.json();
        setAvailableSessions(data.records || []);
        setShowSessionDropdown(true);
      } else {
        alert('获取历史会话列表失败');
      }
    } catch (error) {
      alert('获取会话列表失败: ' + error.message);
    }
  };

  // 查询历史会话
  const handleLoadSession = async (sessionId) => {
    if (!sessionId) {
      fetchSessions();
      return;
    }

    try {
      const response = await fetch(`http://localhost:8889/api/v1/analysis/${sessionId}/messages`);
      if (response.ok) {
        const data = await response.json();
        setCurrentSessionId(sessionId);
        await loadConversation(sessionId);
        setShowSessionDropdown(false);
      } else {
        alert('无法加载该会话');
      }
    } catch (error) {
      alert('加载失败: ' + error.message);
    }
  };

  // 处理专家修正提交
  const handleExpertCorrection = async () => {
    if (!currentSessionId) return;

    setCorrectionSubmitting(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8889/api/v1/expert/corrections/${currentSessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify(correctionData)
      });

      const data = await response.json();

      if (data.success || response.ok) {
        // 添加成功消息
        setMessages(prev => [...prev, {
          message_id: `correction-${Date.now()}`,
          message_type: 'system_response',
          content: `✅ 专家修正已提交，修正ID: ${data.correction_id || '已记录'}`,
          created_at: new Date().toISOString()
        }]);

        // 关闭表单并重置
        setShowCorrectionForm(false);
        setCorrectionData({
          failure_domain: '',
          module: '',
          root_cause: '',
          confidence: 1.0,
          correction_reason: ''
        });
      } else {
        throw new Error(data.message || data.detail || '提交失败');
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        message_id: `error-${Date.now()}`,
        message_type: 'error',
        content: `提交失败: ${error.message}`,
        created_at: new Date().toISOString()
      }]);
    } finally {
      setCorrectionSubmitting(false);
    }
  };

  // 渲染消息内容
  const renderMessageContent = (msg) => {
    switch (msg.message_type) {
      case 'user_input':
        return (
          <div style={{
            display: 'flex',
            justifyContent: 'flex-end',
            marginBottom: '1rem'
          }}>
            <div style={{
              maxWidth: '70%',
              padding: '0.75rem 1rem',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #0066cc 0%, #004499 100%)',
              color: '#ffffff'
            }}>
              <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {msg.content}
              </div>
              <div style={{
                fontSize: '0.75rem',
                opacity: 0.7,
                marginTop: '0.5rem'
              }}>
                {formatDistanceToNow(new Date(msg.created_at), { addSuffix: true, locale: zhCN })}
              </div>
            </div>
          </div>
        );

      case 'progress':
        // 进度消息已被实时统计卡片取代，这里不显示
        return null;

      case 'analysis_result':
        const data = msg.analysis_data;
        return (
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{
              padding: '1.5rem',
              background: 'rgba(15, 23, 42, 0.8)',
              borderRadius: '12px',
              border: '1px solid #1e293b',
              animation: 'fadeInSlide 0.4s ease-out'
            }}>
              {/* 分析概要 */}
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <div style={{
                    display: 'inline-block',
                    padding: '0.25rem 0.75rem',
                    background: data?.need_expert ? 'rgba(251, 191, 36, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                    borderRadius: '20px',
                    fontSize: '0.75rem',
                    color: data?.need_expert ? '#fbbf24' : '#10b981'
                  }}>
                    {data?.need_expert ? '⚠️ 建议专家复核' : '✅ 自动分析完成'}
                  </div>

                  {/* 专家反馈按钮 */}
                  {data?.need_expert && (
                    <button
                      onClick={() => setShowCorrectionForm(!showCorrectionForm)}
                      style={{
                        padding: '0.25rem 0.75rem',
                        background: 'rgba(251, 191, 36, 0.15)',
                        border: '1px solid rgba(251, 191, 36, 0.4)',
                        borderRadius: '20px',
                        fontSize: '0.75rem',
                        color: '#fbbf24',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(251, 191, 36, 0.25)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(251, 191, 36, 0.15)'}
                    >
                      {showCorrectionForm ? '✕ 关闭' : '✏️ 专家反馈'}
                    </button>
                  )}
                </div>

                {data?.final_root_cause && (
                  <div>
                    <div style={{
                      color: '#94a3b8',
                      fontSize: '0.875rem',
                      marginBottom: '0.5rem'
                    }}>
                      推断根因
                    </div>
                    <div style={{
                      fontSize: '1.1rem',
                      fontWeight: '600',
                      color: '#e2e8f0',
                      marginBottom: '0.5rem'
                    }}>
                      {data.final_root_cause.root_cause}
                    </div>
                    <div style={{
                      fontSize: '0.875rem',
                      color: '#64748b'
                    }}>
                      置信度: {(data.final_root_cause.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                )}
              </div>

              {/* AI分析报告 */}
              {data?.infer_report && (
                <div style={{
                  padding: '1rem',
                  background: '#0f172a',
                  borderRadius: '8px',
                  border: '1px solid #1e293b',
                  maxHeight: '400px',
                  overflow: 'auto',
                  animation: 'fadeIn 0.3s ease-in-out'
                }}>
                  <div style={{
                    color: '#00d4ff',
                    fontSize: '0.875rem',
                    marginBottom: '0.75rem',
                    fontWeight: '600'
                  }}>
                    🤖 详细分析报告
                  </div>
                  <div style={{
                    color: '#94a3b8',
                    fontSize: '0.875rem',
                    lineHeight: '1.8',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {data.infer_report}
                  </div>
                  <style>{`
                    @keyframes fadeIn {
                      from {
                        opacity: 0;
                        transform: translateY(-10px);
                      }
                      to {
                        opacity: 1;
                        transform: translateY(0);
                      }
                    }
                  `}</style>
                </div>
              )}

              {/* 专家反馈表单 */}
              {showCorrectionForm && data?.need_expert && (
                <div style={{
                  marginTop: '1rem',
                  padding: '1.5rem',
                  background: 'rgba(251, 191, 36, 0.08)',
                  border: '1px solid rgba(251, 191, 36, 0.25)',
                  borderRadius: '12px',
                  animation: 'fadeIn 0.3s ease-in-out'
                }}>
                  <h4 style={{ color: '#fbbf24', marginBottom: '1rem', fontSize: '1rem', margin: '0 0 1rem 0' }}>
                    📝 提交专家修正
                  </h4>

                  {/* 失效域选择 */}
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.875rem' }}>
                      失效域 *
                    </label>
                    <select
                      value={correctionData.failure_domain}
                      onChange={(e) => setCorrectionData({...correctionData, failure_domain: e.target.value})}
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        background: '#0f172a',
                        border: '1px solid #1e293b',
                        borderRadius: '8px',
                        color: '#e2e8f0',
                        fontSize: '0.875rem'
                      }}
                    >
                      <option value="">请选择失效域</option>
                      <option value="compute">计算单元 (Compute)</option>
                      <option value="cache">缓存 (Cache)</option>
                      <option value="interconnect">互连 (Interconnect)</option>
                      <option value="memory">存储 (Memory)</option>
                      <option value="io">IO (IO)</option>
                    </select>
                  </div>

                  {/* 模块输入 */}
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.875rem' }}>
                      失效模块
                    </label>
                    <input
                      type="text"
                      value={correctionData.module}
                      onChange={(e) => setCorrectionData({...correctionData, module: e.target.value})}
                      placeholder="例如: L3_CACHE, DDR_CONTROLLER"
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        background: '#0f172a',
                        border: '1px solid #1e293b',
                        borderRadius: '8px',
                        color: '#e2e8f0',
                        fontSize: '0.875rem'
                      }}
                    />
                  </div>

                  {/* 根因输入 */}
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.875rem' }}>
                      根因分析 *
                    </label>
                    <textarea
                      value={correctionData.root_cause}
                      onChange={(e) => setCorrectionData({...correctionData, root_cause: e.target.value})}
                      placeholder="请输入您的专家分析..."
                      style={{
                        width: '100%',
                        minHeight: '80px',
                        padding: '0.75rem',
                        background: '#0f172a',
                        border: '1px solid #1e293b',
                        borderRadius: '8px',
                        color: '#e2e8f0',
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                        resize: 'vertical'
                      }}
                    />
                  </div>

                  {/* 修正原因 */}
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', color: '#94a3b8', fontSize: '0.875rem' }}>
                      修正说明 *
                    </label>
                    <textarea
                      value={correctionData.correction_reason}
                      onChange={(e) => setCorrectionData({...correctionData, correction_reason: e.target.value})}
                      placeholder="请说明修正原因和依据..."
                      style={{
                        width: '100%',
                        minHeight: '60px',
                        padding: '0.75rem',
                        background: '#0f172a',
                        border: '1px solid #1e293b',
                        borderRadius: '8px',
                        color: '#e2e8f0',
                        fontSize: '0.875rem',
                        resize: 'vertical'
                      }}
                    />
                  </div>

                  {/* 提交按钮 */}
                  <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                    <button
                      onClick={() => {
                        setShowCorrectionForm(false);
                        setCorrectionData({ failure_domain: '', module: '', root_cause: '', confidence: 1.0, correction_reason: '' });
                      }}
                      style={{
                        padding: '0.6rem 1.25rem',
                        background: 'transparent',
                        border: '1px solid #475569',
                        borderRadius: '8px',
                        color: '#94a3b8',
                        cursor: 'pointer',
                        fontSize: '0.875rem'
                      }}
                    >
                      取消
                    </button>
                    <button
                      onClick={handleExpertCorrection}
                      disabled={correctionSubmitting || !correctionData.failure_domain || !correctionData.root_cause || !correctionData.correction_reason}
                      style={{
                        padding: '0.6rem 1.25rem',
                        background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#ffffff',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        opacity: (correctionSubmitting || !correctionData.failure_domain || !correctionData.root_cause || !correctionData.correction_reason) ? 0.5 : 1
                      }}
                    >
                      {correctionSubmitting ? '提交中...' : '✓ 提交修正'}
                    </button>
                  </div>
                </div>
              )}

              {/* 会话信息 */}
              <div style={{
                marginTop: '1rem',
                fontSize: '0.75rem',
                color: '#475569'
              }}>
                会话ID: {data?.session_id}
              </div>
            </div>
          </div>
        );

      case 'system_response':
        return (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{
              padding: '0.75rem 1rem',
              background: 'rgba(15, 23, 42, 0.8)',
              borderRadius: '12px',
              border: '1px solid #1e293b',
              color: '#94a3b8',
              fontSize: '0.875rem'
            }}>
              <div style={{ marginBottom: '0.25rem', opacity: 0.5 }}>🤖 系统</div>
              {msg.content}
            </div>
          </div>
        );

      case 'error':
        return (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{
              padding: '0.75rem 1rem',
              background: 'rgba(239, 68, 68, 0.1)',
              borderRadius: '12px',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#ef4444',
              fontSize: '0.875rem'
            }}>
              ❌ {msg.content}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 全局样式和动画 */}
      <style>{`
        @keyframes fadeInSlide {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      {/* 顶部工具栏 */}
      <div style={{
        padding: '1rem 1.5rem',
        background: 'rgba(15, 23, 42, 0.8)',
        borderBottom: '1px solid #1e293b',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{
            margin: 0,
            fontSize: '1.25rem',
            fontWeight: '600',
            color: '#e2e8f0'
          }}>
            💬 芯片失效分析助手
          </h1>
          <p style={{
            margin: '0.25rem 0 0 0',
            fontSize: '0.875rem',
            color: '#64748b'
          }}>
            输入芯片型号和故障日志，AI助手将为您分析
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            onClick={handleNewChat}
            className="btn-secondary"
            style={{ fontSize: '0.875rem' }}
          >
            ➕ 新对话
          </button>
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => handleLoadSession(null)}
              className="btn-secondary"
              style={{ fontSize: '0.875rem' }}
            >
              📂 历史会话
            </button>

            {/* 历史会话下拉列表 */}
            {showSessionDropdown && (
              <div style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: '0.5rem',
                width: '400px',
                maxHeight: '400px',
                overflow: 'auto',
                background: 'rgba(15, 23, 42, 0.98)',
                border: '1px solid #1e293b',
                borderRadius: '12px',
                boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
                zIndex: 1000
              }}>
                <div style={{
                  padding: '1rem',
                  borderBottom: '1px solid #1e293b',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span style={{
                    color: '#e2e8f0',
                    fontSize: '0.875rem',
                    fontWeight: '600'
                  }}>
                    历史会话列表 ({availableSessions.length})
                  </span>
                  <button
                    onClick={() => setShowSessionDropdown(false)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#64748b',
                      cursor: 'pointer',
                      fontSize: '1rem',
                      padding: '0.25rem'
                    }}
                  >
                    ✕
                  </button>
                </div>

                {availableSessions.length === 0 ? (
                  <div style={{
                    padding: '2rem',
                    textAlign: 'center',
                    color: '#64748b',
                    fontSize: '0.875rem'
                  }}>
                    暂无历史会话
                  </div>
                ) : (
                  <div>
                    {availableSessions.map((session) => (
                      <div
                        key={session.session_id}
                        onClick={() => handleLoadSession(session.session_id)}
                        style={{
                          padding: '1rem',
                          borderBottom: '1px solid rgba(30, 41, 59, 0.5)',
                          cursor: 'pointer',
                          transition: 'background 0.2s',
                          ':hover': {
                            background: 'rgba(0, 212, 255, 0.1)'
                          }
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(0, 212, 255, 0.1)'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                      >
                        <div style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '0.5rem'
                        }}>
                          <div style={{
                            color: '#00d4ff',
                            fontSize: '0.75rem',
                            fontFamily: 'monospace'
                          }}>
                            {session.session_id}
                          </div>
                          <div style={{
                            padding: '0.125rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            background: session.need_expert
                              ? 'rgba(251, 191, 36, 0.2)'
                              : 'rgba(16, 185, 129, 0.2)',
                            color: session.need_expert
                              ? '#fbbf24'
                              : '#10b981'
                          }}>
                            {session.need_expert ? '需专家确认' : '自动完成'}
                          </div>
                        </div>
                        <div style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '0.75rem',
                          color: '#64748b'
                        }}>
                          <span>{session.chip_model}</span>
                          <span>
                            {session.created_at
                              ? new Date(session.created_at).toLocaleString('zh-CN', {
                                  month: '2-digit',
                                  day: '2-digit',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })
                              : '未知时间'}
                          </span>
                        </div>
                        {session.root_cause && (
                          <div style={{
                            marginTop: '0.5rem',
                            fontSize: '0.875rem',
                            color: '#94a3b8',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            {session.root_cause}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 消息区域 */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1.5rem'
      }}>
        {messages.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '4rem 2rem',
            color: '#64748b'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🤖</div>
            <div style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: '#94a3b8' }}>
              欢迎使用芯片失效分析助手
            </div>
            <div style={{ fontSize: '0.875rem', marginBottom: '2rem' }}>
              请按以下格式输入信息开始分析：
            </div>
            <div style={{
              maxWidth: '500px',
              margin: '0 auto',
              padding: '1rem',
              background: 'rgba(15, 23, 42, 0.5)',
              borderRadius: '8px',
              textAlign: 'left',
              fontSize: '0.875rem',
              color: '#94a3b8'
            }}>
              <div style={{ marginBottom: '0.5rem', color: '#00d4ff' }}>输入格式示例：</div>
              <div style={{ padding: '0.75rem', background: '#0f172a', borderRadius: '4px', fontFamily: 'monospace' }}>
                芯片型号: XC9000<br/>
                [ERROR] ERR_TIMEOUT in Communication Module<br/>
                [INFO] Supply voltage: 0.85V
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div key={msg.message_id}>
                {renderMessageContent(msg)}
              </div>
            ))}

            {/* 实时统计卡片 - 分析中显示 */}
            {analyzing && (
              <div style={{
                padding: '1rem 1.5rem',
                background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(15, 23, 42, 0.9) 100%)',
                borderRadius: '12px',
                border: '1px solid rgba(0, 212, 255, 0.3)',
                borderLeft: '4px solid #00d4ff',
                marginBottom: '1.5rem'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1rem'
                }}>
                  <div style={{
                    color: '#00d4ff',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}>
                    <div className="loading-spinner" style={{ width: '16px', height: '16px' }}></div>
                    {realTimeStats.stage || '分析中...'}
                  </div>
                  <div style={{
                    fontSize: '0.75rem',
                    color: '#64748b'
                  }}>
                    进度: {(realTimeStats.progress * 100).toFixed(0)}%
                  </div>
                </div>

                {/* 进度条 */}
                <div style={{
                  height: '6px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  borderRadius: '3px',
                  overflow: 'hidden',
                  marginBottom: '1rem'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${realTimeStats.progress * 100}%`,
                    background: 'linear-gradient(90deg, #00d4ff 0%, #0099ff 100%)',
                    borderRadius: '3px',
                    transition: 'width 0.3s ease'
                  }}></div>
                </div>

                {/* 统计数据网格 */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: '1rem'
                }}>
                  <div style={{
                    textAlign: 'center',
                    padding: '0.75rem',
                    background: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: '8px',
                    border: '1px solid rgba(0, 212, 255, 0.2)'
                  }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>已消耗时间</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#00d4ff' }}>
                      {realTimeStats.elapsed}
                    </div>
                  </div>
                  <div style={{
                    textAlign: 'center',
                    padding: '0.75rem',
                    background: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: '8px',
                    border: '1px solid rgba(0, 212, 255, 0.2)'
                  }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>预计剩余</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#10b981' }}>
                      {realTimeStats.eta}
                    </div>
                  </div>
                  <div style={{
                    textAlign: 'center',
                    padding: '0.75rem',
                    background: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: '8px',
                    border: '1px solid rgba(0, 212, 255, 0.2)'
                  }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>Token消耗</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#f59e0b' }}>
                      {realTimeStats.tokens}
                    </div>
                  </div>
                  <div style={{
                    textAlign: 'center',
                    padding: '0.75rem',
                    background: 'rgba(15, 23, 42, 0.5)',
                    borderRadius: '8px',
                    border: '1px solid rgba(0, 212, 255, 0.2)'
                  }}>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '0.25rem' }}>Token速率</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: '600', color: '#8b5cf6' }}>
                      {realTimeStats.tokenRate}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {sending && !analyzing && (
              <div style={{
                padding: '0.75rem 1rem',
                background: 'rgba(0, 212, 255, 0.1)',
                borderRadius: '12px',
                display: 'inline-block'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  color: '#00d4ff',
                  fontSize: '0.875rem'
                }}>
                  <div className="loading-spinner"></div>
                  正在思考...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 输入区域 */}
      <div style={{
        padding: '1rem 1.5rem',
        background: 'rgba(15, 23, 42, 0.8)',
        borderTop: '1px solid #1e293b'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto'
        }}>
          {/* 文件上传提示 */}
          {uploadedFile && (
            <div style={{
              marginBottom: '0.75rem',
              padding: '0.5rem 1rem',
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid #10b981',
              borderRadius: '8px',
              color: '#10b981',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <span>📄</span>
              <span>已加载: {uploadedFile.name}</span>
              <button
                onClick={() => {
                  setUploadedFile(null);
                  fileInputRef.current.value = '';
                }}
                style={{
                  marginLeft: 'auto',
                  background: 'none',
                  border: 'none',
                  color: '#ef4444',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  padding: '0.25rem 0.5rem'
                }}
              >
                ✕ 清除
              </button>
            </div>
          )}

          <div style={{
            display: 'flex',
            gap: '0.75rem'
          }}>
            {/* 文件上传按钮 */}
            <button
              onClick={triggerFileSelect}
              disabled={sending}
              className="btn-secondary"
              style={{
                minWidth: '50px',
                alignSelf: 'flex-end',
                height: '80px',
                fontSize: '1.5rem'
              }}
              title="上传日志文件"
            >
              📎
            </button>

            {/* 隐藏的文件输入 */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.log,.json,.xml"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />

            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={currentSessionId
                ? "添加更多信息、日志或纠正之前的内容... (Enter 发送, Shift+Enter 换行)"
                : "输入芯片型号和故障日志... 例如: 芯片型号: XC9000\n[ERROR] Communication timeout\n\n💡 也可点击左侧📎按钮上传日志文件"
              }
              className="textarea"
              style={{
                flex: 1,
                height: '80px',
                minHeight: '80px',
                maxHeight: '200px',
                fontFamily: 'monospace',
                resize: 'vertical'
              }}
              disabled={sending}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && !sending) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />
            <button
              onClick={handleSendMessage}
              disabled={sending || !inputText.trim()}
              className="btn-primary"
              style={{
                minWidth: '100px',
                alignSelf: 'flex-end',
                height: '80px'
              }}
            >
              {sending ? '🔄' : '📤 发送'}
            </button>
          </div>
        </div>
        {currentSessionId && (
          <div style={{
            marginTop: '0.75rem',
            textAlign: 'center',
            fontSize: '0.75rem',
            color: '#475569'
          }}>
            会话ID: {currentSessionId}
          </div>
        )}
      </div>
    </div>
  );
}
