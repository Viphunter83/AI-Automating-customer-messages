'use client'

import { useEffect, useRef } from 'react'
import { Message, MessageWithClassification } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import { PriorityBadge } from '@/components/PriorityBadge'
import clsx from 'clsx'

interface ChatHistoryProps {
  messages: MessageWithClassification[]
  isLoading?: boolean
  clientId?: string
}

export function ChatHistory({ messages, isLoading, clientId }: ChatHistoryProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    // Auto-scroll to bottom
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])
  
  const getMessageLabel = (type: Message['message_type']) => {
    const labels: Record<Message['message_type'], string> = {
      user: '👤 Client',
      bot_auto: '🤖 Auto',
      bot_escalated: '⚠️ Escalated',
      operator: '👨‍💼 Operator'
    }
    return labels[type] || 'Unknown'
  }
  
  // Sort messages by created_at (oldest first) for chronological display
  const sortedMessages = [...messages].sort((a, b) => 
    new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  )
  
  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
    >
      {messages.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center h-full text-gray-600">
          <p className="text-lg mb-2">Пока нет сообщений.</p>
          <p className="text-sm text-gray-500">Чтобы начать, отправьте тестовое сообщение.</p>
        </div>
      )}
      
      {sortedMessages.map((msg) => (
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
              {clientId && (
                <span className="text-xs text-gray-400 font-mono">
                  {clientId}
                </span>
              )}
            </div>
            <span className="text-xs text-gray-500">
              {new Date(msg.created_at).toLocaleTimeString()}
            </span>
          </div>
          
          {/* Show content, but hide file_id line for media messages */}
          {msg.content.includes('[ФОТО получено') ? (
            <div>
              {/* Extract and display caption if present */}
              {msg.content.includes('Подпись:') && (
                <p className="text-sm text-gray-800 break-words mb-2">
                  {msg.content.split('Подпись:')[1]}
                </p>
              )}
              {/* Extract file_id and show image */}
              {(() => {
                const fileIdMatch = msg.content.match(/file_id:\s*([^\]]+)/);
                if (fileIdMatch) {
                  const fileId = fileIdMatch[1].trim();
                  const proxyUrl = `/api/operator/telegram-file/${fileId}`;
                  return (
                    <div className="mt-2">
                      <img 
                        src={proxyUrl}
                        alt="Скриншот от клиента"
                        className="max-w-full h-auto rounded border border-gray-300 cursor-pointer"
                        style={{ maxHeight: '300px' }}
                        onClick={() => window.open(proxyUrl, '_blank')}
                        onError={(e) => {
                          // Show error message if image fails to load
                          const img = e.target as HTMLImageElement;
                          img.style.display = 'none';
                          const errorDiv = document.createElement('div');
                          errorDiv.className = 'text-xs text-red-600 mt-1';
                          errorDiv.textContent = 'Не удалось загрузить изображение';
                          img.parentElement?.appendChild(errorDiv);
                        }}
                      />
                      <a
                        href={proxyUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline mt-1 block"
                      >
                        📷 Открыть в полном размере
                      </a>
                    </div>
                  );
                }
                return <p className="text-sm text-gray-600">📷 Фото получено</p>;
              })()}
            </div>
          ) : (
            <p className="text-sm text-gray-800 break-words">{msg.content}</p>
          )}
          
          {/* Only show classification for user messages (not bot responses) */}
          {msg.classification && msg.message_type === 'user' && (
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
