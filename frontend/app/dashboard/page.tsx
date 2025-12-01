'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ClientDashboard } from '@/components/ClientDashboard'
import { DialogList } from '@/components/DialogList'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { dialogsApi } from '@/lib/api'

export default function Dashboard() {
  const [clientId, setClientId] = useState('')
  const [operatorId] = useState('operator_001')
  const [isConnected, setIsConnected] = useState(true)
  const [availableClients, setAvailableClients] = useState<string[]>([])
  const [loadingClients, setLoadingClients] = useState(false)
  
  // Load available clients (open dialogs)
  useEffect(() => {
    const loadClients = async () => {
      setLoadingClients(true)
      try {
        const response = await dialogsApi.list('open')
        console.log('📋 Dialogs API response:', response)
        // Handle response - data should be an array
        const dialogs = Array.isArray(response.data) ? response.data : []
        console.log('📋 Parsed dialogs:', dialogs)
        const clients = dialogs.map((dialog: any) => dialog.client_id || dialog).filter(Boolean)
        console.log('📋 Extracted clients:', clients)
        // Sort: Telegram clients first, then others
        const sortedClients = clients.sort((a: string, b: string) => {
          const aIsTelegram = a.startsWith('telegram_')
          const bIsTelegram = b.startsWith('telegram_')
          if (aIsTelegram && !bIsTelegram) return -1
          if (!aIsTelegram && bIsTelegram) return 1
          return a.localeCompare(b)
        })
        console.log('📋 Sorted clients:', sortedClients)
        setAvailableClients(sortedClients)
        // Auto-select first Telegram client if none selected or if default client_123 is selected
        if ((!clientId || clientId === 'client_123') && sortedClients.length > 0) {
          // Prefer Telegram clients
          const telegramClient = sortedClients.find((id: string) => id.startsWith('telegram_'))
          const selectedClient = telegramClient || sortedClients[0]
          console.log('📋 Auto-selecting client:', selectedClient)
          setClientId(selectedClient)
        }
      } catch (error) {
        console.error('❌ Failed to load clients:', error)
      } finally {
        setLoadingClients(false)
      }
    }
    
    loadClients()
    // Refresh every 10 seconds
    const interval = setInterval(loadClients, 10000)
    return () => clearInterval(interval)
  }, [clientId])
  
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
            {availableClients.length > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                Активные клиенты ({availableClients.length}):{' '}
                {availableClients.slice(0, 5).map((id, idx) => (
                  <span key={id}>
                    {idx > 0 && ', '}
                    <button
                      onClick={() => setClientId(id)}
                      className="text-blue-600 hover:underline font-mono"
                      title={`Кликните чтобы выбрать ${id}`}
                    >
                      {id}
                    </button>
                  </span>
                ))}
                {availableClients.length > 5 && ` ... (+${availableClients.length - 5})`}
              </p>
            )}
          </div>
          
          <div className="flex gap-2">
            <div className="relative">
              <Input
                placeholder="Client ID (например, client_123 или telegram_123456)"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                className="w-80"
                list="client-suggestions"
              />
              {availableClients.length > 0 && (
                <datalist id="client-suggestions">
                  {availableClients.map((id) => (
                    <option key={id} value={id} />
                  ))}
                </datalist>
              )}
            </div>
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
          <div className="h-full flex flex-col">
            <div className="mb-4">
              <h2 className="text-xl font-semibold mb-2">Активные диалоги</h2>
              <p className="text-sm text-gray-600">
                Выберите диалог для просмотра переписки или введите Client ID в поле выше
              </p>
            </div>
            <div className="flex-1 overflow-hidden">
              <DialogList
                onSelectDialog={setClientId}
                selectedClientId={clientId}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
