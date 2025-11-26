'use client'

import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useMutation } from '@tanstack/react-query'

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('feedback')

  // Feedback Summary
  const { data: feedbackData, isLoading: feedbackLoading } = useQuery({
    queryKey: ['admin', 'feedback', 'summary'],
    queryFn: () => api.get('/api/admin/feedback/summary').then(r => r.data),
    refetchInterval: 30000,
  })

  // Classification Stats
  const { data: classificationStats } = useQuery({
    queryKey: ['admin', 'stats', 'classifications'],
    queryFn: () => api.get('/api/admin/stats/classifications').then(r => r.data),
    refetchInterval: 30000,
  })

  // Message Stats
  const { data: messageStats } = useQuery({
    queryKey: ['admin', 'stats', 'messages'],
    queryFn: () => api.get('/api/admin/stats/messages').then(r => r.data),
    refetchInterval: 30000,
  })

  // Misclassified Messages
  const { data: misclassified } = useQuery({
    queryKey: ['admin', 'feedback', 'misclassified'],
    queryFn: () => api.get('/api/admin/feedback/misclassified').then(r => r.data),
  })

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">System analytics and management</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <Card className="p-4">
            <p className="text-sm text-gray-600 mb-1">Total Messages</p>
            <p className="text-2xl font-bold">{messageStats?.total_messages || 0}</p>
          </Card>
          
          <Card className="p-4">
            <p className="text-sm text-gray-600 mb-1">Unique Clients</p>
            <p className="text-2xl font-bold">{messageStats?.unique_clients || 0}</p>
          </Card>
          
          <Card className="p-4">
            <p className="text-sm text-gray-600 mb-1">Feedback Received</p>
            <p className="text-2xl font-bold">{feedbackData?.total_feedback || 0}</p>
          </Card>
          
          <Card className="p-4">
            <p className="text-sm text-gray-600 mb-1">Accuracy Rate</p>
            <p className="text-2xl font-bold">
              {feedbackData ? (feedbackData.accuracy_rate * 100).toFixed(1) : 0}%
            </p>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="feedback">Feedback</TabsTrigger>
            <TabsTrigger value="classifications">Classifications</TabsTrigger>
            <TabsTrigger value="templates">Templates</TabsTrigger>
            <TabsTrigger value="keywords">Keywords</TabsTrigger>
          </TabsList>

          {/* Feedback Tab */}
          <TabsContent value="feedback" className="space-y-4">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Feedback Summary</h3>
              
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div>
                  <p className="text-sm text-gray-600">Correct</p>
                  <p className="text-xl font-bold text-green-600">
                    {feedbackData?.correct || 0}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Incorrect</p>
                  <p className="text-xl font-bold text-red-600">
                    {feedbackData?.incorrect || 0}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Rate</p>
                  <p className="text-xl font-bold">
                    {feedbackData ? (feedbackData.accuracy_rate * 100).toFixed(1) : 0}%
                  </p>
                </div>
              </div>

              {feedbackData?.scenarios && Object.keys(feedbackData.scenarios).length > 0 && (
                <div className="space-y-2">
                  <p className="font-semibold text-sm">By Scenario:</p>
                  <div className="space-y-2">
                    {Object.entries(feedbackData.scenarios).map(([scenario, stats]: [string, any]) => (
                      <div key={scenario} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="font-medium">{scenario}</span>
                        <div className="flex gap-2">
                          <Badge variant="outline" className="bg-green-50">
                            ✓ {stats.correct}
                          </Badge>
                          <Badge variant="outline" className="bg-red-50">
                            ✗ {stats.incorrect}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>

            {/* Misclassified Messages */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Misclassified Messages</h3>
              
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {misclassified?.messages?.map((msg: any) => (
                  <div key={msg.message_id} className="p-3 bg-red-50 border border-red-200 rounded text-sm">
                    <p className="font-medium mb-1">{msg.content}</p>
                    <div className="flex gap-2 items-center text-xs">
                      <Badge variant="outline">Detected: {msg.detected_scenario}</Badge>
                      <Badge className="bg-green-100">Should be: {msg.suggested_scenario}</Badge>
                    </div>
                    {msg.comment && <p className="text-gray-600 mt-1 italic">"{msg.comment}"</p>}
                  </div>
                )) || <p className="text-gray-500">No misclassified messages</p>}
              </div>
            </Card>
          </TabsContent>

          {/* Classifications Tab */}
          <TabsContent value="classifications">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Classification Stats</h3>
              
              <div className="space-y-3">
                {classificationStats?.scenarios?.map((scenario: any) => (
                  <div key={scenario.scenario} className="p-3 bg-gray-50 rounded">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{scenario.scenario}</p>
                        <p className="text-sm text-gray-600">
                          Avg Confidence: {(scenario.avg_confidence * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold">{scenario.count}</p>
                        <p className="text-xs text-gray-500">classifications</p>
                      </div>
                    </div>
                  </div>
                )) || <p className="text-gray-500">No data</p>}
              </div>
            </Card>
          </TabsContent>

          {/* Templates Tab */}
          <TabsContent value="templates">
            <TemplatesManager />
          </TabsContent>

          {/* Keywords Tab */}
          <TabsContent value="keywords">
            <KeywordsManager />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

// Templates Manager Component
function TemplatesManager() {
  const [editingScenario, setEditingScenario] = useState<string | null>(null)
  const [editText, setEditText] = useState('')
  const queryClient = useQueryClient()

  const { data: templates } = useQuery({
    queryKey: ['admin', 'templates'],
    queryFn: () => api.get('/api/admin/templates').then(r => r.data),
  })

  const updateMutation = useMutation({
    mutationFn: ({ scenario, data }: { scenario: string; data: any }) =>
      api.post(`/api/admin/templates/${scenario}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'templates'] })
      setEditingScenario(null)
    },
  })

  const handleSave = async (scenario: string) => {
    try {
      await updateMutation.mutateAsync({
        scenario,
        data: { template_text: editText },
      })
    } catch (error) {
      console.error('Failed to update template:', error)
    }
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Response Templates</h3>
      
      <div className="space-y-4">
        {templates?.map((template: any) => (
          <div key={template.id} className="p-4 border border-gray-200 rounded">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h4 className="font-semibold">{template.scenario_name}</h4>
                <p className="text-xs text-gray-500">v{template.version}</p>
              </div>
              <Badge variant={template.is_active ? 'default' : 'secondary'}>
                {template.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            
            {editingScenario === template.scenario_name ? (
              <div className="space-y-2">
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded text-sm"
                  rows={4}
                />
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleSave(template.scenario_name)}
                    disabled={updateMutation.isPending}
                  >
                    Save
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditingScenario(null)}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <p className="text-sm text-gray-600 mb-2">{template.template_text.substring(0, 100)}...</p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setEditingScenario(template.scenario_name)
                    setEditText(template.template_text)
                  }}
                >
                  Edit
                </Button>
              </>
            )}
          </div>
        )) || <p className="text-gray-500">No templates found</p>}
      </div>
    </Card>
  )
}

// Keywords Manager Component
function KeywordsManager() {
  const [newKeyword, setNewKeyword] = useState('')
  const [selectedScenario, setSelectedScenario] = useState('GREETING')
  const [priority, setPriority] = useState(5)
  const queryClient = useQueryClient()

  const { data: keywords } = useQuery({
    queryKey: ['admin', 'keywords', selectedScenario],
    queryFn: () => api.get(`/api/admin/keywords?scenario=${selectedScenario}`).then(r => r.data),
  })

  const addMutation = useMutation({
    mutationFn: (params: { scenario: string; keyword: string; priority: number }) =>
      api.post('/api/admin/keywords', null, { params }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'keywords'] })
      setNewKeyword('')
    },
  })

  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) return
    try {
      await addMutation.mutateAsync({
        scenario: selectedScenario,
        keyword: newKeyword,
        priority,
      })
    } catch (error) {
      console.error('Failed to add keyword:', error)
    }
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Keywords Management</h3>
      
      <div className="space-y-4">
        <div className="flex gap-2">
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded text-sm"
          >
            <option value="GREETING">GREETING</option>
            <option value="REFERRAL">REFERRAL</option>
            <option value="TECH_SUPPORT_BASIC">TECH_SUPPORT_BASIC</option>
          </select>
          
          <input
            type="text"
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            placeholder="Add new keyword"
            className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
          />
          
          <input
            type="number"
            min="1"
            max="10"
            value={priority}
            onChange={(e) => setPriority(parseInt(e.target.value))}
            className="w-16 px-2 py-2 border border-gray-300 rounded text-sm"
          />
          
          <Button size="sm" onClick={handleAddKeyword} disabled={addMutation.isPending}>
            Add
          </Button>
        </div>
        <div className="space-y-2">
          {keywords?.keywords?.map((kw: any) => (
            <div key={kw.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span className="font-medium text-sm">{kw.keyword}</span>
              <Badge variant="outline">Priority: {kw.priority}</Badge>
            </div>
          )) || <p className="text-gray-500">No keywords found</p>}
        </div>
      </div>
    </Card>
  )
}

