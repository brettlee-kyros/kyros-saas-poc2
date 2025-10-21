'use client'

import {
  Box,
  Card,
  CardContent,
  CardActionArea,
  Typography,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material'
import { Business } from '@mui/icons-material'
import { useAuth } from '@/contexts/AuthContext'
import type { Tenant } from '@/types/tenant'

interface TenantSelectionContentProps {
  tenants: Tenant[]
  loading?: boolean
  exchanging?: boolean
  error?: string | null
  selectedTenantId?: string | null
  onTenantSelect: (tenant: Tenant) => Promise<void>
  onLogout: () => void
}

export default function TenantSelectionContent({
  tenants,
  loading = false,
  exchanging = false,
  error = null,
  selectedTenantId = null,
  onTenantSelect,
  onLogout
}: TenantSelectionContentProps) {
  const { user } = useAuth()

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 200px)' }}>
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          Loading your tenants...
        </Typography>
      </Box>
    )
  }

  // Get user's first name from email or full name
  const getUserFirstName = () => {
    if (user?.name) {
      return user.name.split(' ')[0]
    }
    if (user?.email) {
      const emailName = user.email.split('@')[0]
      return emailName.split('.').map(part => part.charAt(0).toUpperCase() + part.slice(1)).join(' ')
    }
    return 'User'
  }

  return (
    <Box sx={{ py: 4, px: 3 }}>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 600, color: '#1a1a1a' }}>
          Welcome, {getUserFirstName()}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Please select a tenant to continue
        </Typography>
      </Box>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Tenant Cards */}
      {tenants.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Business sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            No Tenants Available
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            You don&apos;t have access to any tenants. Please contact your administrator.
          </Typography>
          <Button variant="contained" color="primary" onClick={onLogout}>
            Logout
          </Button>
        </Box>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 3, maxWidth: 1200 }}>
          {tenants.map((tenant) => (
            <Card
              key={tenant.tenant_id}
              elevation={2}
              sx={{
                height: '100%',
                opacity: exchanging && selectedTenantId !== tenant.tenant_id ? 0.5 : 1,
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: exchanging ? 'none' : 'translateY(-4px)',
                  boxShadow: exchanging ? 2 : 6,
                },
              }}
            >
              <CardActionArea
                onClick={() => !exchanging && onTenantSelect(tenant)}
                disabled={exchanging}
                sx={{ height: '100%' }}
              >
                <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                    <Box
                      sx={{
                        width: 56,
                        height: 56,
                        borderRadius: 2,
                        bgcolor: 'primary.light',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mr: 2,
                        flexShrink: 0,
                      }}
                    >
                      <Business sx={{ fontSize: 32, color: 'primary.main' }} />
                    </Box>
                    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                      <Typography variant="h6" component="div" sx={{ fontWeight: 600, mb: 0.5 }}>
                        {tenant.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {tenant.slug}
                      </Typography>
                    </Box>
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3, flexGrow: 1 }}>
                    {tenant.config_json?.description || 'No description available'}
                  </Typography>

                  <Button
                    variant="contained"
                    color="primary"
                    fullWidth
                    size="large"
                    disabled={exchanging}
                    startIcon={exchanging && selectedTenantId === tenant.tenant_id ? <CircularProgress size={20} color="inherit" /> : undefined}
                    sx={{
                      py: 1.5,
                      textTransform: 'none',
                      fontWeight: 500,
                    }}
                  >
                    {exchanging && selectedTenantId === tenant.tenant_id ? 'Selecting...' : 'Select'}
                  </Button>
                </CardContent>
              </CardActionArea>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  )
}
