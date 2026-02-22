import { create } from 'zustand'

// Initial state
const initialState = {
  // UI state
  sidebarOpen: true,
  currentPage: 'analyze',
  theme: 'dark',

  // Analysis state
  currentAnalysis: null,
  analysisHistory: [],
  analysisStatus: 'idle', // idle, analyzing, completed, error

  // Statistics
  stats: {
    today_analyses: 0,
    success_rate: 0,
    avg_duration: 0,
    expert_interventions: 0,
    total_analyses: 0,
  },

  // Cases
  cases: [],
  casesFilter: {
    chip_model: 'all',
    failure_domain: 'all',
  },

  // History filter
  historyFilter: {
    chip_model: '',
    date_from: null,
    date_to: null,
    limit: 20,
  },

  // User preferences
  preferences: {
    chip_model: 'XC9000',
    infer_threshold: 0.7,
    api_url: 'http://localhost:8889',
  },

  // Notifications
  notifications: [],
}

// Create store
export const useStore = create((set, get) => ({
  ...initialState,

  // UI actions
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setCurrentPage: (page) => set({ currentPage: page }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  // Analysis actions
  setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
  setAnalysisStatus: (status) => set({ analysisStatus: status }),
  addAnalysisToHistory: (analysis) =>
    set((state) => ({
      analysisHistory: [analysis, ...state.analysisHistory],
    })),

  // Statistics actions
  setStats: (stats) => set({ stats }),

  // Cases actions
  setCases: (cases) => set({ cases }),
  setCasesFilter: (filter) =>
    set((state) => ({
      casesFilter: { ...state.casesFilter, ...filter },
    })),

  // History filter actions
  setHistoryFilter: (filter) =>
    set((state) => ({
      historyFilter: { ...state.historyFilter, ...filter },
    })),

  // Preferences actions
  setPreferences: (prefs) =>
    set((state) => ({
      preferences: { ...state.preferences, ...prefs },
    })),

  // Notification actions
  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        { ...notification, id: Date.now(), timestamp: new Date() },
        ...state.notifications,
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearNotifications: () => set({ notifications: [] }),

  // Reset
  reset: () => set(initialState),
}))

// Selectors
export const selectCurrentAnalysis = (state) => state.currentAnalysis
export const selectAnalysisStatus = (state) => state.analysisStatus
export const selectStats = (state) => state.stats
export const selectCases = (state) => state.cases
export const selectCasesFilter = (state) => state.casesFilter
export const selectHistoryFilter = (state) => state.historyFilter
export const selectPreferences = (state) => state.preferences
export const selectNotifications = (state) => state.notifications
