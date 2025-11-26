'use client'

import { useEffect, useRef } from 'react'
import { Message, MessageWithClassification } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import { PriorityBadge } from '@/components/PriorityBadge'
import clsx from 'clsx'

interface ChatHistoryProps {
  messages: MessageWithClassification[]
  isLoading?: boolean
  clientId: string
}

export function ChatHistory({ messages, isLoading, clientId }: ChatHistoryProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    // Auto-scroll to bottom
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])
  
  const getMessageColor = (type: Message['message_type']) => {
    switch (type) {
      case 'user':
        return 'bg-blue-100 text-blue-900'
      case 'bot_auto':
        return 'bg-green-100 text-green-900'
      case 'bot_escalated':
        return 'bg-yellow-100 text-yellow-900'
      case 'operator':
        return 'bg-purple-100 text-purple-900'
      default:
        return 'bg-gray-100 text-gray-900'
    }
  }
  
  const getMessageLabel = (type: Message['message_type']) => {
    const labels = {
      user: '👤 Client',
      bot_auto: '🤖 Auto',
      bot_escalated: '⚠️ Escalated',
      operator: '👨‍💼 Operator'
    }
    return labels[type] || 'Unknown'
  }
  
  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
    >
      {messages.length === 0 && !isLoading && (
        <div className="flex items-center justify-center h-full text-gray-500">
          <p>No messages yet. Send a test message to start.</p>
        </div>
      )}
      
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={clsx(
            'p-3 rounded-lg max-w-md',
            msg.message_type === 'user'
              ? 'ml-auto bg-blue-50 border border-blue-200'
              : 'mr-auto bg-white border border-gray-200'
          )}
        >
          <div className="flex items-center justify-between gap-2 mb-1">
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">
                {getMessageLabel(msg.message_type)}
              </Badge>
              {msg.priority && <PriorityBadge priority={msg.priority} size="sm" />}
            </div>
            <span className="text-xs text-gray-500">
              {new Date(msg.created_at).toLocaleTimeString()}
            </span>
          </div>
          
          <p className="text-sm text-gray-800 break-words">{msg.content}</p>
          
          {msg.classification && (
            <div className="mt-2 pt-2 border-t border-gray-200 text-xs">
              <div className="flex items-center gap-2">
                <span className="font-semibold">Classification:</span>
                <Badge variant="outline">{msg.classification.detected_scenario}</Badge>
                <span className="text-gray-500">
                  {(msg.classification.confidence * 100).toFixed(0)}%
                </span>
              </div>
              {msg.classification.reasoning && (
                <p className="text-gray-600 mt-1 italic">
                  {msg.classification.reasoning}
                </p>
              )}
            </div>
          )}
        </div>
      ))}
      
      {isLoading && (
        <div className="flex justify-center items-center py-4">
          <div className="animate-spin">⏳</div>
          <span className="ml-2 text-sm text-gray-500">Loading...</span>
        </div>
      )}
    </div>
  )
}
