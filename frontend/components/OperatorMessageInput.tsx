'use client'

import { useState } from 'react'
import { operatorAPI } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface OperatorMessageInputProps {
  clientId: string
  operatorId: string
}

export function OperatorMessageInput({ clientId, operatorId }: OperatorMessageInputProps) {
  const [message, setMessage] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSend = async () => {
    if (!message.trim()) {
      setError('Сообщение не может быть пустым')
      return
    }

    setIsSending(true)
    setError(null)
    setSuccess(false)

    try {
      await operatorAPI.sendMessage(clientId, message.trim())
      setMessage('')
      setSuccess(true)
      // Clear success message after 2 seconds
      setTimeout(() => setSuccess(false), 2000)
      // Refresh messages by reloading page or triggering refetch
      window.location.reload()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при отправке сообщения')
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Введите ответ клиенту..."
          className="flex-1"
          disabled={isSending}
        />
        <Button
          onClick={handleSend}
          disabled={isSending || !message.trim()}
        >
          {isSending ? 'Отправка...' : 'Отправить'}
        </Button>
      </div>
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
      {success && (
        <p className="text-sm text-green-600">Сообщение отправлено успешно!</p>
      )}
    </div>
  )
}










