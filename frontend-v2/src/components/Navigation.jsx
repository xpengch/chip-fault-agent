import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Microscope, History, Database, Settings, Home } from 'lucide-react'

const navItems = [
  { path: '/analyze', icon: Microscope, label: 'Analyze' },
  { path: '/history', icon: History, label: 'History' },
  { path: '/cases', icon: Database, label: 'Cases' },
  { path: '/system', icon: Settings, label: 'System' },
]

export default function Navigation() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      height: '60px',
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid #334155',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px'
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }} onClick={() => navigate('/analyze')}>
        <div style={{
          width: '36px',
          height: '36px',
          background: 'linear-gradient(135deg, #00d4ff, #0066cc)',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(0, 212, 255, 0.3)'
        }}>
          <Microscope size={20} style={{ color: '#ffffff' }} />
        </div>
        <div>
          <h1 style={{
            fontSize: '14px',
            fontWeight: 'bold',
            color: '#ffffff',
            fontFamily: 'JetBrains Mono, monospace',
            lineHeight: '1.2'
          }}>
            CHIP FAULT AI
          </h1>
          <p style={{ fontSize: '11px', color: '#64748b', fontFamily: 'JetBrains Mono, monospace' }}>
            Enterprise Edition
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path

          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                backgroundColor: isActive ? 'rgba(0, 212, 255, 0.2)' : 'transparent',
                border: isActive ? '1px solid #00d4ff' : '1px solid transparent',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '13px',
                fontWeight: '600',
                color: isActive ? '#00d4ff' : '#94a3b8',
                fontFamily: 'JetBrains Mono, monospace'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.target.style.backgroundColor = 'rgba(30, 41, 59, 0.5)'
                  e.target.style.borderColor = '#334155'
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.target.style.backgroundColor = 'transparent'
                  e.target.style.borderColor = 'transparent'
                }
              }}
            >
              <Icon size={16} />
              {item.label}
            </button>
          )
        })}
      </nav>

      {/* API Status */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 16px',
        backgroundColor: 'rgba(0, 0, 0, 0.2)',
        borderRadius: '6px',
        fontSize: '12px',
        color: '#10b981',
        fontFamily: 'JetBrains Mono, monospace'
      }}>
        <span style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: '#10b981',
          animation: 'pulse 2s ease-in-out infinite'
        }} />
        API ONLINE
      </div>
    </div>
  )
}
