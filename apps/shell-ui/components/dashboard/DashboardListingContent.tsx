'use client'

import { useState, useRef, useEffect } from 'react'
import { Box, Card, CardContent, CardActionArea, Typography, CircularProgress, Alert, IconButton, Button } from '@mui/material'
import { Dashboard, Close, ArrowBack } from '@mui/icons-material'
import { useTenantStore } from '@/stores/useTenantStore'
import type { Dashboard as DashboardType } from '@/types/dashboard'

interface DashboardListingContentProps {
  dashboards: DashboardType[]
  tenantToken: string
  loading?: boolean
  error?: string | null
}

export default function DashboardListingContent({
  dashboards,
  tenantToken,
  loading = false,
  error = null
}: DashboardListingContentProps) {
  const { selectedDashboard: dashboardFromStore, setSelectedDashboard: setDashboardInStore } = useTenantStore()
  const [selectedDashboard, setSelectedDashboard] = useState<DashboardType | null>(null)
  const [iframeLoading, setIframeLoading] = useState(false)
  const [iframeError, setIframeError] = useState(false)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  // Check for dashboard selected from store (e.g., from NavigationDrawer)
  useEffect(() => {
    if (dashboardFromStore && !selectedDashboard) {
      setSelectedDashboard(dashboardFromStore)
      setIframeLoading(true)
      setIframeError(false)
    }
  }, [dashboardFromStore, selectedDashboard])

  const handleDashboardClick = (dashboard: DashboardType) => {
    setSelectedDashboard(dashboard)
    setIframeLoading(true)
    setIframeError(false)
  }

  const handleCloseDashboard = () => {
    setSelectedDashboard(null)
    setDashboardInStore(null)  // Clear from store as well
    setIframeLoading(false)
    setIframeError(false)
  }

  const handleIframeLoad = () => {
    setIframeLoading(false)
    setIframeError(false)
  }

  const handleIframeError = () => {
    setIframeLoading(false)
    setIframeError(true)
  }

  const handleRetry = () => {
    setIframeError(false)
    setIframeLoading(true)
    if (iframeRef.current) {
      const currentSrc = iframeRef.current.src
      iframeRef.current.src = ''
      setTimeout(() => {
        if (iframeRef.current) {
          iframeRef.current.src = currentSrc
        }
      }, 100)
    }
  }

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

  // If a dashboard is selected, show the iframe view
  if (selectedDashboard) {
    const iframeSrc = `/api/proxy/dash/${selectedDashboard.slug}/?token=${encodeURIComponent(tenantToken)}`

    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 200px)', minHeight: '600px' }}>
        {/* Header with dashboard title and close button */}
        <Box sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 2,
          pb: 2,
          borderBottom: '1px solid',
          borderColor: 'divider'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              onClick={handleCloseDashboard}
              size="small"
              sx={{ mr: 1 }}
            >
              <ArrowBack />
            </IconButton>
            <Dashboard sx={{ fontSize: 30, color: 'primary.main' }} />
            <Typography variant="h5" component="h2">
              {selectedDashboard.name}
            </Typography>
          </Box>
          <IconButton
            onClick={handleCloseDashboard}
            aria-label="close dashboard"
          >
            <Close />
          </IconButton>
        </Box>

        {/* Iframe container */}
        <Box sx={{ flex: 1, position: 'relative', overflow: 'hidden', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
          {/* Loading overlay */}
          {iframeLoading && !iframeError && (
            <Box sx={{
              position: 'absolute',
              inset: 0,
              bgcolor: 'background.default',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 10
            }}>
              <Box sx={{ textAlign: 'center' }}>
                <CircularProgress size={48} sx={{ mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  Loading dashboard...
                </Typography>
              </Box>
            </Box>
          )}

          {/* Error overlay */}
          {iframeError && (
            <Box sx={{
              position: 'absolute',
              inset: 0,
              bgcolor: 'background.default',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 10
            }}>
              <Box sx={{ textAlign: 'center', maxWidth: 400, p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Failed to Load Dashboard
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  The dashboard could not be loaded. This may be due to a network error or the dashboard service being unavailable.
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                  <Button variant="contained" onClick={handleRetry}>
                    Retry
                  </Button>
                  <Button variant="outlined" onClick={handleCloseDashboard}>
                    Back to Dashboards
                  </Button>
                </Box>
              </Box>
            </Box>
          )}

          {/* Embedded dashboard iframe */}
          <iframe
            ref={iframeRef}
            src={iframeSrc}
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
              display: 'block'
            }}
            title={selectedDashboard.name}
            onLoad={handleIframeLoad}
            onError={handleIframeError}
            allow="fullscreen"
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
          />
        </Box>
      </Box>
    )
  }

  // Default view: dashboard grid
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Dashboards
      </Typography>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 3 }}>
        {dashboards.map((dashboard) => (
          <Card key={dashboard.dashboard_id}>
            <CardActionArea
              onClick={() => handleDashboardClick(dashboard)}
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
