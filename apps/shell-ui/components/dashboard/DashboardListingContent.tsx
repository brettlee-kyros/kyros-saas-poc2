'use client'

import { Box, Card, CardContent, CardActionArea, Typography, CircularProgress, Alert } from '@mui/material'
import { Dashboard } from '@mui/icons-material'
import { useRouter } from 'next/navigation'
import type { Dashboard as DashboardType } from '@/types/dashboard'

interface DashboardListingContentProps {
  dashboards: DashboardType[]
  tenantSlug: string
  loading?: boolean
  error?: string | null
}

export default function DashboardListingContent({
  dashboards,
  tenantSlug,
  loading = false,
  error = null
}: DashboardListingContentProps) {
  const router = useRouter()

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {error}
      </Alert>
    )
  }

  if (dashboards.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Dashboard sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h5" gutterBottom>
          No Dashboards Available
        </Typography>
        <Typography variant="body1" color="text.secondary">
          No dashboards are available for this tenant.
        </Typography>
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Dashboards
      </Typography>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 3 }}>
        {dashboards.map((dashboard) => (
          <Card key={dashboard.dashboard_id}>
            <CardActionArea
              onClick={() => router.push(`/tenant/${tenantSlug}/dashboard/${dashboard.slug}`)}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Dashboard sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                  <Typography variant="h6" component="div">
                    {dashboard.name}
                  </Typography>
                </Box>
                {dashboard.description && (
                  <Typography variant="body2" color="text.secondary">
                    {dashboard.description}
                  </Typography>
                )}
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {dashboard.framework || 'dash'}
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
      </Box>
    </Box>
  )
}
