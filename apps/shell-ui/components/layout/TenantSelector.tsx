'use client'

import {
  FormControl,
  Select,
  MenuItem,
  Box,
  Typography,
  SelectChangeEvent,
  CircularProgress
} from '@mui/material'
import { Business } from '@mui/icons-material'
import { useTenantStore } from '@/stores/useTenantStore'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import type { TokenExchangeResponse } from '@/types/tenant'

export default function TenantSelector() {
  const { user, userToken } = useAuth()
  const { selectedTenant, setSelectedTenant, setTenantToken } = useTenantStore()
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  // Show for all authenticated users
  const tenants = user?.tenants || []
  if (tenants.length === 0) {
    return null  // Don't render if no tenants available
  }

  const handleTenantChange = async (event: SelectChangeEvent<string>) => {
    const tenantId = event.target.value
    const tenant = tenants.find(t => t.tenant_id === tenantId)

    console.log('[TenantSelector DEBUG] Selected tenant ID:', tenantId)
    console.log('[TenantSelector DEBUG] Found tenant:', tenant)
    console.log('[TenantSelector DEBUG] User token present:', !!userToken)

    if (!tenant || !userToken) {
      console.error('[TenantSelector DEBUG] Missing tenant or userToken, aborting')
      return
    }

    setLoading(true)
    try {
      const requestBody = { tenant_id: tenant.tenant_id }
      console.log('[TenantSelector DEBUG] Request body:', JSON.stringify(requestBody))

      // Exchange user token for tenant-scoped token
      const response = await fetch('/api/token/exchange', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })

      console.log('[TenantSelector DEBUG] Response status:', response.status)

      if (!response.ok) {
        throw new Error('Token exchange failed')
      }

      const data: TokenExchangeResponse = await response.json()

      // Update store with new tenant and token
      setSelectedTenant(tenant)
      setTenantToken(data.access_token)

      // Store tenant token in sessionStorage
      sessionStorage.setItem('tenant_token', data.access_token)

      // Navigate to tenant dashboard listing
      router.push(`/tenant/${tenant.slug}`)
    } catch (error) {
      console.error('Failed to switch tenant:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ minWidth: 200, mr: 2 }}>
      <FormControl fullWidth size="small" disabled={loading}>
        <Select
          value={selectedTenant?.tenant_id || ''}
          onChange={handleTenantChange}
          displayEmpty
          sx={{
            bgcolor: 'rgba(0, 0, 0, 0.04)',
            '& .MuiOutlinedInput-notchedOutline': {
              border: 'none',
            },
          }}
          startAdornment={
            loading ? (
              <CircularProgress size={16} sx={{ mr: 1 }} />
            ) : (
              <Business fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
            )
          }
        >
          <MenuItem value="" disabled>
            <Typography variant="body2" color="text.secondary">
              Select a tenant...
            </Typography>
          </MenuItem>
          {tenants.map((tenant) => (
            <MenuItem key={tenant.tenant_id} value={tenant.tenant_id}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {tenant.name}
                </Typography>
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  )
}
