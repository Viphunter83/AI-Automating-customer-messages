'use client'

import { useState } from 'react'
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
            <h1 className="text-2xl font-bold">Operator Dashboard</h1>
            <p className="text-sm text-gray-600">
              Operator: {operatorId} | Status: {isConnected ? '🟢 Connected' : '🔴 Offline'}
            </p>
          </div>
          
          <div className="flex gap-2">
            <Input
              placeholder="Client ID (e.g., client_123)"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              className="w-64"
            />
            <Button onClick={() => setIsConnected(!isConnected)}>
              {isConnected ? 'Disconnect' : 'Reconnect'}
            </Button>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-hidden p-4">
        {clientId ? (
          <ClientDashboard clientId={clientId} operatorId={operatorId} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Enter a client ID to start
          </div>
        )}
      </div>
    </div>
  )
}
