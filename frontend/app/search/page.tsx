'use client'

import { useState, useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchAPI } from '@/lib/api'
import type { AxiosResponse } from 'axios'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatDate } from '@/lib/utils'

type SortField = 'created_at' | 'client_id' | 'message_type' | 'scenario' | 'confidence'
type SortDirection = 'asc' | 'desc'

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedClient, setSelectedClient] = useState('')
  const [scenario, setScenario] = useState('')
  const [minConfidence, setMinConfidence] = useState(0)
  const [offset, setOffset] = useState(0)
  const [sortField, setSortField] = useState<SortField>('created_at')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table')

  // Search messages
  const { data: searchResults, isLoading, refetch } = useQuery({
    queryKey: ['search', 'messages', searchQuery, selectedClient, scenario, minConfidence, offset],
    queryFn: () =>
      searchAPI.searchMessages({
        q: searchQuery,
        client_id: selectedClient || undefined,
        scenario: scenario || undefined,
        min_confidence: minConfidence,
        offset,
      }).then((r: AxiosResponse) => r.data),
    enabled: searchQuery.length >= 3 || selectedClient.length > 0,
  })

  // Autocomplete clients
  const { data: autocompleteData } = useQuery({
    queryKey: ['search', 'clients', 'autocomplete', selectedClient],
    queryFn: () =>
      searchAPI.autocompleteClients(selectedClient).then((r: AxiosResponse) => r.data),
    enabled: selectedClient.length > 0,
  })

  // Sort and filter results
  const sortedResults = useMemo(() => {
    if (!searchResults?.messages) return []
    
    const sorted = [...searchResults.messages].sort((a, b) => {
      let aVal: any, bVal: any
      
      switch (sortField) {
        case 'created_at':
          aVal = new Date(a.created_at).getTime()
          bVal = new Date(b.created_at).getTime()
          break
        case 'client_id':
          aVal = a.client_id.toLowerCase()
          bVal = b.client_id.toLowerCase()
          break
        case 'message_type':
          aVal = a.message_type.toLowerCase()
          bVal = b.message_type.toLowerCase()
          break
        case 'scenario':
          aVal = a.classification?.scenario || ''
          bVal = b.classification?.scenario || ''
          break
        case 'confidence':
          aVal = a.classification?.confidence || 0
          bVal = b.classification?.confidence || 0
          break
        default:
          return 0
      }
      
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
      return 0
    })
    
    return sorted
  }, [searchResults, sortField, sortDirection])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setOffset(0)
    // Explicitly trigger search if query is valid
    if (searchQuery.length >= 3 || selectedClient.length > 0) {
      refetch()
    }
  }

  // Auto-trigger search when selectedClient changes (if valid)
  useEffect(() => {
    if (selectedClient.length > 0 && searchQuery.length < 3) {
      // If only client ID is provided, trigger search
      refetch()
    }
  }, [selectedClient])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const handleExportSearchResults = async (format: 'csv' | 'json') => {
    if (!searchResults?.messages || searchResults.messages.length === 0) return

    try {
      const searchParams = {
        q: searchQuery,
        client_id: selectedClient || undefined,
        scenario: scenario || undefined,
        min_confidence: minConfidence,
        limit: searchResults.total, // Export all results
      }

      if (format === 'csv') {
        // Use backend export endpoint for CSV
        const response = await searchAPI.exportSearchResults(searchParams, 'csv')
        const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `search_results_${new Date().toISOString().split('T')[0]}.csv`
        link.click()
      } else {
        // Use backend export endpoint for JSON
        const response = await searchAPI.exportSearchResults(searchParams, 'json')
        const jsonData = response.data
        const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `search_results_${new Date().toISOString().split('T')[0]}.json`
        link.click()
      }
    } catch (error) {
      console.error('Export error:', error)
      alert('Ошибка при экспорте данных')
    }
  }

  const handleExportDialog = async (format: 'csv' | 'json') => {
    if (!selectedClient) return
    try {
      const response = await searchAPI.exportDialog(selectedClient, format)
      const blob = format === 'csv' 
        ? new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
        : new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `dialog_${selectedClient}_${new Date().toISOString().split('T')[0]}.${format}`
      link.click()
    } catch (error) {
      console.error('Export error:', error)
      alert('Ошибка при экспорте диалога')
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null
    return sortDirection === 'asc' ? '↑' : '↓'
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Поиск и анализ диалогов</h1>
          <p className="text-gray-600">Найдите и проанализируйте переписки с клиентами</p>
        </div>

        {/* Search Form */}
        <Card className="p-6 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Поиск по тексту</label>
                <Input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Введите текст для поиска..."
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Client ID</label>
                <div className="relative">
                  <Input
                    type="text"
                    value={selectedClient}
                    onChange={(e) => setSelectedClient(e.target.value)}
                    placeholder="например, client_123 или telegram_123456"
                    className="w-full"
                  />
                  {autocompleteData?.clients && autocompleteData.clients.length > 0 && (
                    <div className="absolute top-full left-0 right-0 bg-white border border-gray-300 rounded mt-1 z-10 shadow-lg">
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
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Сценарий</label>
                <select
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                >
                  <option value="">Все сценарии</option>
                  <option value="GREETING">GREETING</option>
                  <option value="REFERRAL">REFERRAL</option>
                  <option value="TECH_SUPPORT_BASIC">TECH_SUPPORT_BASIC</option>
                  <option value="ABSENCE_REQUEST">ABSENCE_REQUEST</option>
                  <option value="SCHEDULE_CHANGE">SCHEDULE_CHANGE</option>
                  <option value="COMPLAINT">COMPLAINT</option>
                  <option value="MISSING_TRAINER">MISSING_TRAINER</option>
                  <option value="REVIEW_BONUS">REVIEW_BONUS</option>
                  <option value="UNKNOWN">UNKNOWN</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Минимальная уверенность: {(minConfidence * 100).toFixed(0)}%
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
            </div>

            <Button type="submit" className="w-full">Поиск</Button>
          </form>
        </Card>

        {/* Export Buttons */}
        {searchResults && searchResults.messages.length > 0 && (
          <div className="mb-6 flex gap-2 flex-wrap">
            <Button
              onClick={() => handleExportSearchResults('csv')}
              variant="outline"
            >
              📥 Экспорт результатов в CSV
            </Button>
            <Button
              onClick={() => handleExportSearchResults('json')}
              variant="outline"
            >
              📥 Экспорт результатов в JSON
            </Button>
            {selectedClient && (
              <>
                <Button
                  onClick={() => handleExportDialog('csv')}
                  variant="outline"
                >
                  📥 Экспорт диалога CSV
                </Button>
                <Button
                  onClick={() => handleExportDialog('json')}
                  variant="outline"
                >
                  📥 Экспорт диалога JSON
                </Button>
              </>
            )}
          </div>
        )}

        {/* Results */}
        <Card className="p-6">
          {isLoading ? (
            <p className="text-gray-500">Загрузка...</p>
          ) : searchResults ? (
            <>
              <div className="flex justify-between items-center mb-4">
                <p className="text-sm text-gray-600">
                  Найдено {searchResults.count} из {searchResults.total} сообщений
                </p>
                <div className="flex gap-2">
                  <Button
                    variant={viewMode === 'table' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('table')}
                  >
                    Таблица
                  </Button>
                  <Button
                    variant={viewMode === 'cards' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('cards')}
                  >
                    Карточки
                  </Button>
                </div>
              </div>

              {viewMode === 'table' ? (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort('created_at')}
                        >
                          Дата/Время <SortIcon field="created_at" />
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort('client_id')}
                        >
                          Client ID <SortIcon field="client_id" />
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort('message_type')}
                        >
                          Тип <SortIcon field="message_type" />
                        </TableHead>
                        <TableHead>Содержание</TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort('scenario')}
                        >
                          Сценарий <SortIcon field="scenario" />
                        </TableHead>
                        <TableHead 
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => handleSort('confidence')}
                        >
                          Уверенность <SortIcon field="confidence" />
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sortedResults.map((msg: any) => (
                        <TableRow key={msg.id}>
                          <TableCell className="font-mono text-xs">
                            {formatDate(msg.created_at)}
                          </TableCell>
                          <TableCell className="font-mono text-xs">
                            {msg.client_id}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{msg.message_type}</Badge>
                          </TableCell>
                          <TableCell className="max-w-md">
                            <p className="text-sm truncate" title={msg.content}>
                              {msg.content}
                            </p>
                          </TableCell>
                          <TableCell>
                            {msg.classification?.scenario ? (
                              <Badge variant="outline">{msg.classification.scenario}</Badge>
                            ) : (
                              <span className="text-gray-400">—</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {msg.classification?.confidence ? (
                              <span className="text-sm">
                                {(msg.classification.confidence * 100).toFixed(1)}%
                              </span>
                            ) : (
                              <span className="text-gray-400">—</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {sortedResults.map((msg: any) => (
                    <div key={msg.id} className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex gap-2 items-center">
                          <Badge variant="outline">{msg.message_type}</Badge>
                          <span className="text-xs text-gray-500 font-mono">{msg.client_id}</span>
                          {msg.classification?.scenario && (
                            <Badge variant="outline">{msg.classification.scenario}</Badge>
                          )}
                        </div>
                        <span className="text-xs text-gray-500">
                          {formatDate(msg.created_at)}
                        </span>
                      </div>
                      <p className="text-sm mb-2">{msg.content}</p>
                      {msg.classification && (
                        <div className="text-xs text-gray-600">
                          Уверенность: {(msg.classification.confidence * 100).toFixed(1)}%
                          {msg.classification.reasoning && (
                            <span className="ml-2">• {msg.classification.reasoning}</span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Pagination */}
              {searchResults.total > 50 && (
                <div className="mt-6 flex gap-2 justify-center items-center">
                  <Button
                    variant="outline"
                    onClick={() => setOffset(Math.max(0, offset - 50))}
                    disabled={offset === 0}
                  >
                    ← Назад
                  </Button>
                  <span className="px-4 py-2 text-sm">
                    Страница {Math.floor(offset / 50) + 1} из {Math.ceil(searchResults.total / 50)}
                  </span>
                  <Button
                    variant="outline"
                    onClick={() => setOffset(offset + 50)}
                    disabled={offset + 50 >= searchResults.total}
                  >
                    Вперед →
                  </Button>
                </div>
              )}
            </>
          ) : (
            <p className="text-gray-500">Введите критерии поиска для начала</p>
          )}
        </Card>
      </div>
    </div>
  )
}
