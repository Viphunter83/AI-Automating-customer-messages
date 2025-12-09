'use client'

import { useState, useEffect, useRef } from 'react'
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
  const hasAutoSelectedRef = useRef(false) // Track if we've auto-selected once
  
  // Load available clients (open dialogs) and auto-select first one
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
        
        // Auto-select first client if none selected (only once on initial load)
        if (!hasAutoSelectedRef.current && sortedClients.length > 0) {
          // Check current clientId using functional update
          setClientId((currentClientId) => {
            if (!currentClientId) {
              // Prefer Telegram clients
              const telegramClient = sortedClients.find((id: string) => id.startsWith('telegram_'))
              const selectedClient = telegramClient || sortedClients[0]
              console.log('📋 Auto-selecting first client:', selectedClient)
              hasAutoSelectedRef.current = true
              return selectedClient
            }
            return currentClientId
          })
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
  }, []) // Empty dependencies - only run on mount
  
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
        <div className="h-full flex gap-4">
          {/* Left Sidebar: Dialog List */}
          <div className="w-80 flex-shrink-0 border border-gray-200 rounded-lg bg-white overflow-hidden flex flex-col">
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <h2 className="text-lg font-semibold mb-1">Активные диалоги</h2>
              <p className="text-xs text-gray-600">
                {availableClients.length > 0 
                  ? `${availableClients.length} активных диалогов`
                  : 'Загрузка...'}
              </p>
            </div>
            <div className="flex-1 overflow-hidden p-2">
              {loadingClients ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-gray-500">Загрузка...</div>
                </div>
              ) : (
                <DialogList
                  onSelectDialog={setClientId}
                  selectedClientId={clientId}
                />
              )}
            </div>
          </div>

          {/* Right Side: Chat History */}
          <div className="flex-1 overflow-hidden">
            {clientId ? (
              <ClientDashboard clientId={clientId} operatorId={operatorId} />
            ) : (
              <div className="h-full flex items-center justify-center border border-gray-200 rounded-lg bg-gray-50">
                <div className="text-center text-gray-500">
                  <p className="text-lg mb-2">Выберите диалог для просмотра истории</p>
                  <p className="text-sm">
                    {availableClients.length > 0 
                      ? 'Кликните на диалог в списке слева'
                      : 'Ожидание обращений клиентов...'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
