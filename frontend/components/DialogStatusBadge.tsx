'use client'

import { Badge } from '@/components/ui/badge'
import { DialogStatus } from '@/lib/types'
import clsx from 'clsx'

interface DialogStatusBadgeProps {
  status: DialogStatus | string
  className?: string
}

export function DialogStatusBadge({ status, className }: DialogStatusBadgeProps) {
  // Normalize status to DialogStatus type
  const normalizedStatus = (typeof status === 'string' ? status.toLowerCase() : status) as DialogStatus
  
  const statusConfig: Record<DialogStatus, { label: string; className: string; icon: string }> = {
    open: {
      label: 'Открыт',
      className: 'bg-green-100 text-green-900 border-green-300 dark:bg-green-900 dark:text-green-100',
      icon: '🟢'
    },
    closed: {
      label: 'Закрыт',
      className: 'bg-gray-200 text-gray-900 border-gray-400 dark:bg-gray-700 dark:text-gray-100',
      icon: '⚫'
    },
    escalated: {
      label: 'Эскалирован',
      className: 'bg-yellow-100 text-yellow-900 border-yellow-300 dark:bg-yellow-900 dark:text-yellow-100',
      icon: '⚠️'
    }
  }

  const config = statusConfig[normalizedStatus] || statusConfig.open

  return (
    <Badge 
      className={clsx(
        'inline-flex items-center gap-1 px-2 py-1 text-xs font-medium border',
        config.className,
        className
      )}
    >
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </Badge>
  )
}

