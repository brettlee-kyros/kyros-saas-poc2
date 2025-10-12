'use client'

import { useEffect, useState } from 'react'

interface HealthStatus {
  status: string
  timestamp: string
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchHealth() {
      try {
        const response = await fetch('/api/health')
        if (!response.ok) {
          throw new Error('API health check failed')
        }
        const data = await response.json()
        setHealth(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchHealth()
  }, [])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-8">
          Kyros PoC
        </h1>

        <div className="border border-gray-300 rounded-lg p-6 bg-white shadow-sm">
          <h2 className="text-xl font-semibold mb-4">API Health Status</h2>

          {loading && <p className="text-gray-500">Loading...</p>}

          {error && (
            <div className="text-red-600">
              <p className="font-semibold">Error:</p>
              <p>{error}</p>
            </div>
          )}

          {health && (
            <div className="text-green-600">
              <p><span className="font-semibold">Status:</span> {health.status}</p>
              <p className="text-sm text-gray-500 mt-2">
                Last checked: {new Date(health.timestamp).toLocaleString()}
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
