'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import AuthGuard from '@/components/auth/AuthGuard'
import { useTenantStore } from '@/stores/useTenantStore'
import type { Dashboard, DashboardListResponse } from '@/types/dashboard'

function DashboardListingPage() {
  const [dashboards, setDashboards] = useState<Dashboard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showTenantSwitcher, setShowTenantSwitcher] = useState(false)

  const { selectedTenant, tenantToken, clearTenant } = useTenantStore()
  const router = useRouter()
  const params = useParams()
  const tenantSlug = params.tenant_slug as string

  // Fetch dashboards on mount (AC 2)
  useEffect(() => {
    async function fetchDashboards() {
      if (!selectedTenant || !tenantToken) {
        setError('No tenant selected. Please select a tenant first.')
        setLoading(false)
        return
      }

      // Verify tenant slug matches selected tenant
      if (selectedTenant.slug !== tenantSlug) {
        setError('Tenant mismatch. Redirecting to tenant selection...')
        setTimeout(() => router.push('/'), 2000)
        return
      }

      try {
        const response = await fetch(`/api/tenant/${selectedTenant.tenant_id}/dashboards`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${tenantToken}`,
            'Content-Type': 'application/json',
          },
        })

        // Handle 401 - invalid token (AC 10)
        if (response.status === 401) {
          setError('Session expired. Please log in again.')
          setLoading(false)
          return
        }

        // Handle 403 - access denied (AC 10)
        if (response.status === 403) {
          setError('Access denied. You do not have permission to view dashboards for this tenant.')
          setLoading(false)
          return
        }

        // Handle 404 - tenant not found (AC 10)
        if (response.status === 404) {
          setError('Tenant not found.')
          setLoading(false)
          return
        }

        if (!response.ok) {
          throw new Error('Failed to fetch dashboards')
        }

        const data: DashboardListResponse = await response.json()
        setDashboards(data.dashboards)
        setLoading(false)
      } catch (err) {
        console.error('Error fetching dashboards:', err)
        setError('Network error. Please check your connection and try again.')
        setLoading(false)
      }
    }

    fetchDashboards()
  }, [selectedTenant, tenantToken, tenantSlug, router])

  // Navigate to dashboard view (AC 7)
  const handleOpenDashboard = (dashboard: Dashboard) => {
    router.push(`/tenant/${tenantSlug}/dashboard/${dashboard.slug}`)
  }

  // Switch tenant (AC 11)
  const handleSwitchTenant = () => {
    clearTenant()
    router.push('/')
  }

  // Loading state (AC 9)
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboards...</p>
        </div>
      </div>
    )
  }

  // Error state (AC 10)
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="text-red-600 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Dashboards</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="space-y-3">
              <button
                onClick={() => window.location.reload()}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
              >
                Retry
              </button>
              <button
                onClick={handleSwitchTenant}
                className="w-full px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-md transition-colors"
              >
                Switch Tenant
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Main dashboard listing UI
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header with tenant info and switcher (AC 3, 11) */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            {/* Breadcrumb / Tenant Name (AC 3) */}
            <div>
              <div className="flex items-center space-x-2 text-sm text-gray-500 mb-1">
                <button
                  onClick={handleSwitchTenant}
                  className="hover:text-blue-600 transition-colors"
                >
                  Tenants
                </button>
                <span>/</span>
                <span className="text-gray-900 font-medium">{selectedTenant?.name}</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">
                Dashboards
              </h1>
            </div>

            {/* Tenant Switcher Dropdown (AC 11) */}
            <div className="relative">
              <button
                onClick={() => setShowTenantSwitcher(!showTenantSwitcher)}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                <span className="text-sm font-medium text-gray-700">
                  {selectedTenant?.name}
                </span>
                <svg
                  className={`w-4 h-4 text-gray-500 transition-transform ${showTenantSwitcher ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown Menu */}
              {showTenantSwitcher && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border border-gray-200 z-10">
                  <div className="py-1">
                    <div className="px-4 py-2 text-xs text-gray-500 font-semibold uppercase">
                      Current Tenant
                    </div>
                    <div className="px-4 py-2 bg-blue-50 border-l-4 border-blue-600">
                      <p className="text-sm font-medium text-gray-900">{selectedTenant?.name}</p>
                      <p className="text-xs text-gray-500">{selectedTenant?.slug}</p>
                    </div>
                    <div className="border-t border-gray-200 mt-1"></div>
                    <button
                      onClick={handleSwitchTenant}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      Switch Tenant
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Dashboard Grid (AC 4, 5, 6) */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Empty State (AC 8) */}
        {dashboards.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="w-20 h-20 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-700 mb-2">
              No Dashboards Available
            </h2>
            <p className="text-gray-500 mb-6">
              No dashboards available for this tenant. Please contact your administrator.
            </p>
            <button
              onClick={handleSwitchTenant}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
            >
              Switch Tenant
            </button>
          </div>
        ) : (
          <>
            {/* Dashboard Cards (AC 4, 5) */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {dashboards.map((dashboard) => {
                // Get icon or use default based on framework
                const defaultIcons = {
                  dash: '📊',
                  streamlit: '📈',
                  other: '📉',
                }
                const icon = dashboard.config_json?.icon || defaultIcons[dashboard.framework] || '📊'

                return (
                  <div
                    key={dashboard.dashboard_id}
                    className="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow overflow-hidden"
                  >
                    {/* Thumbnail / Icon Placeholder (AC 5) */}
                    <div className="bg-gradient-to-br from-blue-500 to-blue-600 h-40 flex items-center justify-center">
                      <div className="text-6xl">{icon}</div>
                    </div>

                    <div className="p-6">
                      {/* Dashboard Title (AC 5) */}
                      <h3 className="text-xl font-bold text-gray-900 mb-2">
                        {dashboard.name}
                      </h3>

                      {/* Dashboard Description (AC 5) */}
                      <p className="text-gray-600 text-sm mb-4 min-h-[3rem]">
                        {dashboard.description || 'No description available'}
                      </p>

                      {/* Metadata */}
                      <div className="mb-4 text-xs text-gray-500 space-y-1">
                        <p>Framework: <span className="font-semibold">{dashboard.framework}</span></p>
                        <p className="font-mono">Slug: {dashboard.slug}</p>
                      </div>

                      {/* Open Dashboard Button (AC 5, 7) */}
                      <button
                        onClick={() => handleOpenDashboard(dashboard)}
                        className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md transition-colors"
                      >
                        Open Dashboard
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Dashboard Count Info */}
            <div className="mt-8 text-center text-gray-500 text-sm">
              Showing {dashboards.length} dashboard{dashboards.length !== 1 ? 's' : ''} for {selectedTenant?.name}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// Wrap with AuthGuard to protect this route
export default function DashboardListingRoute() {
  return (
    <AuthGuard>
      <DashboardListingPage />
    </AuthGuard>
  )
}
