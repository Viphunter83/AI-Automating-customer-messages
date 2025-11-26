'use client'

import { useState } from 'react'
import { useChatSession, useDialog, useCloseDialog, useReopenDialog } from '@/hooks/useMessages'
import { ChatHistory } from '@/components/ChatHistory'
import { MessageFeedback } from '@/components/MessageFeedback'
import { DialogStatusBadge } from '@/components/DialogStatusBadge'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatDistanceToNow } from 'date-fns'
import { ru } from 'date-fns/locale'

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
  
  const selectedMessage = messages.find(m => m.id === selectedMessageId)
  
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
          messages={messages}
          isLoading={isLoading}
          clientId={clientId}
        />
      </div>
      
      {/* Feedback Panel */}
      <div className="w-96 flex flex-col gap-4">
        {selectedMessage && selectedMessage.classification ? (
          <>
            <div className="p-4 bg-white border border-gray-200 rounded-lg">
              <h4 className="font-semibold mb-2">Message Details</h4>
              <div className="space-y-2 text-sm">
                <p><strong>Type:</strong> {selectedMessage.message_type}</p>
                <p><strong>Scenario:</strong> {selectedMessage.classification.detected_scenario}</p>
                <p><strong>Confidence:</strong> {(selectedMessage.classification.confidence * 100).toFixed(0)}%</p>
                <p className="text-gray-600"><strong>Reasoning:</strong> {selectedMessage.classification.reasoning}</p>
              </div>
            </div>
            
            <MessageFeedback
              messageId={selectedMessage.id}
              classification={selectedMessage.classification}
              operatorId={operatorId}
            />
          </>
        ) : (
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center text-gray-500">
            <p>Select a message to review and provide feedback</p>
          </div>
        )}
        
        {/* Message List for Selection */}
        <div className="flex-1 overflow-y-auto border border-gray-200 rounded-lg p-3 space-y-2 bg-white">
          <p className="text-xs font-semibold text-gray-600 px-1">Messages with Classifications</p>
          {messages
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
                <div className="flex items-center justify-between">
                  <span className="font-medium truncate">{msg.content.substring(0, 30)}...</span>
                  <Badge variant="outline" className="text-xs">
                    {msg.classification?.detected_scenario}
                  </Badge>
                </div>
              </button>
            ))}
        </div>
      </div>
    </div>
  )
}
