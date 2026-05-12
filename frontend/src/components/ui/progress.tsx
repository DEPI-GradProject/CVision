import * as React from 'react'
import { cn } from '@/lib/utils'

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number
  variant?: 'default' | 'success' | 'warning' | 'error'
}

const variants = {
  default: 'bg-primary',
  success: 'bg-success',
  warning: 'bg-warning',
  error: 'bg-error',
}

function Progress({ className, value = 0, variant = 'default', ...props }: ProgressProps) {
  return (
    <div
      className={cn('h-2 w-full overflow-hidden rounded-full bg-surface-light', className)}
      {...props}
    >
      <div
        className={cn('h-full rounded-full transition-all duration-500 ease-out', variants[variant])}
        style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
      />
    </div>
  )
}

export { Progress }
