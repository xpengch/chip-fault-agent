import React from 'react'

export function CircuitBackground({ className }) {
  return (
    <div className={`fixed inset-0 pointer-events-none ${className || ''}`} style={{ zIndex: 0 }}>
      {/* Simple grid background */}
      <div className="absolute inset-0 opacity-10" style={{
        backgroundImage: 'linear-gradient(#00d4ff 1px, transparent 1px), linear-gradient(90deg, #00d4ff 1px, transparent 1px)',
        backgroundSize: '50px 50px'
      }} />
    </div>
  )
}

export function HUDOverlay() {
  return (
    <div className="fixed inset-0 pointer-events-none" style={{ zIndex: 1 }}>
      {/* Corner brackets */}
      <div className="absolute top-5 left-5 w-10 h-10 border-t-2 border-l-2 border-cyan-400/30" />
      <div className="absolute top-5 right-5 w-10 h-10 border-t-2 border-r-2 border-cyan-400/30" />
      <div className="absolute bottom-5 left-5 w-10 h-10 border-b-2 border-l-2 border-cyan-400/30" />
      <div className="absolute bottom-5 right-5 w-10 h-10 border-b-2 border-r-2 border-cyan-400/30" />
    </div>
  )
}
