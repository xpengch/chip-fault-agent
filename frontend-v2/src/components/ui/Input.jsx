import React, { forwardRef } from 'react'
import { clsx } from 'clsx'

function cn(...classes) {
  return clsx(classes)
}

const inputBaseClasses = 'w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20'

export const Input = forwardRef(
  ({ className, error, label, ...props }, ref) => {
    return (
      <div className="relative">
        {label && (
          <label className="block text-xs font-display font-semibold uppercase tracking-wider text-slate-400 mb-2">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={cn(
            inputBaseClasses,
            error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1 text-xs text-red-400 font-display">{error}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export const Textarea = forwardRef(
  ({ className, error, label, ...props }, ref) => {
    return (
      <div className="relative">
        {label && (
          <label className="block text-xs font-display font-semibold uppercase tracking-wider text-slate-400 mb-2">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          className={cn(
            inputBaseClasses,
            'min-h-[120px] resize-y',
            error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1 text-xs text-red-400 font-display">{error}</p>
        )}
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'
