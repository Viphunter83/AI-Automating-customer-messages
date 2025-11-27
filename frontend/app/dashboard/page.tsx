'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ClientDashboard } from '@/components/ClientDashboard'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export default function Dashboard() {
  const [clientId, setClientId] = useState('client_123')
  const [operatorId] = useState('operator_001')
  const [isConnected, setIsConnected] = useState(true)
  
  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">Панель управления оператора</h1>
            <p className="text-sm text-gray-700">
              Оператор: {operatorId} | Статус: {isConnected ? '🟢 Подключен' : '🔴 Отключен'}
            </p>
          </div>
          
          <div className="flex gap-2">
            <Input
              placeholder="Client ID (например, client_123)"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              className="w-64"
            />
            <Button onClick={() => setIsConnected(!isConnected)} variant="outline">
              {isConnected ? 'Отключиться' : 'Подключиться'}
            </Button>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-hidden p-4">
        {clientId ? (
          <ClientDashboard clientId={clientId} operatorId={operatorId} />
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-600">
            <p className="text-lg mb-2">Введите Client ID для начала работы</p>
            <p className="text-sm text-gray-500">
              Или перейдите в раздел <Link href="/demo" className="text-blue-600 hover:underline">"Демо"</Link> для отправки тестовых сообщений
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
