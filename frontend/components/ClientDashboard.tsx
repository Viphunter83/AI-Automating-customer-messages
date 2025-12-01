'use client'

import { useState } from 'react'
import { useChatSession, useDialog, useCloseDialog, useReopenDialog } from '@/hooks/useMessages'
import { ChatHistory } from '@/components/ChatHistory'
import { MessageFeedback } from '@/components/MessageFeedback'
import { DialogStatusBadge } from '@/components/DialogStatusBadge'
import { PriorityBadge } from '@/components/PriorityBadge'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatDistanceToNow } from 'date-fns'
import { ru } from 'date-fns/locale'
import { useMemo } from 'react'

interface ClientDashboardProps {
  clientId: string
  operatorId: string
}

export function ClientDashboard({ clientId, operatorId }: ClientDashboardProps) {
  const { messages, isLoading, messageCount } = useChatSession(clientId)
  const { data: dialog } = useDialog(clientId)
  const closeDialog = useCloseDialog()
  const reopenDialog = useReopenDialog()
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null)
  const [sortByPriority, setSortByPriority] = useState(true)
  
  // Sort messages by priority (critical > high > medium > low)
  const sortedMessages = useMemo(() => {
    const priorityOrder: Record<string, number> = {
      critical: 4,
      high: 3,
      medium: 2,
      low: 1
    }
    
    if (!sortByPriority) {
      return [...messages].sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
    }
    
    return [...messages].sort((a, b) => {
      const priorityDiff = (priorityOrder[b.priority] || 0) - (priorityOrder[a.priority] || 0)
      if (priorityDiff !== 0) return priorityDiff
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
  }, [messages, sortByPriority])
  
  const selectedMessage = sortedMessages.find(m => m.id === selectedMessageId)
  
  const handleCloseDialog = () => {
    if (dialog?.status === 'open') {
      closeDialog.mutate(clientId)
    }
  }

  const handleReopenDialog = () => {
    if (dialog?.status === 'closed') {
      reopenDialog.mutate(clientId)
    }
  }
  
  return (
    <div className="flex gap-4 h-full">
      {/* Chat History */}
      <div className="flex-1 flex flex-col border border-gray-200 rounded-lg">
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="font-semibold">{clientId}</h3>
                {dialog && <DialogStatusBadge status={dialog.status} />}
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>{messageCount} messages</span>
                {dialog && (
                  <>
                    <span>• Активность: {formatDistanceToNow(new Date(dialog.last_activity_at), { 
                      addSuffix: true, 
                      locale: ru 
                    })}</span>
                    {dialog.farewell_sent_at && (
                      <span className="text-gray-500">
                        • Прощание: {formatDistanceToNow(new Date(dialog.farewell_sent_at), { 
                          addSuffix: true, 
                          locale: ru 
                        })}
                      </span>
                    )}
                  </>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  try {
                    const { searchAPI } = await import('@/lib/api')
                    const response = await searchAPI.exportDialog(clientId, 'csv')
                    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
                    const link = document.createElement('a')
                    link.href = URL.createObjectURL(blob)
                    link.download = `dialog_${clientId}_${new Date().toISOString().split('T')[0]}.csv`
                    link.click()
                  } catch (error) {
                    console.error('Export error:', error)
                    alert('Ошибка при экспорте диалога')
                  }
                }}
              >
                📥 CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  try {
                    const { searchAPI } = await import('@/lib/api')
                    const response = await searchAPI.exportDialog(clientId, 'json')
                    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
                    const link = document.createElement('a')
                    link.href = URL.createObjectURL(blob)
                    link.download = `dialog_${clientId}_${new Date().toISOString().split('T')[0]}.json`
                    link.click()
                  } catch (error) {
                    console.error('Export error:', error)
                    alert('Ошибка при экспорте диалога')
                  }
                }}
              >
                📥 JSON
              </Button>
              {dialog?.status === 'open' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCloseDialog}
                  disabled={closeDialog.isPending}
                >
                  Закрыть диалог
                </Button>
              )}
              {dialog?.status === 'closed' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleReopenDialog}
                  disabled={reopenDialog.isPending}
                >
                  Переоткрыть
                </Button>
              )}
            </div>
          </div>
        </div>
        
        <ChatHistory
          messages={sortedMessages}
          isLoading={isLoading}
          clientId={clientId}
        />
      </div>
      
      {/* Feedback Panel */}
      <div className="w-96 flex flex-col gap-4">
        {selectedMessage && selectedMessage.classification ? (
          <>
                 <div className="p-4 bg-white border border-gray-200 rounded-lg">
                   <h4 className="font-semibold mb-2 text-gray-900">Детали сообщения</h4>
                   <div className="space-y-2 text-sm">
                     <div className="flex items-center gap-2">
                       <strong className="text-gray-900">Приоритет:</strong>
                       <PriorityBadge priority={selectedMessage.priority} size="sm" />
                     </div>
                     {selectedMessage.escalation_reason && (
                       <p className="text-gray-900"><strong>Причина эскалации:</strong> {selectedMessage.escalation_reason}</p>
                     )}
                     <p className="text-gray-900"><strong>Тип:</strong> {selectedMessage.message_type}</p>
                     <p className="text-gray-900"><strong>Сценарий:</strong> {selectedMessage.classification.detected_scenario}</p>
                     <p className="text-gray-900"><strong>Уверенность:</strong> {(selectedMessage.classification.confidence * 100).toFixed(0)}%</p>
                     {selectedMessage.classification.reasoning && (
                       <p className="text-gray-700"><strong>Обоснование:</strong> {selectedMessage.classification.reasoning}</p>
                     )}
                     {selectedMessage.is_first_message && (
                       <Badge variant="outline" className="text-xs">Первое сообщение</Badge>
                     )}
                   </div>
                 </div>
            
            <MessageFeedback
              messageId={selectedMessage.id}
              classification={selectedMessage.classification}
              operatorId={operatorId}
            />
          </>
        ) : (
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center text-gray-700">
            <p>Выберите сообщение для просмотра и оставления обратной связи</p>
          </div>
        )}
        
        {/* Message List for Selection */}
        <div className="flex-1 overflow-y-auto border border-gray-200 rounded-lg p-3 space-y-2 bg-white">
          <div className="flex items-center justify-between mb-2 px-1">
            <p className="text-xs font-semibold text-gray-700">Сообщения с классификациями</p>
            <button
              onClick={() => setSortByPriority(!sortByPriority)}
              className="text-xs text-blue-600 hover:text-blue-800 underline"
            >
              {sortByPriority ? 'Sort by Time' : 'Sort by Priority'}
            </button>
          </div>
          {sortedMessages
            .filter(m => m.classification)
            .map(msg => (
              <button
                key={msg.id}
                onClick={() => setSelectedMessageId(msg.id)}
                className={`w-full text-left p-2 rounded text-sm cursor-pointer transition-colors ${
                  selectedMessageId === msg.id
                    ? 'bg-blue-100 border border-blue-300'
                    : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium truncate flex-1">{msg.content.substring(0, 30)}...</span>
                  <div className="flex items-center gap-1">
                    <PriorityBadge priority={msg.priority} size="sm" />
                    <Badge variant="outline" className="text-xs">
                      {msg.classification?.detected_scenario}
                    </Badge>
                  </div>
                </div>
              </button>
            ))}
        </div>
      </div>
    </div>
  )
}
