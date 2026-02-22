import React, { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useStore } from '../../store/useStore'
import { CircuitBackground, HUDOverlay } from '../ui/CircuitBackground'
import {
  Microscope,
  History,
  Database,
  Settings,
  Menu,
  X,
  Activity,
  Bell,
} from 'lucide-react'

const navigation = [
  { name: 'Analyze', path: '/analyze', icon: Microscope },
  { name: 'History', path: '/history', icon: History },
  { name: 'Cases', path: '/cases', icon: Database },
  { name: 'System', path: '/system', icon: Settings },
]

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const sidebarOpen = useStore((state) => state.sidebarOpen)
  const setSidebarOpen = useStore((state) => state.setSidebarOpen)
  const notifications = useStore((state) => state.notifications)

  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    const checkApi = async () => {
      try {
        await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8889'}/api/v1/health`)
        setApiStatus('online')
      } catch {
        setApiStatus('offline')
      }
    }

    checkApi()
    const interval = setInterval(checkApi, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Background */}
      <CircuitBackground />
      <HUDOverlay />

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 transition-transform duration-300 ease-in-out flex flex-col glass border-r border-slate-800/50 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-slate-800/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center">
              <Microscope className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white font-display">CHIP FAULT AI</h1>
              <p className="text-xs text-slate-500">Enterprise Edition</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path

            return (
              <button
                key={item.name}
                onClick={() => {
                  navigate(item.path)
                  if (window.innerWidth < 1024) {
                    setSidebarOpen(false)
                  }
                }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg font-display text-xs font-semibold uppercase tracking-wider transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-400 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.name}</span>
              </button>
            )
          })}
        </nav>

        {/* API Status */}
        <div className="p-4 border-t border-slate-800/50">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500 font-display uppercase tracking-wider">API Status</span>
            <span className={`flex items-center gap-1.5 font-display font-semibold ${apiStatus === 'online' ? 'text-emerald-400' : 'text-red-400'}`}>
              <span className={`w-2 h-2 rounded-full animate-pulse ${apiStatus === 'online' ? 'bg-emerald-400' : 'bg-red-400'}`} />
              {apiStatus === 'online' ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </aside>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden relative z-10">
        {/* Header */}
        <header className="h-16 glass border-b border-slate-800/50 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden text-slate-400 hover:text-white"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div>
              <h2 className="text-lg font-bold text-white">
                {navigation.find((n) => n.path === location.pathname)?.name || 'Dashboard'}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/50 border border-slate-800">
              <Activity className="w-4 h-4 text-cyan-400 animate-pulse" />
              <span className="text-xs font-display text-slate-400">System Active</span>
            </div>

            <button className="relative text-slate-400 hover:text-white">
              <Bell className="w-5 h-5" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
                  {notifications.length}
                </span>
              )}
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
