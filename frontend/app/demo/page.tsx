'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { mockMessages, mockClassifications, mockClientIds } from '@/lib/mockData'
import { api } from '@/lib/api'
import { useQueryClient } from '@tanstack/react-query'

export default function DemoPage() {
  const [loading, setLoading] = useState<string | null>(null)
  const [results, setResults] = useState<Record<string, any>>({})
  const queryClient = useQueryClient()

  const sendMockMessage = async (message: typeof mockMessages[0]) => {
    setLoading(message.id)
    try {
      const response = await api.post('/api/messages/', {
        client_id: message.client_id,
        content: message.content,
      })
      setResults(prev => ({ ...prev, [message.id]: { success: true, data: response.data } }))
      
      // Invalidate queries to refresh UI
      queryClient.invalidateQueries({ queryKey: ['messages', message.client_id] })
      queryClient.invalidateQueries({ queryKey: ['classifications', message.client_id] })
      
      setTimeout(() => {
        setLoading(null)
      }, 2000)
    } catch (error: any) {
      setResults(prev => ({ 
        ...prev, 
        [message.id]: { 
          success: false, 
          error: error.response?.data?.detail || error.message 
        } 
      }))
      setLoading(null)
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Демонстрация системы</h1>
        <p className="text-gray-600">
          Отправьте тестовые сообщения для демонстрации функционала системы поддержки
        </p>
      </div>

      <div className="grid gap-6">
        {mockMessages
          .filter((msg, idx, arr) => arr.findIndex(m => m.client_id === msg.client_id) === idx)
          .map(clientMsg => {
            const clientMessages = mockMessages.filter(m => m.client_id === clientMsg.client_id)
            return (
              <Card key={clientMsg.client_id} className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold mb-1">Клиент: {clientMsg.client_id}</h2>
                    <p className="text-sm text-gray-600">
                      {clientMessages.length} сообщений для отправки
                    </p>
                  </div>
                  <Button
                    onClick={() => {
                      // Send all messages for this client sequentially
                      clientMessages.forEach((msg, idx) => {
                        setTimeout(() => sendMockMessage(msg), idx * 2000)
                      })
                    }}
                    disabled={loading !== null}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    Отправить все сообщения
                  </Button>
                </div>

                <div className="space-y-3">
                  {clientMessages.map(msg => {
                    const classification = mockClassifications.find(c => c.message_id === msg.id)
                    const result = results[msg.id]
                    return (
                      <div
                        key={msg.id}
                        className="p-4 border border-gray-200 rounded-lg bg-gray-50"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <p className="font-medium text-gray-900 mb-1">{msg.content}</p>
                            {classification && (
                              <div className="flex items-center gap-2 text-sm text-gray-600">
                                <span className="font-medium">{classification.detected_scenario}</span>
                                <span>•</span>
                                <span>{(classification.confidence * 100).toFixed(0)}% уверенности</span>
                              </div>
                            )}
                          </div>
                          <Button
                            size="sm"
                            onClick={() => sendMockMessage(msg)}
                            disabled={loading === msg.id || loading !== null}
                            variant="outline"
                          >
                            {loading === msg.id ? 'Отправка...' : 'Отправить'}
                          </Button>
                        </div>
                        {result && (
                          <div className={`mt-2 p-2 rounded text-sm ${
                            result.success 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {result.success ? (
                              <div>
                                ✅ Сообщение отправлено успешно
                                {result.data?.classification && (
                                  <div className="mt-1">
                                    Сценарий: {result.data.classification.scenario} 
                                    ({(result.data.classification.confidence * 100).toFixed(0)}%)
                                  </div>
                                )}
                              </div>
                            ) : (
                              <div>❌ Ошибка: {result.error}</div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </Card>
            )
          })}
      </div>

      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold mb-2">💡 Совет</h3>
        <p className="text-sm text-gray-700">
          После отправки сообщений перейдите в{' '}
          <a href="/dashboard" className="text-blue-600 underline">
            Панель оператора
          </a>{' '}
          и выберите соответствующий Client ID для просмотра истории сообщений и классификаций.
        </p>
      </div>
    </div>
  )
}

