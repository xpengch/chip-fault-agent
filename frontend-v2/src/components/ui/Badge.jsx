import React from 'react'
import { cn } from '@/lib/utils'
import { CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react'

const badgeVariants = {
  success: 'badge-success',
  warning: 'badge-warning',
  error: 'badge-error',
  info: 'badge-info',
  tech: 'badge-tech',
  neutral: 'bg-slate-800 text-slate-300 border-slate-700',
}

const badgeIcons = {
  success: CheckCircle,
  warning: AlertTriangle,
  error: XCircle,
  info: Info,
}

export function Badge({
  children,
  variant = 'neutral',
  className,
  icon,
  size = 'md',
  ...props
}) {
  const Icon = icon || badgeIcons[variant]

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3 py-1.5',
  }

  return (
    <span
      className={cn(
        'badge inline-flex items-center gap-1.5 font-display font-semibold uppercase tracking-wider rounded',
        badgeVariants[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {Icon && <Icon className="w-3 h-3" />}
      {children}
    </span>
  )
}

export function StatusBadge({ status, className }) {
  const statusConfig = {
    completed: { variant: 'success', label: 'Completed', icon: CheckCircle },
    pending: { variant: 'warning', label: 'Pending', icon: AlertTriangle },
    failed: { variant: 'error', label: 'Failed', icon: XCircle },
    analyzing: { variant: 'info', label: 'Analyzing', icon: Info },
    idle: { variant: 'neutral', label: 'Idle' },
  }

  const config = statusConfig[status] || statusConfig.idle

  return (
    <Badge variant={config.variant} icon={config.icon} className={className}>
      {config.label}
    </Badge>
  )
}
