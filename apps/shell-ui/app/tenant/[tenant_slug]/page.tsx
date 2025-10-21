'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Box, Typography, CircularProgress, Alert } from '@mui/material'
import AuthGuard from '@/components/auth/AuthGuard'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { useTenantStore } from '@/stores/useTenantStore'
import type { Dashboard, DashboardListResponse } from '@/types/dashboard'

function DashboardListingPage() {
  const [dashboards, setDashboards] = useState<Dashboard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { selectedTenant, tenantToken } = useTenantStore()
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

  // Wrapped in DashboardLayout for consistent UI
  return (
    <DashboardLayout>
      <Box sx={{ py: 4, px: 3 }}>
        {loading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 200px)' }}>
            <CircularProgress size={60} sx={{ mb: 3 }} />
            <Typography variant="h6" color="text.secondary">
              Loading dashboards...
            </Typography>
          </Box>
        ) : error ? (
          <Box sx={{ maxWidth: 600, mx: 'auto', mt: 8, textAlign: 'center' }}>
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Unable to load dashboards for this tenant.
            </Typography>
          </Box>
        ) : (
          <Box>
            <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
              Dashboards for {selectedTenant?.name}
            </Typography>

            {dashboards && dashboards.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <Typography variant="h6" color="text.secondary">
                  No dashboards available for this tenant.
                </Typography>
              </Box>
            ) : (
              <Typography variant="body1" color="text.secondary">
                {dashboards?.length || 0} dashboard(s) available
              </Typography>
            )}
          </Box>
        )}
      </Box>
    </DashboardLayout>
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
