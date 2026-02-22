"""
芯片失效分析AI Agent系统 - Streamlit前端应用
企业级商业化UI界面
"""

import streamlit as st
import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# 配置日志
logger = logging.getLogger(__name__)

# ============================================
# 配置页面
# ============================================
st.set_page_config(
    page_title="芯片失效分析AI Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 商业化UI样式
st.markdown("""
<style>
    /* ============================================
       全局样式 - 企业级设计系统
       ============================================ */

    /* 品牌色定义 - 暗色主题优化版 */
    :root {
        --primary: #00d4ff;
        --primary-dark: #0099cc;
        --primary-light: #33e0ff;
        --secondary: #64748b;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --info: #3b82f6;
        --purple: #a855f7;
        --bg-dark: #070a14;
        --bg-card: #0f172a;
        --bg-elevated: #1e293b;
        --border-dark: #1e293b;
        --border-subtle: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --gradient-primary: linear-gradient(135deg, #00d4ff 0%, #0066cc 100%);
        --gradient-purple: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
        --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
        --shadow-glow: 0 0 20px rgba(0, 212, 255, 0.3);
    }

    /* 整个页面背景 - 深色科技风 */
    html, body {
        background: #070a14 !important;
        background-color: #070a14 !important;
        color: #cbd5e1 !important;
    }

    /* 隐藏默认元素 */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem;
        max-width: 1440px;
        background: transparent !important;
    }

    /* 确保主容器有足够顶部空间 */
    .main .block-container {
        margin-top: 0 !important;
    }

    /* 主背景 - 深色科技风 */
    .main {
        background: #070a14 !important;
        background-color: #070a14 !important;
        min-height: 100vh;
        position: relative;
    }

    /* 添加背景网格效果 */
    .main::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image:
            linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
    }

    /* 侧边栏样式 - 深色科技风 */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1a 0%, #0f172a 100%) !important;
        border-right: 1px solid rgba(0, 212, 255, 0.1) !important;
    }

    /* ============================================
       头部样式 - 科技风格
       ============================================ */

    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.5rem;
        margin-top: 0;
        letter-spacing: -0.5px;
        line-height: 1.2;
        text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
        position: relative;
        z-index: 1;
    }

    .main-header::after {
        content: '';
        display: block;
        width: 80px;
        height: 4px;
        background: linear-gradient(90deg, #00d4ff, #0066cc, #a855f7);
        border-radius: 2px;
        margin-top: 1rem;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }

    .header-subtitle {
        font-size: 1rem;
        color: #00d4ff;
        margin-bottom: 2rem;
        margin-top: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        position: relative;
        z-index: 1;
    }

    /* ============================================
       卡片系统 - 科技风格
       ============================================ */

    .card {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(0, 212, 255, 0.15);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        position: relative;
        z-index: 1;
    }

    .card:hover {
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
        border-color: rgba(0, 212, 255, 0.3);
        transform: translateY(-2px);
    }

    .card-elevated {
        background: rgba(15, 23, 42, 0.9);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        border: 1px solid rgba(0, 212, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        padding: 2rem;
        margin: 1.5rem 0;
        position: relative;
        z-index: 1;
    }

    .card-elevated::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.5), transparent);
    }

    /* 卡片标题 */
    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .card-subtitle {
        font-size: 0.875rem;
        color: #00d4ff;
        margin-bottom: 1rem;
    }

    /* ============================================
       状态卡片 - 科技风格
       ============================================ */

    .status-card {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 1.25rem;
        border: 1px solid rgba(0, 212, 255, 0.15);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }

    .status-card:hover {
        border-color: rgba(0, 212, 255, 0.3);
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.15);
    }

    .status-card-success {
        border-left: 4px solid #10b981;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
    }

    .status-card-warning {
        border-left: 4px solid #f59e0b;
        box-shadow: 0 0 15px rgba(245, 158, 11, 0.2);
    }

    .status-card-error {
        border-left: 4px solid #ef4444;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.2);
    }

    .status-card-info {
        border-left: 4px solid #00d4ff;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
    }

    /* ============================================
       指标卡片 - 科技风格
       ============================================ */

    .metric-card {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid rgba(0, 212, 255, 0.15);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        min-width: 140px;
        white-space: nowrap;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 3px;
        height: 100%;
        background: linear-gradient(180deg, #00d4ff, #0066cc);
        opacity: 0.5;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.3);
        border-color: rgba(0, 212, 255, 0.4);
    }

    .metric-value-primary {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00d4ff;
        line-height: 1;
        margin: 0.75rem 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: clip;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
    }

    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
        white-space: nowrap;
    }

    .metric-change {
        font-size: 0.875rem;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
    }

    .metric-change-positive {
        color: #10b981;
    }

    .metric-change-negative {
        color: #ef4444;
    }

    /* ============================================
       按钮系统 - 科技风格
       ============================================ */

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00d4ff 0%, #0066cc 100%);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .stButton > button[kind="primary"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s ease;
    }

    .stButton > button[kind="primary"]:hover::before {
        left: 100%;
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #33e0ff 0%, #0099cc 100%);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.6);
        transform: translateY(-2px);
    }

    .stButton > button:not([kind="primary"]) {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(12px);
        color: #f1f5f9;
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 10px;
        padding: 0.625rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton > button:not([kind="primary"]):hover {
        background: rgba(51, 65, 85, 0.9);
        border-color: rgba(0, 212, 255, 0.4);
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
    }

    /* ============================================
       输入框样式 - 科技风格
       ============================================ */

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 10px;
        color: #f1f5f9;
        padding: 0.75rem 1rem;
        font-size: 0.9375rem;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #00d4ff;
        box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.2), 0 0 20px rgba(0, 212, 255, 0.1);
        background: rgba(15, 23, 42, 0.95);
        outline: none;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #64748b;
    }

    /* ============================================
       滑块样式
       ============================================ */

    .stSlider > div > div > div {
        background: #1e293b;
        border-radius: 10px;
        padding: 1rem;
    }

    /* ============================================
       展开区域 - 科技风格
       ============================================ */

    .streamlit-expanderHeader {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 212, 255, 0.15);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        color: #ffffff;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .streamlit-expanderHeader:hover {
        background: rgba(30, 41, 59, 0.9);
        border-color: rgba(0, 212, 255, 0.3);
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.1);
    }

    .streamlit-expanderContent {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 212, 255, 0.15);
        border-radius: 0 0 10px 10px;
        padding: 1.25rem;
        margin-top: 0.5rem;
        color: #94a3b8;
    }

    /* ============================================
       Radio样式 - 科技风格
       ============================================ */

    .stRadio > div {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 212, 255, 0.15);
        border-radius: 10px;
        padding: 0.75rem;
    }

    .stRadio > div > label {
        color: #ffffff;
        font-weight: 500;
    }

    /* ============================================
       信息框 - 科技风格
       ============================================ */

    .info-box {
        background: rgba(0, 212, 255, 0.1);
        backdrop-filter: blur(12px);
        border-left: 4px solid #00d4ff;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        color: #00d4ff;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.1);
    }

    .success-box {
        background: rgba(16, 185, 129, 0.1);
        backdrop-filter: blur(12px);
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        color: #10b981;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.1);
    }

    .warning-box {
        background: rgba(245, 158, 11, 0.1);
        backdrop-filter: blur(12px);
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        color: #f59e0b;
        box-shadow: 0 0 15px rgba(245, 158, 11, 0.1);
    }

    .error-box {
        background: rgba(239, 68, 68, 0.1);
        backdrop-filter: blur(12px);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        color: #ef4444;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.1);
    }

    /* ============================================
       分隔线
       ============================================ */

    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #374151, transparent);
        margin: 2rem 0;
    }

    /* ============================================
       侧边栏
       ============================================ */

    .css-1v0mbdj {
        color: #ffffff !important;
        font-weight: 600;
    }

    .sidebar-section {
        padding: 1.5rem 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .sidebar-title {
        color: #ffffff;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 1rem;
        opacity: 0.9;
    }

    /* ============================================
       数据表格
       ============================================ */

    .data-table {
        width: 100%;
        border-collapse: collapse;
        background: #1e293b;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }

    .data-table th {
        background: #0f172a;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 1rem;
        text-align: left;
        border-bottom: 1px solid #374151;
    }

    .data-table td {
        padding: 1rem;
        border-bottom: 1px solid #1e293b;
        color: #cbd5e1;
    }

    .data-table tr:hover {
        background: #1e293b;
    }

    /* ============================================
       标签和徽章 - 科技风格
       ============================================ */

    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.375rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        backdrop-filter: blur(12px);
    }

    .badge-primary {
        background: rgba(0, 212, 255, 0.15);
        color: #00d4ff;
        border: 1px solid rgba(0, 212, 255, 0.3);
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
    }

    .badge-success {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
    }

    .badge-warning {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.2);
    }

    .badge-danger {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.2);
    }

    .badge-info {
        background: rgba(0, 212, 255, 0.15);
        color: #00d4ff;
        border: 1px solid rgba(0, 212, 255, 0.3);
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
    }

    /* ============================================
       进度条 - 科技风格
       ============================================ */

    .progress-bar {
        width: 100%;
        height: 8px;
        background: rgba(30, 41, 59, 0.8);
        border-radius: 9999px;
        overflow: hidden;
        border: 1px solid rgba(0, 212, 255, 0.2);
    }

    .progress-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #00d4ff, #0066cc, #a855f7);
        border-radius: 9999px;
        transition: width 0.3s ease;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }

    /* ============================================
       加载动画 - 科技风格
       ============================================ */

    .loading-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 3rem;
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid rgba(30, 41, 59, 0.8);
        border-top-color: #00d4ff;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* ============================================
       文本样式
       ============================================ */

    h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
        font-weight: 600;
    }

    p, span, div, label {
        color: #cbd5e1;
    }

    /* 特殊处理Streamlit元素 */
    [data-testid="stMarkdownContainer"],
    [data-testid="stText"],
    [data-testid="metric-container"] {
        color: #cbd5e1 !important;
    }

    /* 代码块 */
    pre, code {
        background: #1e293b !important;
        color: #e2e8f0 !important;
        border-radius: 8px;
        padding: 1rem;
    }

    /* ============================================
       导航标签
       ============================================ */

    .nav-tabs {
        display: flex;
        gap: 0.5rem;
        background: #1e293b;
        padding: 0.375rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border: 1px solid #374151;
    }

    .nav-tab {
        padding: 0.625rem 1.25rem;
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.875rem;
        color: #94a3b8;
        background: transparent;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .nav-tab:hover {
        color: #f1f5f9;
        background: #334155;
    }

    .nav-tab-active {
        background: #3b82f6;
        color: #f1f5f9;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }

    /* ============================================
       统计图表
       ============================================ */

    .chart-container {
        background: #1e293b;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #374151;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }

    /* ============================================
       响应式
       ============================================ */

    @media (max-width: 768px) {
        .main-header {
            font-size: 1.75rem;
        }

        .card {
            padding: 1rem;
        }

        .metric-value-primary {
            font-size: 2rem;
        }
    }

    /* ============================================
       全局深色主题覆盖 - 科技风格
       ============================================ */

    /* 覆盖所有可能的白色背景 */
    div[data-testid="stAppViewContainer"],
    div[data-testid="stAppViewBlockContainer"],
    .stApp,
    [class^="stApp"],
    [class*=" stApp"] {
        background: #070a14 !important;
        background-color: #070a14 !important;
    }

    /* 确保所有容器都是透明或深色背景 */
    .stApp,
    .stApp > div,
    .stApp > div > div,
    .stApp > div > div > div {
        background: transparent !important;
    }

    /* 覆盖所有可能的白色背景元素 */
    section,
    .main > div,
    .main .block-container {
        background: transparent !important;
    }

    /* 确保所有文本都是浅色 */
    * {
        scrollbar-color: #4b5563 #1e293b !important;
    }

    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #1e293b !important;
    }

    ::-webkit-scrollbar-thumb {
        background: #4b5563 !important;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #64748b !important;
    }

    /* 确保顶部区域不被遮挡 */
    [data-testid="stAppViewBlockContainer"] {
        padding-top: 2rem !important;
    }

    /* 确保主内容区域顶部有足够空间 */
    .main .element-container:first-child {
        margin-top: 0 !important;
    }

    /* 防止任何固定定位元素遮挡标题 */
    [data-testid="stHeader"] {
        display: none;
    }

    /* ============================================
       动画效果 - 科技风格
       ============================================ */

    @keyframes pulse {
        0%, 100% {
            opacity: 1;
            transform: scale(1);
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }
        50% {
            opacity: 0.7;
            transform: scale(1.3);
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.8);
        }
    }

    @keyframes glow {
        0%, 100% {
            box-shadow: 0 0 5px rgba(0, 212, 255, 0.3);
        }
        50% {
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.6), 0 0 30px rgba(0, 212, 255, 0.3);
        }
    }

    @keyframes scanline {
        0% {
            transform: translateY(-100%);
        }
        100% {
            transform: translateY(100%);
        }
    }

    /* 进度条动画 */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00d4ff 0%, #0066cc 50%, #a855f7 100%);
        transition: width 0.3s ease;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }

    /* 卡片加载动画 */
    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }

    .loading {
        animation: shimmer 2s infinite;
        background: linear-gradient(90deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.9) 50%, rgba(15, 23, 42, 0.8) 100%);
        background-size: 1000px 100%;
    }

    /* ============================================
       额外科技风格效果
       ============================================ */

    /* 为特定元素添加扫描线效果 */
    .tech-border {
        position: relative;
        border: 1px solid rgba(0, 212, 255, 0.3);
    }

    .tech-border::before,
    .tech-border::after {
        content: '';
        position: absolute;
        width: 20px;
        height: 20px;
        border: 2px solid #00d4ff;
        opacity: 0.5;
        transition: all 0.3s ease;
    }

    .tech-border::before {
        top: -1px;
        left: -1px;
        border-right: none;
        border-bottom: none;
    }

    .tech-border::after {
        bottom: -1px;
        right: -1px;
        border-left: none;
        border-top: none;
    }

    .tech-border:hover::before,
    .tech-border:hover::after {
        width: 30px;
        height: 30px;
        opacity: 1;
    }

    /* 高亮文本效果 */
    .tech-highlight {
        color: #00d4ff;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }

    /* 为卡片添加悬停发光效果 */
    .card-glow {
        transition: all 0.3s ease;
    }

    .card-glow:hover {
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.3), inset 0 0 30px rgba(0, 212, 255, 0.05);
    }

    /* 为侧边栏添加科技风格的分隔线 */
    .tech-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent);
        margin: 1.5rem 0;
    }

    /* 为导航添加激活状态指示器 */
    .nav-active {
        position: relative;
    }

    .nav-active::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #00d4ff, #0066cc);
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# 配置和常量
# ============================================
API_BASE_URL = "http://localhost:8889"

CHIP_MODELS = [
    "XC9000",
    "XC8000",
    "XC7000",
    "XC6000",
    "自定义型号"
]

THRESHOLD_MIN = 0.0
THRESHOLD_MAX = 1.0
THRESHOLD_DEFAULT = 0.7


# ============================================
# API客户端函数
# ============================================

def check_api_health() -> bool:
    """检查API健康状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def submit_analysis(chip_model: str, raw_log: str, infer_threshold: float = 0.7, session_id: str = None) -> Dict[str, Any]:
    """提交分析请求"""
    payload = {
        "chip_model": chip_model,
        "raw_log": raw_log,
        "infer_threshold": infer_threshold
    }
    if session_id:
        payload["session_id"] = session_id

    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/analyze", json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"API错误: {response.status_code}", "detail": response.text}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时", "detail": "分析处理时间较长，请稍后重试"}
    except Exception as e:
        return {"success": False, "error": "请求失败", "detail": str(e)}


def get_statistics() -> Dict[str, Any]:
    """获取系统统计数据"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # API直接返回StatsResponse，不包装在success/data中
            if isinstance(data, dict):
                # 检查是否有data字段（旧格式）
                if "data" in data:
                    return data.get("data", {})
                # 否则直接返回数据（新格式）
                else:
                    return data
            return {}
        else:
            logger.warning(f"获取统计数据失败: {response.status_code}")
            return get_default_stats()
    except Exception as e:
        logger.warning(f"获取统计数据异常: {str(e)}")
        return get_default_stats()


def get_default_stats() -> Dict[str, Any]:
    """获取默认统计数据"""
    return {
        "today_analyses": 0,
        "success_rate": 0.0,
        "avg_duration": 0.0,
        "expert_interventions": 0,
        "total_analyses": 0,
        "today_change": 0.0,
        "duration_change": 0.0,
        "expert_change": 0.0
    }


def get_analysis_result(session_id: str) -> Dict[str, Any]:
    """获取分析结果"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/analysis/{session_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"success": False, "error": "未找到分析结果", "detail": f"会话ID {session_id} 不存在"}
        else:
            return {"success": False, "error": f"API错误: {response.status_code}", "detail": response.text}
    except Exception as e:
        return {"success": False, "error": "请求失败", "detail": str(e)}


def get_analysis_history(
    limit: int = 50,
    offset: int = 0,
    chip_model: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict[str, Any]:
    """获取分析历史记录"""
    try:
        params = {"limit": limit, "offset": offset}
        if chip_model:
            params["chip_model"] = chip_model
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = requests.get(f"{API_BASE_URL}/api/v1/history", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"records": [], "total_count": 0, "error": f"API错误: {response.status_code}"}
    except Exception as e:
        return {"records": [], "total_count": 0, "error": str(e)}


# ============================================
# UI组件函数
# ============================================

def render_header():
    """渲染页面头部 - 科技风格"""
    st.markdown('<div class="main-header">🔬 芯片失效分析AI Agent系统</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-subtitle">企业级智能故障诊断与分析平台 <span style="color: #10b981;">●</span> API在线</div>', unsafe_allow_html=True)


def render_sidebar():
    """渲染侧边栏 - 科技风格"""
    with st.sidebar:
        # Logo区域
        st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem;">
            <div style="
                width: 60px;
                height: 60px;
                margin: 0 auto 1rem;
                background: linear-gradient(135deg, #00d4ff 0%, #0066cc 100%);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
                font-size: 2rem;
            ">🔬</div>
            <div style="font-size: 1.125rem; font-weight: 700; color: #ffffff; margin-bottom: 0.25rem;">
                Chip Fault AI
            </div>
            <div style="font-size: 0.75rem; color: #00d4ff;">
                Enterprise Edition v2.0
            </div>
        </div>
        <div class="tech-divider"></div>
        """, unsafe_allow_html=True)

        # API配置
        st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-title" style="color: #00d4ff;">🔌 API配置</div>
        </div>
        """, unsafe_allow_html=True)

        api_url = st.text_input("API地址", value=API_BASE_URL, label_visibility="collapsed")

        # 芯片配置
        st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-title" style="color: #00d4ff;">💼 芯片配置</div>
        </div>
        """, unsafe_allow_html=True)

        chip_model = st.selectbox("选择芯片型号", CHIP_MODELS, label_visibility="visible")
        if chip_model == "自定义型号":
            chip_model = st.text_input("输入型号", placeholder="例如: XC5000")

        # 分析参数
        st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-title" style="color: #00d4ff;">⚙️ 分析参数</div>
        </div>
        """, unsafe_allow_html=True)

        infer_threshold = st.slider("置信度阈值", THRESHOLD_MIN, THRESHOLD_MAX, THRESHOLD_DEFAULT, 0.05, format="%.2f")

        # 系统状态
        st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-title" style="color: #00d4ff;">📊 系统状态</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("检查", use_container_width=True):
                if check_api_health():
                    st.success("✓ 在线")
                else:
                    st.error("✗ 离线")
        with col2:
            st.button("刷新", use_container_width=True, on_click=lambda: st.rerun())

        return chip_model, infer_threshold


def render_dashboard_stats():
    """渲染仪表板统计"""
    # 获取统计数据
    stats = get_statistics()

    today_analyses = stats.get("today_analyses", 0)
    success_rate = stats.get("success_rate", 0.0)
    avg_duration = stats.get("avg_duration", 0.0)
    expert_interventions = stats.get("expert_interventions", 0)

    today_change = stats.get("today_change", 0.0)
    duration_change = stats.get("duration_change", 0.0)
    expert_change = stats.get("expert_change", 0.0)

    col1, col2, col3, col4 = st.columns([1, 1, 1.3, 1.3])

    with col1:
        # 今日分析卡片
        change_class = "metric-change-positive" if today_change >= 0 else "metric-change-negative"
        change_arrow = "↑" if today_change >= 0 else "↓"
        change_value = abs(today_change)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">今日分析</div>
            <div class="metric-value-primary" style="text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);">{today_analyses}</div>
            <div class="metric-change {change_class}">
                <span>{change_arrow}</span> {change_value:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # 成功率卡片
        success_change = 0.0  # 可以后续添加历史对比
        success_change_class = "metric-change-positive" if success_change >= 0 else "metric-change-negative"
        success_change_arrow = "↑" if success_change >= 0 else "↓"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">成功率</div>
            <div class="metric-value-primary" style="color: #10b981; text-shadow: 0 0 15px rgba(16, 185, 129, 0.5);">{success_rate:.1f}%</div>
            <div class="metric-change {success_change_class}">
                <span>{success_change_arrow}</span> {abs(success_change):.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # 平均耗时卡片
        duration_class = "metric-change-positive" if duration_change <= 0 else "metric-change-negative"
        duration_arrow = "↓" if duration_change <= 0 else "↑"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">平均耗时</div>
            <div class="metric-value-primary" style="color: #a855f7; text-shadow: 0 0 15px rgba(168, 85, 247, 0.5);">{avg_duration:.1f}s</div>
            <div class="metric-change {duration_class}">
                <span>{duration_arrow}</span> {abs(duration_change):.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        # 专家介入卡片
        expert_class = "metric-change-positive" if expert_change <= 0 else "metric-change-negative"
        expert_arrow = "↓" if expert_change <= 0 else "↑"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">专家介入</div>
            <div class="metric-value-primary" style="color: #f59e0b; text-shadow: 0 0 15px rgba(245, 158, 11, 0.5);">{expert_interventions}</div>
            <div class="metric-change {expert_class}">
                <span>{expert_arrow}</span> {abs(expert_change):.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_log_input():
    """渲染日志输入区域 - 科技风格"""
    st.markdown("""
    <div class="card-elevated tech-border">
        <div class="card-title">📝 故障日志输入</div>
        <div class="card-subtitle">粘贴或上传芯片故障日志以开始智能分析</div>
    </div>
    """, unsafe_allow_html=True)

    input_method = st.radio("输入方式", ["📋 直接粘贴", "📁 文件上传"], horizontal=True, label_visibility="collapsed")

    raw_log = ""
    if input_method == "📋 直接粘贴":
        raw_log = st.text_area("日志内容", height=180, placeholder="在此粘贴芯片故障日志...\n\n支持格式：\n• 系统日志\n• 错误日志\n• 调试输出\n• JSON格式日志", label_visibility="collapsed")
    else:
        uploaded_file = st.file_uploader("选择文件", type=["txt", "log", "json"], label_visibility="collapsed")
        if uploaded_file:
            try:
                raw_log = uploaded_file.read().decode("utf-8")
                st.success(f"✓ 已加载: {uploaded_file.name}")
                with st.expander("预览内容"):
                    st.code(raw_log[:500] + "..." if len(raw_log) > 500 else raw_log)
            except Exception as e:
                st.error(f"✗ 文件读取失败: {str(e)}")

    return raw_log


def render_analysis_button(chip_model: str, raw_log: str, infer_threshold: float):
    """渲染分析按钮"""
    can_submit = bool(chip_model and raw_log)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 开始智能分析", type="primary", disabled=not can_submit, use_container_width=True, key="analyze_button"):
            if not can_submit:
                st.warning("⚠️ 请先填写芯片型号和日志内容")
                return None

            # 创建实时进度显示容器
            progress_container = st.container()

            with progress_container:
                # 进度状态卡片
                st.markdown("""
                <div class="card-elevated tech-border" style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(15, 23, 42, 0.9) 100%); border-left: 4px solid #00d4ff;">
                    <div class="card-title">⚡ 分析进度实时监控</div>
                </div>
                """, unsafe_allow_html=True)

                # 创建进度条和信息显示区域
                progress_bar = st.progress(0, "准备分析...")

                # 创建指标显示列 (给Token相关列更多空间)
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns([1, 1, 1.3, 1.3])

                with metric_col1:
                    elapsed_placeholder = st.empty()
                    elapsed_placeholder.markdown("""
                    <div class="metric-card">
                        <div class="metric-label">已用时间</div>
                        <div class="metric-value-primary" style="font-size: 1.6rem; color: #00d4ff; text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);">0.0s</div>
                    </div>
                    """, unsafe_allow_html=True)

                with metric_col2:
                    eta_placeholder = st.empty()
                    eta_placeholder.markdown("""
                    <div class="metric-card">
                        <div class="metric-label">预计剩余</div>
                        <div class="metric-value-primary" style="font-size: 1.6rem; color: #10b981; text-shadow: 0 0 15px rgba(16, 185, 129, 0.5);">计算中...</div>
                    </div>
                    """, unsafe_allow_html=True)

                with metric_col3:
                    token_placeholder = st.empty()
                    token_placeholder.markdown("""
                    <div class="metric-card">
                        <div class="metric-label">Token消耗</div>
                        <div class="metric-value-primary" style="font-size: 1.6rem; color: #f59e0b; text-shadow: 0 0 15px rgba(245, 158, 11, 0.5);">--</div>
                    </div>
                    """, unsafe_allow_html=True)

                with metric_col4:
                    speed_placeholder = st.empty()
                    speed_placeholder.markdown("""
                    <div class="metric-card">
                        <div class="metric-label">Token速率</div>
                        <div class="metric-value-primary" style="font-size: 1.6rem; color: #a855f7; text-shadow: 0 0 15px rgba(168, 85, 247, 0.5);">--</div>
                    </div>
                    """, unsafe_allow_html=True)

                # 状态显示区域
                status_placeholder = st.empty()
                status_placeholder.markdown("""
                <div class="status-card status-card-info" style="margin-top: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <div style="width: 8px; height: 8px; border-radius: 50%; background: #00d4ff; animation: pulse 2s infinite; box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);"></div>
                        <div style="font-size: 0.875rem; color: #ffffff;">初始化分析引擎...</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 记录开始时间
            start_time = time.time()
            estimated_duration = 30  # 预估30秒完成

            # 定义进度阶段和消息
            progress_stages = [
                (0.1, "📋 解析日志格式...", 2),
                (0.2, "🔍 提取故障特征...", 5),
                (0.4, "🧠 执行多源推理...", 12),
                (0.6, "🔗 知识图谱查询...", 18),
                (0.8, "📝 LLM生成分析报告...", 25),
                (0.95, "✨ 融合推理结果...", 28),
                (1.0, "✅ 分析完成", 30)
            ]

            # 使用状态容器运行分析
            result = None
            try:
                # 在后台线程中运行分析
                import threading
                import queue

                result_queue = queue.Queue()
                error_queue = queue.Queue()

                def run_analysis():
                    try:
                        result = submit_analysis(chip_model, raw_log, infer_threshold)
                        result_queue.put(result)
                    except Exception as e:
                        error_queue.put(str(e))

                # 启动分析线程
                analysis_thread = threading.Thread(target=run_analysis)
                analysis_thread.start()

                # 实时更新进度
                stage_index = 0
                last_update_time = start_time
                tokens_displayed = "--"
                speed_displayed = "--"

                while analysis_thread.is_alive():
                    current_time = time.time()
                    elapsed = current_time - start_time

                    # 更新进度阶段
                    if stage_index < len(progress_stages):
                        progress_value, stage_message, stage_time = progress_stages[stage_index]
                        if elapsed >= stage_time:
                            progress_bar.progress(progress_value, stage_message)
                            # 更新状态消息
                            current_stage_msg = stage_message
                            stage_index += 1

                    # 计算剩余时间
                    if elapsed > 0:
                        progress_ratio = min(elapsed / estimated_duration, 0.95)
                        eta = max(estimated_duration - elapsed, 0)
                        eta_minutes = int(eta // 60)
                        eta_seconds = int(eta % 60)

                        if eta_minutes > 0:
                            eta_text = f"{eta_minutes}m {eta_seconds}s"
                        else:
                            eta_text = f"{eta_seconds}s"

                        # Token消耗估算（使用更真实的增长曲线）
                        if elapsed > 3:  # 3秒后开始显示
                            # 使用指数增长曲线模拟token消耗（LLM处理通常是非线性的）
                            # 前期慢，中期快，后期趋于平稳
                            if elapsed < 8:
                                # 前期：日志解析阶段，约30-50 tokens/秒
                                estimated_tokens = int(elapsed * 35)
                                current_rate = 35
                            elif elapsed < 15:
                                # 中期：推理阶段，约60-100 tokens/秒
                                base_tokens = 8 * 35  # 前期的token
                                mid_elapsed = elapsed - 8
                                estimated_tokens = int(base_tokens + mid_elapsed * 75)
                                current_rate = 75
                            else:
                                # 后期：报告生成阶段，约100-150 tokens/秒
                                base_tokens = 8 * 35 + 7 * 75  # 前中期的token
                                late_elapsed = elapsed - 15
                                estimated_tokens = int(base_tokens + late_elapsed * 120)
                                current_rate = 120

                            tokens_displayed = f"{estimated_tokens:,}"
                            speed_displayed = f"~{current_rate}/s"

                        # 更新显示
                        elapsed_placeholder.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">已用时间</div>
                            <div class="metric-value-primary" style="font-size: 1.6rem; color: #00d4ff; text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);">{elapsed:.1f}s</div>
                        </div>
                        """, unsafe_allow_html=True)

                        eta_placeholder.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">预计剩余</div>
                            <div class="metric-value-primary" style="font-size: 1.6rem; color: #10b981; text-shadow: 0 0 15px rgba(16, 185, 129, 0.5);">{eta_text}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        token_placeholder.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Token消耗</div>
                            <div class="metric-value-primary" style="font-size: 1.6rem; color: #f59e0b; text-shadow: 0 0 15px rgba(245, 158, 11, 0.5);">{tokens_displayed}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        speed_placeholder.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Token速率</div>
                            <div class="metric-value-primary" style="font-size: 1.6rem; color: #a855f7; text-shadow: 0 0 15px rgba(168, 85, 247, 0.5);">{speed_displayed}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # 获取当前阶段消息
                        if stage_index > 0:
                            current_stage_msg = progress_stages[min(stage_index - 1, len(progress_stages) - 1)][1]
                        else:
                            current_stage_msg = "🚀 初始化分析..."

                        status_placeholder.markdown(f"""
                        <div class="status-card status-card-info" style="margin-top: 1rem;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <div style="width: 8px; height: 8px; border-radius: 50%; background: #00d4ff; animation: pulse 2s infinite; box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);"></div>
                                <div style="font-size: 0.875rem; color: #ffffff;">{current_stage_msg}</div>
                            </div>
                            <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.5rem;">
                                进度: {int(progress_ratio * 100)}% | 已耗时: {elapsed:.1f}s
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # 等待一段时间再更新
                    time.sleep(0.3)

                # 分析完成，获取结果
                analysis_thread.join(timeout=2)

                if not result_queue.empty():
                    result = result_queue.get()
                elif not error_queue.empty():
                    result = {"success": False, "error": "分析失败", "detail": error_queue.get()}

                # 最终更新
                total_elapsed = time.time() - start_time
                progress_bar.progress(1.0, "✅ 分析完成")

                # 从结果中获取实际token消耗（如果有）
                if result and result.get("success"):
                    data = result.get("data", {})
                    tokens_used = data.get("tokens_used", 0)
                    if tokens_used > 0:
                        tokens_displayed = f"{tokens_used:,}"
                        speed_displayed = f"{int(tokens_used / total_elapsed)}/s"

                # 更新最终显示
                elapsed_placeholder.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">已用时间</div>
                    <div class="metric-value-primary" style="font-size: 1.6rem; color: #00d4ff; text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);">{total_elapsed:.1f}s</div>
                </div>
                """, unsafe_allow_html=True)

                eta_placeholder.markdown("""
                <div class="metric-card">
                    <div class="metric-label">预计剩余</div>
                    <div class="metric-value-primary" style="font-size: 1.6rem; color: #10b981; text-shadow: 0 0 15px rgba(16, 185, 129, 0.5);">完成</div>
                </div>
                """, unsafe_allow_html=True)

                token_placeholder.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Token消耗</div>
                    <div class="metric-value-primary" style="font-size: 1.6rem; color: #f59e0b; text-shadow: 0 0 15px rgba(245, 158, 11, 0.5);">{tokens_displayed}</div>
                </div>
                """, unsafe_allow_html=True)

                speed_placeholder.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Token速率</div>
                    <div class="metric-value-primary" style="font-size: 1.6rem; color: #a855f7; text-shadow: 0 0 15px rgba(168, 85, 247, 0.5);">{speed_displayed}</div>
                </div>
                """, unsafe_allow_html=True)

                status_placeholder.markdown("""
                <div class="status-card status-card-success" style="margin-top: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <div style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 10px rgba(16, 185, 129, 0.8);"></div>
                        <div style="font-size: 0.875rem; color: #ffffff;">✅ 分析完成！正在生成报告...</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 添加完成动画效果
                time.sleep(0.5)

                # 分析完成后，结果会返回给调用者显示
                # 不使用st.rerun()，这样用户可以看到分析结果

            except Exception as e:
                progress_container.empty()
                st.error(f"❌ 分析过程中出现错误: {str(e)}")
                return None

            return result
    return None


def render_result(result: Dict[str, Any]):
    """渲染分析结果"""
    if not result or not result.get("success"):
        if result:
            st.markdown(f"""
            <div class="status-card status-card-error">
                <strong>❌ 分析失败</strong><br>
                {result.get("error", "未知错误")}
            </div>
            """, unsafe_allow_html=True)
        return

    # 分析完成后，获取最新统计并显示更新提示
    latest_stats = get_statistics()
    today_count = latest_stats.get("today_analyses", 0)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem; color: white;">
            <span style="font-size: 1.25rem;">✅</span>
            <div>
                <div style="font-weight: 600; font-size: 0.95rem;">分析已完成并保存</div>
                <div style="font-size: 0.8rem; opacity: 0.9;">今日已完成 {today_count} 次分析</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    data = result.get("data", {})

    # 概览卡片
    col1, col2, col3 = st.columns(3)
    with col1:
        domain = data.get("final_root_cause", {}).get("failure_domain", "未知")
        st.markdown(f"""
        <div class="status-card status-card-info">
            <div class="metric-label">失效域</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #60a5fa; margin-top: 0.5rem;">
                {domain.upper()}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        confidence = data.get("final_root_cause", {}).get("confidence", 0) * 100
        color_class = "metric-change-positive" if confidence >= 70 else "metric-change-negative"
        st.markdown(f"""
        <div class="status-card status-card-success">
            <div class="metric-label">置信度</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #34d399; margin-top: 0.5rem;">
                {confidence:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        need_expert = data.get("need_expert", False)
        status = "需要专家" if need_expert else "自动完成"
        status_class = "status-card-warning" if need_expert else "status-card-success"
        st.markdown(f"""
        <div class="status-card {status_class}">
            <div class="metric-label">分析状态</div>
            <div style="font-size: 1rem; font-weight: 600; margin-top: 0.5rem;">
                {"⚠️ " + status if need_expert else "✓ " + status}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 根因分析
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
        <div class="card-title">🎯 根因分析</div>
    </div>
    """, unsafe_allow_html=True)

    root_cause = data.get("final_root_cause", {})
    st.markdown(f"""
    <div class="card">
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            <div>
                <div class="metric-label">失效模块</div>
                <div style="font-size: 1.125rem; font-weight: 600; color: #f1f5f9;">
                    {root_cause.get("module", "未知").upper()}
                </div>
            </div>
            <div>
                <div class="metric-label">根因分类</div>
                <div style="font-size: 1.125rem; font-weight: 600; color: #f1f5f9;">
                    {root_cause.get("root_cause_category", "未知")}
                </div>
            </div>
        </div>
        <div style="margin-top: 1rem;">
            <div class="metric-label">根本原因</div>
            <div style="background: #0f172a; padding: 1rem; border-radius: 8px; margin-top: 0.5rem; color: #cbd5e1;">
                {root_cause.get("root_cause", "未知")}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # LLM生成的分析报告
    infer_report = data.get("infer_report")
    if infer_report:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <div class="card-title">📝 AI分析报告</div>
        </div>
        """, unsafe_allow_html=True)

        # 检查报告类型
        report_type = data.get("report_type", "unknown")

        if report_type == "llm":
            # LLM生成的Markdown报告
            st.markdown(f"""
            <div class="card">
                <div style="background: #0f172a; padding: 1.5rem; border-radius: 8px; color: #e2e8f0; line-height: 1.8;">
                    {infer_report}
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif infer_report.endswith(('.html', '.htm')):
            # 模板生成的HTML报告 - 显示链接
            st.markdown(f"""
            <div class="card">
                <div style="background: #0f172a; padding: 1rem; border-radius: 8px; color: #cbd5e1;">
                    <div class="metric-label">报告文件</div>
                    <div style="margin-top: 0.5rem;">
                        📄 <a href="{infer_report}" target="_blank" style="color: #60a5fa;">查看详细报告</a>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 其他格式的报告
            st.markdown(f"""
            <div class="card">
                <div style="background: #0f172a; padding: 1.5rem; border-radius: 8px; color: #e2e8f0; white-space: pre-wrap;">
                    {infer_report}
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_session_query():
    """渲染历史查询"""
    st.markdown("""
    <div class="card">
        <div class="card-title">🔍 历史记录查询</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        session_id = st.text_input("会话ID", placeholder="输入会话ID...", label_visibility="collapsed")
    with col2:
        st.write("")  # 占位
        if st.button("查询", use_container_width=True):
            if session_id:
                result = get_analysis_result(session_id)
                render_result(result)


def render_case_browser():
    """渲染案例库"""
    st.markdown("""
    <div class="card-elevated">
        <div class="card-title">📚 案例库</div>
        <div class="card-subtitle">历史失效案例与解决方案</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/cases", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                cases = data.get("data", [])

                # 筛选
                col1, col2 = st.columns(2)
                with col1:
                    chip_filter = st.selectbox("芯片型号", ["全部"] + ["XC9000", "XC8000", "XC7000"], label_visibility="collapsed")
                with col2:
                    domain_filter = st.selectbox("失效域", ["全部"] + ["compute", "cache", "memory", "interconnect"], label_visibility="collapsed")

                # 统计
                filtered = cases
                if chip_filter != "全部":
                    filtered = [c for c in filtered if c.get("chip_model") == chip_filter]
                if domain_filter != "全部":
                    filtered = [c for c in filtered if c.get("failure_domain") == domain_filter]

                st.markdown(f"""
                <div class="info-box">
                    找到 <strong>{len(filtered)}</strong> 个相关案例
                </div>
                """, unsafe_allow_html=True)

                # ��表
                for case in filtered[:10]:
                    with st.expander(f"📋 {case.get('id', 'N/A')} - {case.get('root_cause', 'N/A')[:50]}"):
                        st.markdown(f"""
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem;">
                            <div>
                                <span class="badge badge-info">{case.get('chip_model', 'N/A')}</span>
                            </div>
                            <div>
                                <span class="badge badge-warning">{case.get('failure_domain', 'N/A').upper()}</span>
                            </div>
                            <div>
                                <span class="badge badge-danger">{case.get('severity', 'N/A')}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if case.get("solution"):
                            st.markdown(f"""
                            <div class="success-box">
                                <strong>💡 解决方案:</strong><br>
                                {case['solution']}
                            </div>
                            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"获取案例失败: {str(e)}")


def render_system_info():
    """渲染系统信息"""
    st.markdown("""
    <div class="card-elevated">
        <div class="card-title">ℹ️ 系统信息</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">💻 支持的模块</div>
            <div style="line-height: 2;">
                <div><strong>计算子系统</strong><br><span style="color: #94a3b8;">CPU • L3 Cache</span></div>
                <div><strong>内存子系统</strong><br><span style="color: #94a3b8;">DDR Controller • HBM Controller</span></div>
                <div><strong>互连子系统</strong><br><span style="color: #94a3b8;">Home Agent • NoC Router</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-title">🔧 支持的芯片</div>
            <div style="line-height: 2;">
                <div><strong>XC9000</strong> <span style="color: #94a3b8; font-size: 0.875rem;">7nm ARMv9 高性能</span></div>
                <div><strong>XC8000</strong> <span style="color: #94a3b8; font-size: 0.875rem;">12nm ARMv8 标准版</span></div>
                <div><strong>XC7000</strong> <span style="color: #94a3b8; font-size: 0.875rem;">14nm ARMv8 入门级</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def show_history_page():
    """显示历史分析记录页面"""
    st.markdown("""
    <div class="card-elevated" style="border-left: 4px solid #3b82f6;">
        <div class="card-title">📋 分析历史记录</div>
        <div class="card-subtitle">查看和检索历史分析结果</div>
    </div>
    """, unsafe_allow_html=True)

    # 筛选选项
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        filter_chip = st.text_input("芯片型号", placeholder="输入芯片型号筛选", key="page_history_filter_chip")
    with col2:
        filter_date = st.date_input("日期", key="page_history_filter_date", value=None)
    with col3:
        limit = st.selectbox("显示数量", [10, 20, 50, 100], index=2, key="page_history_limit")
    with col4:
        st.write("")
        if st.button("刷新", use_container_width=True, key="page_history_refresh"):
            st.rerun()

    # 获取历史数据
    from datetime import datetime
    date_from = None
    date_to = None
    if filter_date:
        date_from = datetime.combine(filter_date, datetime.min.time())
        date_to = datetime.combine(filter_date, datetime.max.time())

    history_data = get_analysis_history(
        limit=limit,
        offset=0,
        chip_model=filter_chip if filter_chip else None,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None
    )

    records = history_data.get("records", [])
    total_count = history_data.get("total_count", 0)

    # 显示统计信息
    st.markdown(f"""
    <div style="color: #94a3b8; font-size: 0.875rem; margin-bottom: 1rem;">
        共找到 <strong style="color: #60a5fa;">{total_count}</strong> 条记录
    </div>
    """, unsafe_allow_html=True)

    if not records:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #94a3b8;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📭</div>
            <div>暂无分析记录</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # 显示历史记录列表
    for idx, record in enumerate(records):
        with st.container():
            # 格式化时间
            created_at = record.get("created_at", "")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = created_at[:19]
            else:
                time_str = "未知时间"

            # 状态颜色
            status = record.get("status", "unknown")
            if status == "completed":
                status_color = "#10b981"
                status_text = "✓ 完成"
            elif status == "pending":
                status_color = "#f59e0b"
                status_text = "⏳ 处理中"
            else:
                status_color = "#ef4444"
                status_text = "✗ 失败"

            # 置信度颜色
            confidence = record.get("confidence", 0)
            if confidence >= 0.7:
                conf_color = "#10b981"
            elif confidence >= 0.5:
                conf_color = "#f59e0b"
            else:
                conf_color = "#ef4444"

            # 处理时长
            duration = record.get("processing_duration")
            duration_str = f"{duration:.1f}s" if duration else "N/A"

            st.markdown(f"""
            <div class="card" style="margin-bottom: 1rem; border-left: 3px solid {status_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div>
                        <strong style="color: #e2e8f0;">{record.get('chip_model', 'Unknown')}</strong>
                        <span style="color: #94a3b8; font-size: 0.875rem; margin-left: 0.5rem;">{record.get('session_id', '')[:12]}...</span>
                    </div>
                    <div style="color: {status_color}; font-weight: 600;">{status_text}</div>
                </div>
                <div style="font-size: 0.875rem; color: #cbd5e1; margin-bottom: 0.5rem;">
                    🕒 {time_str} | ⏱️ {duration_str} | 📊 置信度: <span style="color: {conf_color};">{confidence:.0%}</span>
                </div>
                <div style="font-size: 0.875rem; color: #94a3b8;">
                    🎯 失效域: {record.get('failure_domain') or 'N/A'} | 💡 根因: {(record.get('root_cause') or 'N/A')[:30]}...
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 查看详情按钮
            if st.button("📄 查看详情", key=f"page_view_detail_{idx}", use_container_width=True):
                # 获取完整分析结果并显示
                full_result = get_analysis_result(record.get("session_id", ""))
                if full_result and full_result.get("success") and full_result.get("data"):
                    st.session_state["detail_result"] = full_result["data"]
                    st.session_state["show_detail_dialog"] = True
                    st.rerun()
                else:
                    st.error(f"无法获取分析结果: {full_result.get('error', 'Unknown error')}")

            st.markdown("<br>", unsafe_allow_html=True)


def show_history_dialog():
    """显示历史分析记录对话框"""
    st.markdown("""
    <div class="card-elevated" style="border-left: 4px solid #3b82f6;">
        <div class="card-title">📋 分析历史记录</div>
        <div class="card-subtitle">查看和检索历史分析结果</div>
    </div>
    """, unsafe_allow_html=True)

    # 筛选选项
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        filter_chip = st.text_input("芯片型号", placeholder="输入芯片型号筛选", key="history_filter_chip")
    with col2:
        filter_date = st.date_input("日期", key="history_filter_date", value=None)
    with col3:
        limit = st.selectbox("显示数量", [10, 20, 50, 100], index=2, key="history_limit")
    with col4:
        st.write("")
        if st.button("刷新", use_container_width=True, key="history_refresh"):
            st.rerun()

    # 获取历史数据
    from datetime import datetime
    date_from = None
    date_to = None
    if filter_date:
        date_from = datetime.combine(filter_date, datetime.min.time())
        date_to = datetime.combine(filter_date, datetime.max.time())

    history_data = get_analysis_history(
        limit=limit,
        offset=0,
        chip_model=filter_chip if filter_chip else None,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None
    )

    records = history_data.get("records", [])
    total_count = history_data.get("total_count", 0)

    # 显示统计信息
    st.markdown(f"""
    <div style="color: #94a3b8; font-size: 0.875rem; margin-bottom: 1rem;">
        共找到 <strong style="color: #60a5fa;">{total_count}</strong> 条记录
    </div>
    """, unsafe_allow_html=True)

    if not records:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #94a3b8;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📭</div>
            <div>暂无分析记录</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # 显示历史记录列表
    for idx, record in enumerate(records):
        with st.container():
            # 格式化时间
            created_at = record.get("created_at", "")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = created_at[:19]
            else:
                time_str = "未知时间"

            # 状态颜色
            status = record.get("status", "unknown")
            if status == "completed":
                status_color = "#10b981"
                status_text = "✓ 完成"
            elif status == "pending":
                status_color = "#f59e0b"
                status_text = "⏳ 处理中"
            else:
                status_color = "#ef4444"
                status_text = "✗ 失败"

            # 置信度颜色
            confidence = record.get("confidence", 0)
            if confidence >= 0.7:
                conf_color = "#10b981"
            elif confidence >= 0.5:
                conf_color = "#f59e0b"
            else:
                conf_color = "#ef4444"

            # 处理时长
            duration = record.get("processing_duration")
            duration_str = f"{duration:.1f}s" if duration else "N/A"

            st.markdown(f"""
            <div class="card" style="margin-bottom: 1rem; border-left: 3px solid {status_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div>
                        <strong style="color: #e2e8f0;">{record.get('chip_model', 'Unknown')}</strong>
                        <span style="color: #94a3b8; font-size: 0.875rem; margin-left: 0.5rem;">{record.get('session_id', '')[:12]}...</span>
                    </div>
                    <div style="color: {status_color}; font-weight: 600;">{status_text}</div>
                </div>
                <div style="font-size: 0.875rem; color: #cbd5e1; margin-bottom: 0.5rem;">
                    🕒 {time_str} | ⏱️ {duration_str} | 📊 置信度: <span style="color: {conf_color};">{confidence:.0%}</span>
                </div>
                <div style="font-size: 0.875rem; color: #94a3b8;">
                    🎯 失效域: {record.get('failure_domain') or 'N/A'} | 💡 根因: {(record.get('root_cause') or 'N/A')[:30]}...
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 查看详情按钮
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("📄 查看详情", key=f"view_detail_{idx}", use_container_width=True):
                    # 获取完整分析结果并显示
                    full_result = get_analysis_result(record.get("session_id", ""))
                    if full_result and full_result.get("success") and full_result.get("data"):
                        st.session_state["detail_result"] = full_result["data"]
                        st.session_state["show_detail_dialog"] = True
                    else:
                        st.error(f"无法获取分析结果: {full_result.get('error', 'Unknown error')}")
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

    # 关闭按钮
    if st.button("✖ 关闭", key="close_history"):
        st.session_state["show_history_dialog"] = False
        st.rerun()


def show_detail_dialog():
    """显示分析结果详情对话框"""
    if "detail_result" not in st.session_state:
        st.session_state["show_detail_dialog"] = False
        st.rerun()
        return

    result = st.session_state["detail_result"]

    st.markdown("""
    <div class="card-elevated" style="border-left: 4px solid #10b981;">
        <div class="card-title">📄 分析结果详情</div>
    </div>
    """, unsafe_allow_html=True)

    # 显示完整结果
    render_result(result)

    # 关闭按钮
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("✖ 返回", key="close_detail", use_container_width=True):
            st.session_state["show_detail_dialog"] = False
            st.session_state["detail_result"] = None
            # 返回时保持在当前页面（历史记录页面）
            st.rerun()


# ============================================
# 主应用
# ============================================

def main():
    # 初始化session state
    if "show_history_dialog" not in st.session_state:
        st.session_state["show_history_dialog"] = False
    if "show_detail_dialog" not in st.session_state:
        st.session_state["show_detail_dialog"] = False
    if "detail_result" not in st.session_state:
        st.session_state["detail_result"] = None
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "日志分析"

    # 显示详情对话框（如果激活）
    if st.session_state.get("show_detail_dialog"):
        show_detail_dialog()
        return

    # 显示历史对话框（如果激活）
    if st.session_state.get("show_history_dialog"):
        show_history_dialog()
        return

    # 渲染头部
    render_header()

    # 仪表板统计
    render_dashboard_stats()

    st.markdown("<br>", unsafe_allow_html=True)

    # 渲染侧边栏
    chip_model, infer_threshold = render_sidebar()

    # 导航
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div class="sidebar-section">
        <div class="sidebar-title">📁 功能导航</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.sidebar.radio("选择功能页面", ["📋 日志分析", "📜 历史记录", "📚 案例库", "⚙️ 系统信息"], label_visibility="collapsed")

    # 记录当前页面
    st.session_state["current_page"] = page

    # 主内容区
    # 清理页面名称中的表情符号
    page_clean = page.split(" ", 1)[-1] if " " in page else page

    if page_clean == "日志分析":
        raw_log = render_log_input()
        st.markdown("<br>", unsafe_allow_html=True)
        result = render_analysis_button(chip_model, raw_log, infer_threshold)
        if result:
            st.markdown("<br>", unsafe_allow_html=True)
            render_result(result)
        st.markdown("<br>", unsafe_allow_html=True)
        render_session_query()

    elif page_clean == "历史记录":
        show_history_page()

    elif page_clean == "案例库":
        render_case_browser()

    elif page_clean == "系统信息":
        render_system_info()

    # 页脚
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem; color: #64748b; font-size: 0.875rem;">
        <div style="margin-bottom: 0.5rem; color: #00d4ff;">© 2024 芯片失效分析AI Agent系统 | 企业版 v2.0</div>
        <div style="font-size: 0.75rem;">技术支持: support@chipfault.ai | 官网: www.chipfault.ai</div>
        <div style="margin-top: 1rem; font-size: 0.7rem; color: #475569;">
            Powered by LangGraph + GLM-4.7 + Claude
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
