'use client'

import { useState, useEffect } from 'react'
import { jwtDecode } from 'jwt-decode'
import { useAuth } from '@/contexts/AuthContext'
import { useTenantStore } from '@/stores/useTenantStore'

interface DecodedToken {
  sub?: string
  email?: string
  tenant_id?: string
  tenant_ids?: string[]
  role?: string
  iat?: number
  exp?: number
  iss?: string
  [key: string]: string | number | string[] | undefined
}

/**
 * JWT Debug Panel Component
 *
 * Displays decoded JWT claims and expiry countdown for demonstration purposes.
 * Shows token exchange mechanism: User Token (tenant_ids[]) → Tenant Token (tenant_id)
 *
 * AC 1, 2, 3: Collapsible panel in top-right corner
 * AC 4: Displays token type, decoded claims, expiry countdown
 * AC 5, 6: Highlights tenant_id vs tenant_ids
 * AC 7: Live countdown with expiry warning
 * AC 8: Tailwind CSS styling
 * AC 9: Uses jwt-decode library
 * AC 10: Handles missing/invalid tokens
 * AC 12: Re-renders on token changes
 */
export default function DebugPanel() {
  const [isExpanded, setIsExpanded] = useState(false)
  const [decodedToken, setDecodedToken] = useState<DecodedToken | null>(null)
  const [tokenError, setTokenError] = useState<string | null>(null)
  const [timeRemaining, setTimeRemaining] = useState<string>('')
  const [isExpired, setIsExpired] = useState(false)

  const { userToken } = useAuth()
  const { tenantToken } = useTenantStore()

  // Determine which token to display (tenant token takes precedence)
  const activeToken = tenantToken || userToken
  const tokenType = tenantToken ? 'Tenant-Scoped Token' : userToken ? 'User Access Token' : null

  // Decode token and handle errors (AC 9, 10)
  useEffect(() => {
    if (!activeToken) {
      setDecodedToken(null)
      setTokenError('No token available')
      setTimeRemaining('')
      return
    }

    try {
      const decoded = jwtDecode<DecodedToken>(activeToken)
      setDecodedToken(decoded)
      setTokenError(null)
    } catch (error) {
      console.error('JWT decode error:', error)
      setDecodedToken(null)
      setTokenError('Invalid token format')
    }
  }, [activeToken])

  // Expiry countdown timer (AC 7)
  useEffect(() => {
    if (!decodedToken?.exp) {
      setTimeRemaining('')
      setIsExpired(false)
      return
    }

    const updateCountdown = () => {
      const now = Math.floor(Date.now() / 1000)
      const exp = decodedToken.exp!
      const remaining = exp - now

      if (remaining <= 0) {
        setTimeRemaining('Expired')
        setIsExpired(true)
        return
      }

      setIsExpired(false)

      // Format as "45m 23s"
      const minutes = Math.floor(remaining / 60)
      const seconds = remaining % 60

      if (minutes > 0) {
        setTimeRemaining(`${minutes}m ${seconds}s`)
      } else {
        setTimeRemaining(`${seconds}s`)
      }
    }

    // Initial update
    updateCountdown()

    // Update every second
    const interval = setInterval(updateCountdown, 1000)

    return () => clearInterval(interval)
  }, [decodedToken])

  // Don't render on login page
  if (typeof window !== 'undefined' && window.location.pathname === '/login') {
    return null
  }

  return (
    <div className="fixed top-4 right-4 z-50">
      {/* Toggle Button (AC 3) */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="bg-gray-900 bg-opacity-90 hover:bg-opacity-100 text-white px-4 py-2 rounded-md shadow-lg transition-all flex items-center space-x-2"
      >
        <span className="text-sm font-semibold">🔍 Debug</span>
        {!isExpanded && tokenType && (
          <span className="text-xs bg-blue-600 px-2 py-0.5 rounded">
            {tokenType === 'Tenant-Scoped Token' ? 'Tenant' : 'User'}
          </span>
        )}
        <svg
          className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded Panel (AC 2, 4, 8) */}
      {isExpanded && (
        <div className="mt-2 bg-gray-900 bg-opacity-95 text-white rounded-lg shadow-2xl p-4 w-96 max-h-[80vh] overflow-y-auto">
          <h3 className="text-lg font-bold mb-3 border-b border-gray-700 pb-2">
            JWT Debug Panel
          </h3>

          {/* No Token State (AC 10) */}
          {!activeToken && (
            <div className="text-gray-400 text-sm text-center py-8">
              <p className="mb-2">🔒 No token available</p>
              <p className="text-xs">Log in to see JWT claims</p>
            </div>
          )}

          {/* Token Error State (AC 10) */}
          {tokenError && activeToken && (
            <div className="bg-red-900 bg-opacity-50 border border-red-700 rounded p-3 mb-3">
              <p className="text-red-300 text-sm">
                ⚠️ {tokenError}
              </p>
            </div>
          )}

          {/* Token Display */}
          {decodedToken && !tokenError && (
            <>
              {/* Token Type (AC 5, 6) */}
              <div className="mb-4">
                <p className="text-xs text-gray-400 mb-1">Token Type:</p>
                <div className="flex items-center space-x-2">
                  <span className={`px-3 py-1 rounded text-sm font-semibold ${
                    tokenType === 'Tenant-Scoped Token'
                      ? 'bg-green-600'
                      : 'bg-blue-600'
                  }`}>
                    {tokenType}
                  </span>
                  {tokenType === 'Tenant-Scoped Token' && (
                    <span className="text-xs text-green-400">✓ Scoped</span>
                  )}
                </div>
              </div>

              {/* Expiry Countdown (AC 7) */}
              <div className="mb-4">
                <p className="text-xs text-gray-400 mb-1">Token Expiry:</p>
                <div className={`text-lg font-mono font-bold ${
                  isExpired ? 'text-red-500' : 'text-green-400'
                }`}>
                  {isExpired ? '🔴 Expired' : `⏱️  ${timeRemaining}`}
                </div>
                {decodedToken.exp && (
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(decodedToken.exp * 1000).toLocaleString()}
                  </p>
                )}
              </div>

              {/* Decoded Claims (AC 4, 5, 6) */}
              <div>
                <p className="text-xs text-gray-400 mb-2">Decoded Claims:</p>
                <div className="bg-black bg-opacity-50 rounded p-3 font-mono text-xs overflow-x-auto">
                  <pre className="whitespace-pre-wrap break-words">
{JSON.stringify(decodedToken, null, 2).split('\n').map((line, i) => {
  // Highlight tenant_id (single value - AC 5)
  if (line.includes('"tenant_id"')) {
    return (
      <div key={i} className="bg-green-900 bg-opacity-50 border-l-4 border-green-500 pl-2 -ml-2">
        {line} <span className="text-green-400">← Single tenant</span>
      </div>
    )
  }
  // Highlight tenant_ids (array - AC 6)
  if (line.includes('"tenant_ids"')) {
    return (
      <div key={i} className="bg-blue-900 bg-opacity-50 border-l-4 border-blue-500 pl-2 -ml-2">
        {line} <span className="text-blue-400">← Multi-tenant</span>
      </div>
    )
  }
  return <div key={i}>{line}</div>
})}
                  </pre>
                </div>
              </div>

              {/* Token Info */}
              <div className="mt-4 pt-3 border-t border-gray-700 text-xs text-gray-400">
                <p className="mb-1">
                  <span className="text-gray-500">Subject:</span> {decodedToken.sub?.substring(0, 8)}...
                </p>
                <p className="mb-1">
                  <span className="text-gray-500">Email:</span> {decodedToken.email}
                </p>
                <p>
                  <span className="text-gray-500">Issuer:</span> {decodedToken.iss}
                </p>
              </div>
            </>
          )}

          {/* PoC Note */}
          <div className="mt-4 pt-3 border-t border-gray-700 text-xs text-gray-500">
            <p className="italic">
              💡 This panel demonstrates the JWT token exchange mechanism for stakeholder visibility.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
