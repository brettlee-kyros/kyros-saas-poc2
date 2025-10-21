'use client'

import { useEffect, useState } from 'react'
import { Box, Typography, CircularProgress, Alert } from '@mui/material'
import AuthGuard from '@/components/auth/AuthGuard'
import { useAuth } from '@/contexts/AuthContext'
import DashboardLayout from '@/components/layout/DashboardLayout'
import type { UserInfoResponse, Tenant } from '@/types/tenant'

function TenantSelectionPage() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { userToken, setUser } = useAuth()

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

        // Store user info in AuthContext for Material-UI components
        setUser({
          user_id: data.user_id,
          email: data.email,
          tenants: data.tenants,
        })

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

  // Show welcome page with instruction to select tenant from dropdown
  return (
    <DashboardLayout>
      <Box sx={{ py: 4, px: 3, textAlign: 'center', mt: 8 }}>
        {loading ? (
          <>
            <CircularProgress size={60} sx={{ mb: 3 }} />
            <Typography variant="h6" color="text.secondary">
              Loading your tenants...
            </Typography>
          </>
        ) : (
          <>
            <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 600, color: '#1a1a1a', mb: 2 }}>
              Welcome to KYROS
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
              {tenants.length > 0
                ? 'Please select a tenant from the dropdown above to access your dashboards'
                : 'No tenants available. Please contact your administrator.'}
            </Typography>
            {error && (
              <Alert severity="error" sx={{ maxWidth: 600, mx: 'auto' }}>
                {error}
              </Alert>
            )}
          </>
        )}
      </Box>
    </DashboardLayout>
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
