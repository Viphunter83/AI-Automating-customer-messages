'use client'

import { Badge } from '@/components/ui/badge'
import { PriorityLevel } from '@/lib/types'
import clsx from 'clsx'

interface PriorityBadgeProps {
  priority: PriorityLevel
  size?: 'sm' | 'md' | 'lg'
}

export function PriorityBadge({ priority, size = 'md' }: PriorityBadgeProps) {
  const getPriorityConfig = (priority: PriorityLevel) => {
    switch (priority) {
      case 'critical':
        return {
          label: 'Critical',
          className: 'bg-red-100 text-red-800 border-red-300',
          icon: '🔴'
        }
      case 'high':
        return {
          label: 'High',
          className: 'bg-orange-100 text-orange-800 border-orange-300',
          icon: '🟠'
        }
      case 'medium':
        return {
          label: 'Medium',
          className: 'bg-yellow-100 text-yellow-800 border-yellow-300',
          icon: '🟡'
        }
      case 'low':
        return {
          label: 'Low',
          className: 'bg-green-100 text-green-800 border-green-300',
          icon: '🟢'
        }
      default:
        return {
          label: 'Unknown',
          className: 'bg-gray-100 text-gray-800 border-gray-300',
          icon: '⚪'
        }
    }
  }

  const config = getPriorityConfig(priority)
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-xs px-2 py-1',
    lg: 'text-sm px-2.5 py-1.5'
  }

  return (
    <Badge
      variant="outline"
      className={clsx(
        config.className,
        sizeClasses[size],
        'font-semibold border'
      )}
    >
      <span className="mr-1">{config.icon}</span>
      {config.label}
    </Badge>
  )
}










