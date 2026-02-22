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
  }
};

export default api;
