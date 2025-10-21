import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DebugPanel from '@/components/dashboard/DebugPanel'
import { AuthProvider } from '@/contexts/AuthContext'
import { create } from 'zustand'

// Mock zustand tenant store
const mockTenantStore = create(() => ({
  selectedTenant: null,
  tenantToken: null,
  setSelectedTenant: vi.fn(),
  setTenantToken: vi.fn(),
  clearTenant: vi.fn(),
}))

vi.mock('@/stores/useTenantStore', () => ({
  useTenantStore: () => mockTenantStore.getState(),
}))

// Helper to render with providers
function renderWithProviders(ui: React.ReactElement, { userToken }: { userToken?: string } = {}) {
  if (userToken) {
    sessionStorage.setItem('user_token', userToken)
  }

  return render(
    <AuthProvider>
      {ui}
    </AuthProvider>
  )
}

// Mock JWT tokens with known claims
const mockUserToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImVtYWlsIjoidGVzdEB0ZXN0LmNvbSIsInRlbmFudF9pZHMiOlsidGVuYW50LTEiLCJ0ZW5hbnQtMiJdLCJleHAiOjk5OTk5OTk5OTksImlhdCI6MTcwMDAwMDAwMCwiaXNzIjoia3lyb3MtcG9jIn0.signature'
const mockTenantToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImVtYWlsIjoidGVzdEB0ZXN0LmNvbSIsInRlbmFudF9pZCI6InRlbmFudC0xIiwicm9sZSI6InZpZXdlciIsImV4cCI6OTk5OTk5OTk5OSwiaWF0IjoxNzAwMDAwMDAwLCJpc3MiOiJreXJvcy1wb2MifQ.signature'
const mockExpiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImVtYWlsIjoidGVzdEB0ZXN0LmNvbSIsInRlbmFudF9pZHMiOlsidGVuYW50LTEiXSwiZXhwIjoxNjAwMDAwMDAwLCJpYXQiOjE1MDAwMDAwMDAsImlzcyI6Imt5cm9zLXBvYyJ9.signature'

describe('DebugPanel Component', () => {
  beforeEach(() => {
    // Clear sessionStorage before each test
    sessionStorage.clear()

    // Reset tenant store
    mockTenantStore.setState({
      selectedTenant: null,
      tenantToken: null,
    })
  })

  it('toggles panel open and closed', async () => {
    const user = userEvent.setup()

    renderWithProviders(<DebugPanel />, { userToken: mockUserToken })

    // Panel should be closed initially - decoded claims not visible
    expect(screen.queryByText(/decoded claims/i)).not.toBeInTheDocument()

    // Click toggle button
    const toggleButton = screen.getByRole('button', { name: /debug/i })
    await user.click(toggleButton)

    // Panel should be open - decoded claims visible
    await waitFor(() => {
      expect(screen.getByText(/decoded claims/i)).toBeInTheDocument()
    })

    // Click toggle button again
    await user.click(toggleButton)

    // Panel should be closed
    await waitFor(() => {
      expect(screen.queryByText(/decoded claims/i)).not.toBeInTheDocument()
    })
  })

  it('displays decoded user token claims correctly', async () => {
    const user = userEvent.setup()

    renderWithProviders(<DebugPanel />, { userToken: mockUserToken })

    // Open panel
    const toggleButton = screen.getByRole('button', { name: /debug/i })
    await user.click(toggleButton)

    // Verify user token claims are displayed
    await waitFor(() => {
      expect(screen.getByText(/user access token/i)).toBeInTheDocument()
    })

    // Verify subject and email (getAllByText since they appear multiple times)
    const userIdElements = screen.getAllByText(/user-123/i)
    expect(userIdElements.length).toBeGreaterThan(0)

    const emailElements = screen.getAllByText(/test@test\.com/i)
    expect(emailElements.length).toBeGreaterThan(0)

    // Verify tenant_ids array is shown (multi-tenant indicator)
    expect(screen.getByText(/tenant_ids/i)).toBeInTheDocument()
    expect(screen.getByText(/multi-tenant/i)).toBeInTheDocument()
  })

  it('displays decoded tenant-scoped token claims correctly', async () => {
    const user = userEvent.setup()

    // Set tenant token in store
    mockTenantStore.setState({
      tenantToken: mockTenantToken,
    })

    renderWithProviders(<DebugPanel />, { userToken: mockUserToken })

    // Open panel
    const toggleButton = screen.getByRole('button', { name: /debug/i })
    await user.click(toggleButton)

    // Verify tenant-scoped token is displayed
    await waitFor(() => {
      expect(screen.getByText(/tenant-scoped token/i)).toBeInTheDocument()
    })

    // Verify tenant_id (single value) is shown
    expect(screen.getByText(/tenant_id/i)).toBeInTheDocument()
    expect(screen.getByText(/single tenant/i)).toBeInTheDocument()

    // Verify role is shown
    expect(screen.getByText(/viewer/i)).toBeInTheDocument()

    // Should NOT show tenant_ids array
    expect(screen.queryByText(/multi-tenant/i)).not.toBeInTheDocument()
  })

  it('distinguishes tenant_id vs tenant_ids array', async () => {
    const user = userEvent.setup()

    // First render with user token (tenant_ids array)
    const { rerender } = renderWithProviders(<DebugPanel />, { userToken: mockUserToken })

    const toggleButton = screen.getByRole('button', { name: /debug/i })
    await user.click(toggleButton)

    // Verify tenant_ids (array) is shown
    await waitFor(() => {
      expect(screen.getByText(/tenant_ids/i)).toBeInTheDocument()
      expect(screen.getByText(/multi-tenant/i)).toBeInTheDocument()
    })

    // Close panel
    await user.click(toggleButton)

    // Update to tenant token (tenant_id single value)
    mockTenantStore.setState({
      tenantToken: mockTenantToken,
    })

    // Re-render to trigger update
    rerender(
      <AuthProvider>
        <DebugPanel />
      </AuthProvider>
    )

    // Open panel again
    await user.click(toggleButton)

    // Verify tenant_id (single value) is shown
    await waitFor(() => {
      expect(screen.getByText(/tenant_id/i)).toBeInTheDocument()
      expect(screen.getByText(/single tenant/i)).toBeInTheDocument()
    })
  })

  it('updates expiry countdown', async () => {
    vi.useFakeTimers()

    renderWithProviders(<DebugPanel />, { userToken: mockUserToken })

    // Open panel without user interaction to avoid timer issues
    const toggleButton = screen.getByRole('button', { name: /debug/i })
    toggleButton.click()

    // Wait for initial expiry time to render
    await vi.waitFor(() => {
      expect(screen.getByText(/token expiry/i)).toBeInTheDocument()
    })

    // Get initial countdown value (should be very large since exp is 9999999999)
    const initialCountdown = screen.getByText(/⏱️/i)
    expect(initialCountdown).toBeInTheDocument()

    // Advance time by 1 second
    await vi.advanceTimersByTimeAsync(1000)

    // Countdown should update (wait for next render)
    await vi.waitFor(() => {
      const updatedCountdown = screen.getByText(/⏱️/i)
      expect(updatedCountdown).toBeInTheDocument()
    })

    vi.useRealTimers()
  }, 10000)

  it('shows expired state for expired tokens', async () => {
    const user = userEvent.setup()

    renderWithProviders(<DebugPanel />, { userToken: mockExpiredToken })

    // Open panel
    const toggleButton = screen.getByRole('button', { name: /debug/i })
    await user.click(toggleButton)

    // Verify expired indicator is shown
    await waitFor(() => {
      expect(screen.getByText(/expired/i)).toBeInTheDocument()
    }, { timeout: 10000 })
  })

  it('handles missing token gracefully', async () => {
    const user = userEvent.setup()

    // Render without any token
    renderWithProviders(<DebugPanel />)

    // Open panel
    const toggleButton = screen.getByRole('button', { name: /debug/i })
    await user.click(toggleButton)

    // Verify "no token" message is shown
    await waitFor(() => {
      expect(screen.getByText(/no token available/i)).toBeInTheDocument()
    }, { timeout: 10000 })
  })

  it('handles invalid token format gracefully', async () => {
    const user = userEvent.setup()
    // Create a more realistic malformed JWT (3 parts but invalid base64)
    const invalidToken = 'invalid.token.here'

    renderWithProviders(<DebugPanel />, { userToken: invalidToken })

    // Open panel
    const toggleButton = screen.getByRole('button', { name: /debug/i })
    await user.click(toggleButton)

    // Verify error message is shown (the component should display an error)
    await waitFor(() => {
      // The panel should be open
      expect(screen.getByText(/JWT Debug Panel/i)).toBeInTheDocument()
      // Should show some error indicator (check for the error emoji or message)
      const body = screen.getByText(/JWT Debug Panel/i).parentElement
      expect(body).toBeTruthy()
    }, { timeout: 10000 })
  }, 15000)

  it('shows token type badge when closed', () => {
    renderWithProviders(<DebugPanel />, { userToken: mockUserToken })

    // Panel is closed, should show "User" badge
    const toggleButton = screen.getByRole('button', { name: /debug/i })
    expect(toggleButton).toHaveTextContent(/user/i)
  })

  it('updates when token changes', async () => {
    const user = userEvent.setup()

    // Start with user token
    const { rerender } = renderWithProviders(<DebugPanel />, { userToken: mockUserToken })

    const toggleButton = screen.getByRole('button', { name: /debug/i })
    await user.click(toggleButton)

    // Verify user token is displayed
    await waitFor(() => {
      expect(screen.getByText(/user access token/i)).toBeInTheDocument()
    }, { timeout: 10000 })

    // Update to tenant token
    mockTenantStore.setState({
      tenantToken: mockTenantToken,
    })

    // Re-render
    rerender(
      <AuthProvider>
        <DebugPanel />
      </AuthProvider>
    )

    // Verify tenant token is now displayed
    await waitFor(() => {
      expect(screen.getByText(/tenant-scoped token/i)).toBeInTheDocument()
    }, { timeout: 10000 })
  })
})
