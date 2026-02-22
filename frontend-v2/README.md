# 芯片失效分析AI Agent系统 - 前端

## 项目概述

企业级芯片失效分析AI Agent系统的现代化Web前端，采用工业科技（Industrial Tech）设计风格。

### 设计特色

- **工业实验室仪器美学** - 类似电子显微镜、实验室分析设备的专业界面
- **HUD式界面元素** - 十字准星、测量标记、扫描线效果
- **动态电路板背景** - 模拟芯片内部电流流动的动画效果
- **实时数据可视化** - 分析过程的动画化展示
- **响应式设计** - 完美适配桌面和移动设备

### 技术栈

- **框架**: React 18 + Vite
- **状态管理**: Zustand
- **路由**: React Router v6
- **UI动画**: Framer Motion
- **数据可视化**: Recharts
- **HTTP客户端**: Axios
- **图标**: Lucide React
- **样式**: CSS-in-JS + CSS Variables

### 核心功能

1. **日志分析** (`/analyze`)
   - 芯片型号选择与配置
   - 故障日志输入（粘贴/上传）
   - 实时分析进度显示
   - 分析结果可视化

2. **历史记录** (`/history`)
   - 历史分析记录浏览
   - 多维度筛选（芯片型号、日期）
   - 详细结果查看
   - JSON数据导出

3. **案例库** (`/cases`)
   - 历史失效案例浏览
   - 按芯片/域/严重度筛选
   - 解决方案展示
   - 验证状态标识

4. **系统信息** (`/system`)
   - 系统健康状态监控
   - 支持的芯片型号展示
   - 支持的模块列表
   - 系统统计数据

### 安装与运行

```bash
# 安装依赖
npm install

# 复制环境变量文件
cp .env.example .env

# 开发模式运行
npm run dev

# 生产构建
npm run build

# 预览生产构建
npm run preview
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VITE_API_URL` | 后端API地址 | `http://localhost:8889` |
| `VITE_APP_TITLE` | 应用标题 | `Chip Fault AI Agent` |
| `VITE_APP_VERSION` | 应用版本 | `2.0.0` |

### 目录结构

```
frontend-v2/
├── src/
│   ├── components/
│   │   ├── layout/       # 布局组件
│   │   └── ui/           # UI组件库
│   ├── pages/            # 页面组件
│   ├── lib/              # 工具库
│   ├── store/            # 状态管理
│   ├── App.jsx           # 根组件
│   ├── main.jsx          # 入口文件
│   └── index.css         # 全局样式
├── public/               # 静态资源
├── index.html            # HTML模板
├── vite.config.js        # Vite配置
└── package.json          # 项目配置
```

### 设计系统

#### 配色方案

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 主背景 | `#070a14` | 深空蓝黑 |
| 次背景 | `#0a0f1e` | 深蓝灰 |
| 卡片背景 | `rgba(17, 24, 39, 0.8)` | 半透明 |
| 主强调色 | `#00d4ff` | 电光蓝 |
| 次强调色 | `#7c3aed` | 紫色 |
| 成功色 | `#00ff9d` | 霓虹绿 |
| 警告色 | `#ff9500` | 琥珀色 |
| 错误色 | `#ff375f` | 玫瑰红 |

#### 字体系统

- **显示字体**: JetBrains Mono（标题、技术文本）
- **正文字体**: Manrope（内容文本）

### API集成

前端通过以下端点与后端通信：

```
GET  /api/v1/health          # 健康检查
GET  /api/v1/stats           # 系统统计
POST /api/v1/analyze         # 提交分析
GET  /api/v1/analysis/:id    # 获取结果
GET  /api/v1/history         # 历史记录
GET  /api/v1/cases           # 案例库
GET  /api/v1/modules         # 支持的模块
GET  /api/v1/chips           # 支持的芯片
```

### 浏览器支持

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

### 开发说明

#### 添加新页面

1. 在 `src/pages/` 创建页面组件
2. 在 `src/components/layout/Layout.jsx` 的导航数组中添加路由
3. 在 `src/App.jsx` 中添加路由配置

#### 添加UI组件

UI组件放在 `src/components/ui/` 目录下，遵循以下约定：
- 使用 CSS Variables 进行样式定制
- 支持 `className` prop 进行样式扩展
- 使用 Framer Motion 添加动效

#### 状态管理

使用 Zustand 进行全局状态管理，store定义在 `src/store/useStore.js`：

```javascript
// 获取状态
const state = useStore((state) => state.someValue)

// 更新状态
const updateState = useStore((state) => state.setSomeValue)
updateState(newValue)
```

### 性能优化

- 使用 Vite 进行快速冷启动
- 组件按需加载（React.lazy + Suspense）
- 静态资源优化
- CSS-in-JS减少样式冲突

### 许可证

Copyright © 2024 芯片失效分析AI Agent系统
