'use client'

import { useState } from 'react'
import { useChatSession } from '@/hooks/useMessages'
import { ChatHistory } from '@/components/ChatHistory'
import { MessageFeedback } from '@/components/MessageFeedback'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface ClientDashboardProps {
  clientId: string
  operatorId: string
}

export function ClientDashboard({ clientId, operatorId }: ClientDashboardProps) {
  const { messages, isLoading, messageCount } = useChatSession(clientId)
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null)
  
  const selectedMessage = messages.find(m => m.id === selectedMessageId)
  
  return (
    <div className="flex gap-4 h-full">
      {/* Chat History */}
      <div className="flex-1 flex flex-col border border-gray-200 rounded-lg">
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold">{clientId}</h3>
              <p className="text-sm text-gray-600">{messageCount} messages</p>
            </div>
            <Badge variant="outline">Active</Badge>
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
