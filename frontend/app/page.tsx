"use client"

import { useEffect, useState } from "react"
import { healthAPI } from "@/lib/api"

export default function Home() {
  const [status, setStatus] = useState("checking...")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await healthAPI.check()
        setStatus("Backend is running ✅")
      } catch (err: any) {
        setError("Backend is not available ❌")
      }
    }
    
    checkHealth()
  }, [])

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Dashboard</h2>
      <div className="p-4 bg-gray-100 rounded">
        <p>Backend Status: {error || status}</p>
      </div>
      <a href="/dashboard" className="text-blue-500 hover:underline">
        Go to Operator Dashboard →
      </a>
    </div>
  )
}

