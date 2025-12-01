'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AxiosResponse } from 'axios'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'

export default function AnalyticsPage() {
  const [hours, setHours] = useState(24)

  // Get analytics report
  const { data: report, isLoading } = useQuery({
    queryKey: ['analytics', 'report', hours],
    queryFn: () =>
      api.get('/api/search/export/report', {
        params: { hours }
      }).then((r: AxiosResponse) => r.data),
    refetchInterval: 60000,
  })

  const handleExport = async () => {
    try {
      const response = await api.get('/api/search/export/report', {
        params: { hours }
      })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(
        new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
      )
      link.download = `analytics_report_${new Date().toISOString().split('T')[0]}.json`
      link.click()
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  if (isLoading) {
    return <div className="p-8 text-center">Loading analytics...</div>
  }

  if (!report) {
    return <div className="p-8 text-center text-gray-500">No data available</div>
  }

  const messageByTypeData = Object.entries(report.messages.by_type || {}).map(
    ([type, count]) => ({ name: type, value: count })
  )

  const scenarioData = Object.entries(report.classifications.by_scenario || {}).map(
    ([scenario, count]) => ({ name: scenario, value: count })
  )

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Analytics Dashboard</h1>
            <p className="text-gray-600">
              Period: {report.period.hours} hours ({new Date(report.period.start).toLocaleString()})
            </p>
          </div>
          <div className="flex gap-2">
            <select
              value={hours}
              onChange={(e) => setHours(parseInt(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded"
            >
              <option value={24}>Last 24 hours</option>
              <option value={168}>Last week</option>
              <option value={720}>Last month</option>
            </select>
            <Button onClick={handleExport}>Export Report</Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <Card className="p-4">
            <p className="text-sm text-gray-600">Total Messages</p>
            <p className="text-2xl font-bold">{report.messages.total}</p>
          </Card>

          <Card className="p-4">
            <p className="text-sm text-gray-600">Classifications</p>
            <p className="text-2xl font-bold">{report.classifications.total}</p>
          </Card>

          <Card className="p-4">
            <p className="text-sm text-gray-600">Avg Confidence</p>
            <p className="text-2xl font-bold">
              {(report.classifications.avg_confidence * 100).toFixed(1)}%
            </p>
          </Card>

          <Card className="p-4">
            <p className="text-sm text-gray-600">Accuracy Rate</p>
            <p className="text-2xl font-bold text-green-600">
              {(report.feedback.accuracy_rate * 100).toFixed(1)}%
            </p>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-2 gap-8 mb-8">
          {/* Message Types */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Messages by Type</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={messageByTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {messageByTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>

          {/* Scenarios */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Classifications by Scenario</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scenarioData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Feedback Stats */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Feedback Summary</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Total Feedback</p>
              <p className="text-2xl font-bold">{report.feedback.total}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Correct</p>
              <p className="text-2xl font-bold text-green-600">{report.feedback.correct}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Incorrect</p>
              <p className="text-2xl font-bold text-red-600">{report.feedback.incorrect}</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

