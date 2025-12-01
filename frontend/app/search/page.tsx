'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AxiosResponse } from 'axios'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedClient, setSelectedClient] = useState('')
  const [scenario, setScenario] = useState('')
  const [minConfidence, setMinConfidence] = useState(0)
  const [offset, setOffset] = useState(0)

  // Search messages
  const { data: searchResults, isLoading } = useQuery({
    queryKey: ['search', 'messages', searchQuery, selectedClient, scenario, minConfidence, offset],
    queryFn: () =>
      api.get('/api/search/messages', {
        params: {
          q: searchQuery,
          client_id: selectedClient || undefined,
          scenario: scenario || undefined,
          min_confidence: minConfidence,
          offset,
        }
      }).then((r: AxiosResponse) => r.data),
    enabled: searchQuery.length > 2 || selectedClient.length > 0,
  })

  // Autocomplete clients
  const { data: autocompleteData } = useQuery({
    queryKey: ['search', 'clients', 'autocomplete', selectedClient],
    queryFn: () =>
      api.get('/api/search/clients/autocomplete', {
        params: { prefix: selectedClient }
      }).then((r: AxiosResponse) => r.data),
    enabled: selectedClient.length > 0,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setOffset(0)
  }

  const handleExport = async (format: 'csv' | 'json') => {
    if (!selectedClient) return
    const url = `/api/search/export/dialog/${selectedClient}.${format}`
    window.open(url, '_blank')
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Search Dialogs</h1>
          <p className="text-gray-600">Find and analyze customer conversations</p>
        </div>

        {/* Search Form */}
        <Card className="p-6 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Search Text</label>
              <Input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search messages..."
                className="w-full"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Client ID</label>
                <div className="relative">
                  <Input
                    type="text"
                    value={selectedClient}
                    onChange={(e) => setSelectedClient(e.target.value)}
                    placeholder="e.g., client_123"
                    className="w-full"
                  />
                  {autocompleteData?.clients && autocompleteData.clients.length > 0 && (
                    <div className="absolute top-full left-0 right-0 bg-white border border-gray-300 rounded mt-1 z-10">
                      {autocompleteData.clients.map((client: string) => (
                        <button
                          key={client}
                          type="button"
                          onClick={() => setSelectedClient(client)}
                          className="w-full text-left px-3 py-2 hover:bg-gray-100 text-sm"
                        >
                          {client}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Scenario</label>
                <select
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                >
                  <option value="">All Scenarios</option>
                  <option value="GREETING">GREETING</option>
                  <option value="REFERRAL">REFERRAL</option>
                  <option value="TECH_SUPPORT_BASIC">TECH_SUPPORT</option>
                  <option value="UNKNOWN">UNKNOWN</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Min Confidence: {(minConfidence * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={minConfidence}
                onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            <Button type="submit" className="w-full">Search</Button>
          </form>
        </Card>

        {/* Export Buttons */}
        {selectedClient && (
          <div className="mb-6 flex gap-2">
            <Button
              onClick={() => handleExport('csv')}
              variant="outline"
            >
              📥 Export CSV
            </Button>
            <Button
              onClick={() => handleExport('json')}
              variant="outline"
            >
              📥 Export JSON
            </Button>
          </div>
        )}

        {/* Results */}
        <Card className="p-6">
          {isLoading ? (
            <p className="text-gray-500">Loading...</p>
          ) : searchResults ? (
            <>
              <p className="text-sm text-gray-600 mb-4">
                Found {searchResults.count} of {searchResults.total} messages
              </p>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {searchResults.messages.map((msg: any) => (
                  <div key={msg.id} className="p-3 bg-gray-50 border border-gray-200 rounded">
                    <p className="font-medium text-sm">{msg.content}</p>
                    <div className="flex gap-2 items-center mt-2 text-xs">
                      <Badge variant="outline">{msg.message_type}</Badge>
                      <span className="text-gray-500">{msg.client_id}</span>
                      <span className="text-gray-500">
                        {new Date(msg.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {searchResults.total > 50 && (
                <div className="mt-4 flex gap-2 justify-center">
                  <Button
                    variant="outline"
                    onClick={() => setOffset(Math.max(0, offset - 50))}
                    disabled={offset === 0}
                  >
                    ← Previous
                  </Button>
                  <span className="px-4 py-2 text-sm">
                    Page {Math.floor(offset / 50) + 1}
                  </span>
                  <Button
                    variant="outline"
                    onClick={() => setOffset(offset + 50)}
                    disabled={offset + 50 >= searchResults.total}
                  >
                    Next →
                  </Button>
                </div>
              )}
            </>
          ) : (
            <p className="text-gray-500">Enter search criteria to begin</p>
          )}
        </Card>
      </div>
    </div>
  )
}

