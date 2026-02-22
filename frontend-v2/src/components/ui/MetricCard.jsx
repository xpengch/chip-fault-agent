import React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export function MetricCard({
  title,
  value,
  unit,
  change,
  changeType,
  icon: Icon,
  className,
  variant = 'default',
  trend,
}) {
  const isPositive = changeType === 'positive'
  const isNegative = changeType === 'negative'
  const isNeutral = changeType === 'neutral'

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'metric-card relative overflow-hidden',
        className
      )}
    >
      {/* Icon */}
      {Icon && (
        <div className="absolute top-4 right-4 w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center">
          <Icon className="w-5 h-5 text-cyan-400" />
        </div>
      )}

      {/* Content */}
      <div>
        <p className="metric-label">{title}</p>
        <div className="flex items-baseline gap-2 mt-2">
          <span className="metric-value">{value}</span>
          {unit && (
            <span className="text-sm text-slate-400">{unit}</span>
          )}
        </div>

        {/* Change indicator */}
        {change !== undefined && (
          <div className={cn(
            'metric-change flex items-center gap-1',
            isPositive && 'metric-change-positive',
            isNegative && 'metric-change-negative',
            isNeutral && 'text-slate-400'
          )}>
            {!isNeutral && <TrendIcon className="w-3 h-3" />}
            <span>{Math.abs(change)}%</span>
          </div>
        )}
      </div>

      {/* Accent line */}
      <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-cyan-500/50 to-purple-500/50" />
    </motion.div>
  )
}

export function MetricGrid({ children, className }) {
  return (
    <div className={cn(
      'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4',
      className
    )}>
      {children}
    </div>
  )
}
