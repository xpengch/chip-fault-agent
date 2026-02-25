const API_BASE_URL = 'http://localhost:8889';

// 内存缓存：存储新分析的完整结果（包含 infer_report）
// 键: session_id, 值: 完整的 analysis data
const analysisCache = new Map();

// API客户端函数
export const api = {
  // 检查API健康状态
  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      return response.ok;
    } catch {
      return false;
    }
  },

  // 提交分析请求
  async submitAnalysis(chipModel, rawLog, inferThreshold = 0.7, sessionId = null) {
    const payload = {
      chip_model: chipModel,
      raw_log: rawLog,
      infer_threshold: inferThreshold,
    };
    if (sessionId) {
      payload.session_id = sessionId;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const responseData = await response.json();

      // 后端已经返回 { success: true, data: {...} } 格式
      // 直接返回后端的响应
      if (response.ok) {
        console.log('API Raw Response:', responseData); // 调试
        // 缓存完整的结果数据（包含 infer_report）
        if (responseData.success && responseData.data?.session_id) {
          analysisCache.set(responseData.data.session_id, responseData.data);
          console.log('已缓存分析结果:', responseData.data.session_id);
        }
        return responseData;
      } else {
        return {
          success: false,
          error: `API错误: ${response.status}`,
          detail: JSON.stringify(responseData)
        };
      }
    } catch (error) {
      return {
        success: false,
        error: '请求失败',
        detail: error.message
      };
    }
  },

  // 获取系统统计数据
  async getStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/stats`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        // API直接返回StatsResponse，不包装在success/data中
        if (typeof data === 'object' && data !== null) {
          // 检查是否有data字段（旧格式）
          if ('data' in data) {
            return data.data || {};
          }
          // 否则直接返回数据（新格式）
          return data;
        }
        return {};
      } else {
        console.warn(`获取统计数据失败: ${response.status}`);
        return this.getDefaultStats();
      }
    } catch (error) {
      console.warn(`获取统计数据异常: ${error.message}`);
      return this.getDefaultStats();
    }
  },

  // 获取默认统计数据
  getDefaultStats() {
    return {
      today_analyses: 0,
      success_rate: 0.0,
      avg_duration: 0.0,
      expert_interventions: 0,
      total_analyses: 0,
      today_change: 0.0,
      duration_change: 0.0,
      expert_change: 0.0
    };
  },

  // 获取分析结果
  async getAnalysisResult(sessionId) {
    // 先检查缓存（新分析可能在缓存中有完整数据包含 infer_report）
    if (analysisCache.has(sessionId)) {
      console.log('从缓存获取分析结果:', sessionId);
      return { success: true, data: analysisCache.get(sessionId) };
    }

    // 缓存中没有，从API查询
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${sessionId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        return { success: true, data };
      } else if (response.status === 404) {
        return {
          success: false,
          error: '未找到分析结果',
          detail: `会话ID ${sessionId} 不存在`
        };
      } else {
        return {
          success: false,
          error: `API错误: ${response.status}`,
          detail: response.statusText
        };
      }
    } catch (error) {
      return {
        success: false,
        error: '请求失败',
        detail: error.message
      };
    }
  },

  // 获取分析历史记录
  async getHistory(limit = 50, offset = 0, chipModel = null, dateFrom = null, dateTo = null) {
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString()
      });
      if (chipModel) params.append('chip_model', chipModel);
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await fetch(`${API_BASE_URL}/api/v1/history?${params}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        return await response.json();
      } else {
        return { records: [], total_count: 0, error: `API错误: ${response.status}` };
      }
    } catch (error) {
      return { records: [], total_count: 0, error: error.message };
    }
  },

  // 获取案例库
  async getCases() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/cases`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        return await response.json();
      } else {
        return { success: false, data: [] };
      }
    } catch (error) {
      return { success: false, data: [] };
    }
  },

  // ==================== 多轮对话 API ====================

  // 添加消息到会话
  async addMessage(sessionId, content, contentType = 'text', correctionTarget = null, chipModel = null) {
    try {
      const payload = {
        content: content,
        content_type: contentType,
      };
      if (chipModel) payload.chip_model = chipModel;
      if (correctionTarget) payload.correction_target = correctionTarget;

      const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${sessionId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        // 缓存分析结果
        if (data.success && data.analysis_result?.session_id) {
          analysisCache.set(data.analysis_result.session_id, data.analysis_result);
        }
        return data;
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || '添加消息失败' };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // 获取会话对话历史
  async getConversationHistory(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${sessionId}/messages`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.ok) {
        return await response.json();
      } else {
        return { success: false, messages: [], error: '获取对话历史失败' };
      }
    } catch (error) {
      return { success: false, messages: [], error: error.message };
    }
  },

  // 纠正之前的信息
  async correctInformation(sessionId, targetMessageId, correctedContent, reason = null) {
    try {
      const payload = {
        target_message_id: targetMessageId,
        corrected_content: correctedContent,
      };
      if (reason) payload.reason = reason;

      const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${sessionId}/correct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        return await response.json();
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || '纠正信息失败' };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // 获取分析时间线
  async getTimeline(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${sessionId}/timeline`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.ok) {
        return await response.json();
      } else {
        return { success: true, timeline: [], total_entries: 0 };
      }
    } catch (error) {
      return { success: true, timeline: [], total_entries: 0 };
    }
  },

  // 回滚到之前的状态
  async rollbackToMessage(sessionId, messageSequence) {
    try {
      const payload = {
        message_sequence: messageSequence,
      };

      const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${sessionId}/rollback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        return await response.json();
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || '回滚失败' };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // ==================== 专家修正 API ====================

  /**
   * 提交专家修正
   * @param {string} analysisId - 分析ID/会话ID
   * @param {object} correctionData - 修正数据
   * @param {string} correctionData.failure_domain - 失效域
   * @param {string} correctionData.module - 失效模块
   * @param {string} correctionData.root_cause - 根因
   * @param {number} correctionData.confidence - 置信度 (0-1)
   * @param {string} correctionData.correction_reason - 修正原因
   */
  async submitExpertCorrection(analysisId, correctionData) {
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/expert/corrections/${analysisId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify(correctionData)
      });

      if (response.ok) {
        return await response.json();
      } else {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || error.message || '提交修正失败'
        };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  /**
   * 获取专家修正列表
   * @param {string} status - 筛选状态 (pending/approved/rejected)
   * @param {number} skip - 跳过记录数
   * @param {number} limit - 返回记录数
   */
  async getExpertCorrections(status = null, skip = 0, limit = 50) {
    const token = localStorage.getItem('access_token');
    let url = `${API_BASE_URL}/api/v1/expert/corrections?skip=${skip}&limit=${limit}`;
    if (status) url += `&status=${status}`;

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      });

      if (response.ok) {
        return await response.json();
      } else {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || error.message || '获取修正列表失败'
        };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  /**
   * 批准专家修正
   * @param {string} correctionId - 修正ID
   * @param {string} comments - 批准意见 (可选)
   */
  async approveExpertCorrection(correctionId, comments = null) {
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/expert/corrections/${correctionId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        ...(comments && { body: JSON.stringify({ comments }) })
      });

      if (response.ok) {
        return await response.json();
      } else {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || error.message || '批准修正失败'
        };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  /**
   * 拒绝专家修正
   * @param {string} correctionId - 修正ID
   * @param {string} reason - 拒绝原因
   */
  async rejectExpertCorrection(correctionId, reason) {
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/expert/corrections/${correctionId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({ reason })
      });

      if (response.ok) {
        return await response.json();
      } else {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || error.message || '拒绝修正失败'
        };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  /**
   * 获取知识学习统计
   */
  async getKnowledgeStatistics() {
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/expert/knowledge/statistics`, {
        method: 'GET',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      });

      if (response.ok) {
        return await response.json();
      } else {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || error.message || '获取统计失败'
        };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

export default api;
