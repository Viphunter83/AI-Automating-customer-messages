'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { mockMessages, mockClassifications } from '@/lib/mockData'
import { api } from '@/lib/api'
import { useQueryClient } from '@tanstack/react-query'
import type { Message, Classification } from '@/lib/types'

export default function DemoPage() {
  const [loading, setLoading] = useState<string | null>(null)
  const [results, setResults] = useState<Record<string, { success: boolean; data?: any; error?: string }>>({})
  const queryClient = useQueryClient()
  // Track the currently loading message ID to prevent race conditions
  const currentLoadingRef = useRef<string | null>(null)
  // Track active timers to clean them up
  const timerRefs = useRef<Map<string, NodeJS.Timeout>>(new Map())

  // Cleanup timers on unmount
  useEffect(() => {
    const timers = timerRefs.current
    return () => {
      timers.forEach(timer => clearTimeout(timer))
      timers.clear()
    }
  }, [])

  const sendMockMessage = async (message: typeof mockMessages[0]) => {
    // Clear any existing timer for this message
    const existingTimer = timerRefs.current.get(message.id)
    if (existingTimer) {
      clearTimeout(existingTimer)
      timerRefs.current.delete(message.id)
    }

    // Set loading state and track it
    currentLoadingRef.current = message.id
    setLoading(message.id)
    
    let timer: NodeJS.Timeout | null = null
    
    try {
      const response = await api.post('/api/messages/', {
        client_id: message.client_id,
        content: message.content,
      })
      setResults(prev => ({ ...prev, [message.id]: { success: true, data: response.data } }))
      
      // Invalidate queries to refresh UI
      queryClient.invalidateQueries({ queryKey: ['messages', message.client_id] })
      queryClient.invalidateQueries({ queryKey: ['classifications', message.client_id] })
      
      // Only clear loading state if this is still the current loading message
      // Store timer immediately after creation to prevent memory leaks
      timer = setTimeout(() => {
        // Check if this message is still the one being loaded
        if (currentLoadingRef.current === message.id) {
          setLoading(null)
          currentLoadingRef.current = null
        }
        timerRefs.current.delete(message.id)
      }, 2000)
      
      // Store timer reference immediately to ensure it can be cleaned up
      timerRefs.current.set(message.id, timer)
    } catch (error: unknown) {
      // Check for API response data first (most specific error message)
      const apiError = error as { response?: { data?: { detail?: string } } }
      const errorMessage = apiError?.response?.data?.detail 
        || (error instanceof Error ? error.message : 'Unknown error')
      setResults(prev => ({ 
        ...prev, 
        [message.id]: { 
          success: false, 
          error: errorMessage
        } 
      }))
      
      // Only clear loading state if this is still the current loading message
      if (currentLoadingRef.current === message.id) {
        setLoading(null)
        currentLoadingRef.current = null
      }
      
      // Clear timer if exists (check both local timer and ref to handle all cases)
      if (timer) {
        clearTimeout(timer)
        timerRefs.current.delete(message.id)
      } else {
        // Fallback: check ref in case timer was created but variable wasn't set
        const existingTimer = timerRefs.current.get(message.id)
        if (existingTimer) {
          clearTimeout(existingTimer)
          timerRefs.current.delete(message.id)
        }
      }
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
          .filter((msg: Message, idx: number, arr: Message[]) => arr.findIndex((m: Message) => m.client_id === msg.client_id) === idx)
          .map((clientMsg: Message) => {
            const clientMessages = mockMessages.filter((m: Message) => m.client_id === clientMsg.client_id)
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
                    onClick={async () => {
                      // Send all messages for this client sequentially
                      for (const msg of clientMessages) {
                        await sendMockMessage(msg)
                        // Wait 2 seconds between messages to avoid rate limiting
                        await new Promise(resolve => setTimeout(resolve, 2000))
                      }
                    }}
                    disabled={loading !== null}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    Отправить все сообщения
                  </Button>
                </div>

                <div className="space-y-3">
                  {clientMessages.map((msg: Message) => {
                    const classification = mockClassifications.find((c: Classification) => c.message_id === msg.id)
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
                                {result.data?.response && (
                                  <div className="mt-2 p-2 bg-white rounded border border-green-300">
                                    <div className="text-xs font-semibold mb-1">🤖 Ответ системы:</div>
                                    <div className="text-sm whitespace-pre-wrap">{result.data.response.text}</div>
                                    <div className="text-xs text-gray-600 mt-1">
                                      Тип: {result.data.response.type}
                                    </div>
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

