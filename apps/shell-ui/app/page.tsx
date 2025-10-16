'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import AuthGuard from '@/components/auth/AuthGuard'
import { useAuth } from '@/contexts/AuthContext'
import { useTenantStore } from '@/stores/useTenantStore'
import type { UserInfoResponse, Tenant, TokenExchangeRequest, TokenExchangeResponse } from '@/types/tenant'

function TenantSelectionPage() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [exchanging, setExchanging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null)

  const { logout, userToken } = useAuth()
  const { setSelectedTenant, setTenantToken } = useTenantStore()
  const router = useRouter()

  // Fetch user tenants on mount (AC 1)
  useEffect(() => {
    async function fetchUserTenants() {
      if (!userToken) {
        setError('No user token available')
        setLoading(false)
        return
      }

      try {
        const response = await fetch('/api/me', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${userToken}`,
            'Content-Type': 'application/json',
          },
        })

        if (response.status === 401) {
          setError('Session expired. Please log in again.')
          setLoading(false)
          return
        }

        if (!response.ok) {
          throw new Error('Failed to fetch user information')
        }

        const data: UserInfoResponse = await response.json()
        setTenants(data.tenants)

        // Auto-select if user has only one tenant (AC 9)
        if (data.tenants.length === 1) {
          await handleTenantExchange(data.tenants[0])
        }

        setLoading(false)
      } catch (err) {
        console.error('Error fetching tenants:', err)
        setError('Network error. Please check your connection and try again.')
        setLoading(false)
      }
    }

    fetchUserTenants()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userToken])

  // Token exchange function (AC 5, 6)
  const handleTenantExchange = async (tenant: Tenant) => {
    setExchanging(true)
    setSelectedTenantId(tenant.tenant_id)
    setError(null)

    try {
      const request: TokenExchangeRequest = {
        tenant_id: tenant.tenant_id,
      }

      const response = await fetch('/api/token/exchange', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      // Handle 403 - access denied (AC 11)
      if (response.status === 403) {
        setError('Access denied. You do not have permission to access this tenant.')
        setExchanging(false)
        setSelectedTenantId(null)
        return
      }

      // Handle 401 - invalid token (AC 11)
      if (response.status === 401) {
        setError('Session expired. Please log in again.')
        setExchanging(false)
        setSelectedTenantId(null)
        return
      }

      if (!response.ok) {
        throw new Error('Token exchange failed')
      }

      const data: TokenExchangeResponse = await response.json()

      // Store tenant-scoped token and selected tenant (AC 6, 7)
      setTenantToken(data.access_token)
      setSelectedTenant(tenant)

      // Redirect to tenant dashboard listing (AC 8)
      router.push(`/tenant/${tenant.slug}`)
    } catch (err) {
      console.error('Token exchange error:', err)
      setError('Failed to exchange token. Please try again.')
      setExchanging(false)
      setSelectedTenantId(null)
    }
  }

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  // Loading state (AC 10)
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your tenants...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error && tenants.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="text-red-600 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Tenants</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="space-y-3">
              <button
                onClick={() => window.location.reload()}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
              >
                Retry
              </button>
              <button
                onClick={handleLogout}
                className="w-full px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-md transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Tenant selection UI (AC 2, 3, 4)
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Select Your Tenant
            </h1>
            <p className="text-gray-600">
              Choose a tenant to access dashboards
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
          >
            Logout
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">
              <span className="font-semibold">Error:</span> {error}
            </p>
          </div>
        )}

        {/* Tenant Cards Grid (AC 2) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tenants.map((tenant) => {
            const isExchanging = exchanging && selectedTenantId === tenant.tenant_id
            const primaryColor = tenant.config_json?.branding?.primary_color || '#2563eb'
            const description = tenant.config_json?.description || 'No description available'

            return (
              <div
                key={tenant.tenant_id}
                className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow"
              >
                {/* Tenant Card Header with branding color (AC 4) */}
                <div
                  className="h-3"
                  style={{ backgroundColor: primaryColor }}
                />

                <div className="p-6">
                  {/* Tenant Name (AC 3) */}
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    {tenant.name}
                  </h3>

                  {/* Tenant Description (AC 3) */}
                  <p className="text-gray-600 mb-4 min-h-[3rem]">
                    {description}
                  </p>

                  {/* Tenant Metadata */}
                  <div className="mb-4 text-xs text-gray-500 space-y-1">
                    <p className="font-mono">Slug: {tenant.slug}</p>
                  </div>

                  {/* Select Button (AC 3) */}
                  <button
                    onClick={() => handleTenantExchange(tenant)}
                    disabled={exchanging}
                    className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed"
                  >
                    {isExchanging ? (
                      <span className="flex items-center justify-center">
                        <svg
                          className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Exchanging Token...
                      </span>
                    ) : (
                      'Select Tenant'
                    )}
                  </button>
                </div>
              </div>
            )
          })}
        </div>

        {/* No Tenants Message */}
        {tenants.length === 0 && !loading && !error && (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <p className="text-gray-600 text-lg">
              You don&apos;t have access to any tenants. Please contact your administrator.
            </p>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <span className="font-semibold">PoC Demonstration:</span> This page demonstrates the token exchange mechanism.
            After selecting a tenant, your user access token (multi-tenant) is exchanged for a tenant-scoped token (single tenant).
          </p>
        </div>
      </div>
    </div>
  )
}

// Wrap with AuthGuard to protect this route
export default function Home() {
  return (
    <AuthGuard>
      <TenantSelectionPage />
    </AuthGuard>
  )
}
