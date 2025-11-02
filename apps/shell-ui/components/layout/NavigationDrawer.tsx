'use client'

import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Box,
  CircularProgress,
  Typography,
  Divider
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  ShowChart,
  Assessment,
  TrendingUp
} from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useTenantStore } from '@/stores/useTenantStore'
import type { Dashboard } from '@/types/dashboard'

const DRAWER_WIDTH = 240

const iconMap: Record<string, JSX.Element> = {
  'customer-lifetime-value': <TrendingUp />,
  'risk-analysis': <Assessment />,
  'revenue-forecast': <ShowChart />,
}

interface NavigationDrawerProps {
  open?: boolean
  onClose?: () => void
  variant?: 'permanent' | 'temporary'
}

export default function NavigationDrawer({
  open = true,
  onClose,
  variant = 'permanent'
}: NavigationDrawerProps) {
  const [dashboards, setDashboards] = useState<Dashboard[]>([])
  const [loading, setLoading] = useState(false)
  const { selectedTenant, tenantToken, selectedDashboard, setSelectedDashboard } = useTenantStore()
  const router = useRouter()
  const pathname = usePathname()

  // Fetch dashboards when tenant changes
  useEffect(() => {
    if (!selectedTenant || !tenantToken) {
      setDashboards([])
      return
    }

    fetchDashboards()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTenant, tenantToken])

  const fetchDashboards = async () => {
    if (!selectedTenant || !tenantToken) return

    console.log('[NavigationDrawer DEBUG] Fetching dashboards for tenant:', selectedTenant.tenant_id)
    setLoading(true)
    try {
      const response = await fetch(`/api/tenant/${selectedTenant.tenant_id}/dashboards`, {
        headers: {
          'Authorization': `Bearer ${tenantToken}`,
        },
      })

      console.log('[NavigationDrawer DEBUG] Dashboard fetch response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('[NavigationDrawer DEBUG] Dashboards received:', data.dashboards?.length || 0)
        setDashboards(data.dashboards || [])
      } else {
        const errorText = await response.text()
        console.error('[NavigationDrawer DEBUG] Dashboard fetch failed:', response.status, errorText)
      }
    } catch (error) {
      console.error('[NavigationDrawer DEBUG] Failed to fetch dashboards:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDashboardClick = (dashboard: Dashboard) => {
    if (!selectedTenant) return

    // Set the selected dashboard in the store
    setSelectedDashboard(dashboard)

    // Navigate to tenant page if not already there
    const tenantPagePath = `/tenant/${selectedTenant.slug}`
    if (pathname !== tenantPagePath) {
      router.push(tenantPagePath)
    }

    if (onClose) onClose()  // Close drawer on mobile
  }

  const isActive = (dashboardSlug: string) => {
    // Check if this dashboard is selected in the store and we're on the tenant page
    return selectedDashboard?.slug === dashboardSlug && pathname?.includes(`/tenant/${selectedTenant?.slug}`)
  }

  const drawerContent = (
    <>
      <Toolbar />  {/* Spacer for fixed AppBar */}
      <Box sx={{ overflow: 'auto', p: 2 }}>
        <Typography variant="overline" color="text.secondary" sx={{ px: 2, fontWeight: 600 }}>
          Dashboards
        </Typography>
        <Divider sx={{ my: 1 }} />

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={32} />
          </Box>
        ) : dashboards.length === 0 ? (
          <Box sx={{ px: 2, py: 4 }}>
            <Typography variant="body2" color="text.secondary" align="center">
              No dashboards available
            </Typography>
          </Box>
        ) : (
          <List>
            {dashboards.map((dashboard) => (
              <ListItem key={dashboard.dashboard_id} disablePadding>
                <ListItemButton
                  onClick={() => handleDashboardClick(dashboard)}
                  selected={isActive(dashboard.slug)}
                  sx={{
                    borderRadius: 1,
                    mb: 0.5,
                    '&.Mui-selected': {
                      bgcolor: 'primary.main',
                      color: 'primary.contrastText',
                      '&:hover': {
                        bgcolor: 'primary.dark',
                      },
                      '& .MuiListItemIcon-root': {
                        color: 'primary.contrastText',
                      },
                    },
                    '&:hover': {
                      bgcolor: 'rgba(25, 118, 210, 0.08)',
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    {iconMap[dashboard.slug] || <DashboardIcon />}
                  </ListItemIcon>
                  <ListItemText
                    primary={dashboard.name}
                    primaryTypographyProps={{
                      variant: 'body2',
                      fontWeight: 500,
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Box>
    </>
  )

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
        },
      }}
    >
      {drawerContent}
    </Drawer>
  )
}
