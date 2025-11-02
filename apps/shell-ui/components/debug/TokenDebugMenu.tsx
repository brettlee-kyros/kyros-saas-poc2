'use client'

import { useState } from 'react'
import {
  Box,
  IconButton,
  Drawer,
  Typography,
  Paper,
  Divider,
  Chip,
  Alert
} from '@mui/material'
import { BugReport, Close } from '@mui/icons-material'
import { useTenantStore } from '@/stores/useTenantStore'

interface DecodedToken {
  header: Record<string, unknown>
  payload: Record<string, unknown>
  signature: string
}

/**
 * TokenDebugMenu Component (PoC Only)
 *
 * Displays decoded JWT token claims for demonstration and debugging purposes.
 * Shows both user token and tenant token information.
 *
 * WARNING: This is for PoC demonstration only. Do not use in production.
 */
export default function TokenDebugMenu() {
  const [open, setOpen] = useState(false)
  const { tenantToken, selectedTenant } = useTenantStore()

  const toggleDrawer = () => {
    setOpen(!open)
  }

  const decodeJWT = (token: string): DecodedToken | null => {
    try {
      const parts = token.split('.')
      if (parts.length !== 3) {
        return null
      }

      const header = JSON.parse(atob(parts[0]))
      const payload = JSON.parse(atob(parts[1]))
      const signature = parts[2]

      return { header, payload, signature }
    } catch (error) {
      console.error('Failed to decode JWT:', error)
      return null
    }
  }

  const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  const renderTokenSection = (title: string, token: string | null) => {
    if (!token) {
      return (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          <Alert severity="info">No token available</Alert>
        </Box>
      )
    }

    const decoded = decodeJWT(token)
    if (!decoded) {
      return (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          <Alert severity="error">Failed to decode token</Alert>
        </Box>
      )
    }

    const isExpired = Boolean(decoded.payload.exp && typeof decoded.payload.exp === 'number' && decoded.payload.exp < Date.now() / 1000)

    return (
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Typography variant="h6">
            {title}
          </Typography>
          {isExpired && (
            <Chip label="EXPIRED" color="error" size="small" />
          )}
        </Box>

        {/* Header */}
        <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.100' }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Header
          </Typography>
          <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
            {Object.entries(decoded.header).map(([key, value]) => (
              <Box key={key} sx={{ mb: 0.5 }}>
                <strong>{key}:</strong> {JSON.stringify(value)}
              </Box>
            ))}
          </Box>
        </Paper>

        {/* Payload */}
        <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Payload (Claims)
          </Typography>
          <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
            {Object.entries(decoded.payload).map(([key, value]) => {
              let displayValue = JSON.stringify(value)

              // Format timestamps
              if ((key === 'iat' || key === 'exp') && typeof value === 'number') {
                displayValue = `${value} (${formatTimestamp(value)})`
              }

              return (
                <Box key={key} sx={{ mb: 0.5 }}>
                  <strong>{key}:</strong> {displayValue}
                </Box>
              )
            })}
          </Box>
        </Paper>

        {/* Signature */}
        <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.100' }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Signature
          </Typography>
          <Box sx={{
            fontFamily: 'monospace',
            fontSize: '0.75rem',
            wordBreak: 'break-all',
            color: 'text.secondary'
          }}>
            {decoded.signature}
          </Box>
        </Paper>
      </Box>
    )
  }

  return (
    <>
      {/* Debug Button (Fixed position) */}
      <IconButton
        onClick={toggleDrawer}
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          bgcolor: 'warning.main',
          color: 'white',
          '&:hover': {
            bgcolor: 'warning.dark',
          },
          zIndex: 1000,
          boxShadow: 3
        }}
        aria-label="Open debug menu"
      >
        <BugReport />
      </IconButton>

      {/* Debug Drawer */}
      <Drawer
        anchor="right"
        open={open}
        onClose={toggleDrawer}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', sm: '500px' },
            maxWidth: '100%'
          }
        }}
      >
        <Box sx={{ p: 3, height: '100%', overflow: 'auto' }}>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BugReport color="warning" />
              <Typography variant="h5">
                Debug: Token Inspector
              </Typography>
            </Box>
            <IconButton onClick={toggleDrawer}>
              <Close />
            </IconButton>
          </Box>

          <Alert severity="warning" sx={{ mb: 3 }}>
            <strong>PoC Only:</strong> This debug menu is for demonstration purposes to show token exchange.
          </Alert>

          <Divider sx={{ mb: 3 }} />

          {/* Selected Tenant Info */}
          {selectedTenant && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Selected Tenant
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'primary.50' }}>
                <Box sx={{ mb: 1 }}>
                  <strong>Name:</strong> {selectedTenant.name}
                </Box>
                <Box sx={{ mb: 1 }}>
                  <strong>ID:</strong> {selectedTenant.tenant_id}
                </Box>
                <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                  <strong>Slug:</strong> {selectedTenant.slug}
                </Box>
              </Paper>
            </Box>
          )}

          <Divider sx={{ my: 3 }} />

          {/* Tenant Token */}
          {renderTokenSection('Tenant-Scoped Token', tenantToken)}

          {/* Raw Token Display */}
          {tenantToken && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Raw Token
              </Typography>
              <Paper sx={{
                p: 2,
                bgcolor: 'grey.100',
                maxHeight: '150px',
                overflow: 'auto'
              }}>
                <Typography sx={{
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  wordBreak: 'break-all',
                  color: 'text.secondary'
                }}>
                  {tenantToken}
                </Typography>
              </Paper>
            </Box>
          )}
        </Box>
      </Drawer>
    </>
  )
}
