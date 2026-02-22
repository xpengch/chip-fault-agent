import React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

export function ProgressBar({
  value = 0,
  max = 100,
  className,
  variant = 'default',
  showLabel,
  label,
  size = 'md',
  animated = true,
}) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  }

  const variantClasses = {
    default: 'progress-bar',
    tech: 'progress-bar-tech',
  }

  return (
    <div className={cn('w-full', className)}>
      {(label || showLabel) && (
        <div className="flex justify-between items-center mb-2">
          {label && (
            <span className="text-xs font-display font-semibold uppercase tracking-wider text-slate-400">
              {label}
            </span>
          )}
          {showLabel && (
            <span className="text-xs font-mono text-cyan-400">
              {percentage.toFixed(1)}%
            </span>
          )}
        </div>
      )}
      <div className={cn(variantClasses[variant], sizeClasses[size])}>
        <motion.div
          className="progress-bar-fill"
          initial={false}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: animated ? 0.5 : 0 }}
        />
      </div>
    </div>
  )
}

export function CircularProgress({
  value = 0,
  max = 100,
  size = 120,
  strokeWidth = 8,
  className,
  children,
  color = '#00d4ff',
}) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (percentage / 100) * circumference

  return (
    <div className={cn('relative inline-flex', className)} style={{ width: size, height: size }}>
      <svg
        className="transform -rotate-90"
        width={size}
        height={size}
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(148, 163, 184, 0.1)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          initial={false}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          style={{
            strokeDasharray: circumference,
          }}
        />
      </svg>
      {/* Center content */}
      <div className="absolute inset-0 flex items-center justify-center">
        {children || (
          <span className="text-2xl font-display font-bold text-white">
            {percentage.toFixed(0)}%
          </span>
        )}
      </div>
    </div>
  )
}
