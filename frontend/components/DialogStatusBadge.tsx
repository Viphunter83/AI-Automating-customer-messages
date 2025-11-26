'use client'

import { Badge } from '@/components/ui/badge'
import { DialogStatus } from '@/lib/types'
import clsx from 'clsx'

interface DialogStatusBadgeProps {
  status: DialogStatus
  className?: string
}

export function DialogStatusBadge({ status, className }: DialogStatusBadgeProps) {
  const statusConfig = {
    open: {
      label: 'Открыт',
      className: 'bg-green-100 text-green-800 border-green-300',
      icon: '🟢'
    },
    closed: {
      label: 'Закрыт',
      className: 'bg-gray-100 text-gray-800 border-gray-300',
      icon: '⚫'
    },
    escalated: {
      label: 'Эскалирован',
      className: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      icon: '⚠️'
    }
  }

  const config = statusConfig[status] || statusConfig.open

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

