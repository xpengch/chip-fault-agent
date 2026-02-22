import React from 'react'
import { motion } from 'framer-motion'
import { clsx } from 'clsx'

function cn(...classes) {
  return clsx(classes)
}

export function Card({ children, className, variant = 'default', hover, ...props }) {
  const baseClasses = 'bg-slate-900/50 backdrop-blur border border-slate-800 rounded-xl p-4'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(baseClasses, hover && 'hover:border-slate-700 transition-shadow', className)}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export function CardHeader({ children, className }) {
  return (
    <div className={cn('flex items-start justify-between mb-4', className)}>
      {children}
    </div>
  )
}

export function CardTitle({ children, className, icon: Icon }) {
  return (
    <h3 className={cn('text-lg font-bold text-white flex items-center gap-2', className)}>
      {Icon && <Icon className="w-5 h-5 text-cyan-400" />}
      {children}
    </h3>
  )
}

export function CardContent({ children, className }) {
  return (
    <div className={cn('', className)}>
      {children}
    </div>
  )
}

export function CardFooter({ children, className }) {
  return (
    <div className={cn('mt-4 pt-4 border-t border-slate-800', className)}>
      {children}
    </div>
  )
}
