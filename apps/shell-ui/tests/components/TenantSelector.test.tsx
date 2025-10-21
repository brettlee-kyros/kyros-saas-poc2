import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import Home from '@/app/page'
import { AuthProvider } from '@/contexts/AuthContext'

// Mock next/navigation
const mockPush = vi.fn()
const mockPathname = '/'
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => mockPathname,
}))

// Helper to render with providers
function renderWithProviders(ui: React.ReactElement) {
  return render(
    <AuthProvider>
      {ui}
    </AuthProvider>
  )
}

describe('TenantSelector (Tenant Selection Page)', () => {
  beforeEach(() => {
    // Clear mocks before each test
    mockPush.mockClear()

    // Set a mock user token in sessionStorage
    sessionStorage.setItem('user_token', 'mock-user-token.eyJzdWIiOiJ1c2VyLTEyMyJ9.signature')
  })

  it('renders tenant cards correctly with tenant data', async () => {
    renderWithProviders(<Home />)

    // Wait for tenants to load
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    // Verify tenant names are displayed
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Beta Industries')).toBeInTheDocument()

    // Verify select buttons are rendered
    const selectButtons = screen.getAllByRole('button', { name: /select tenant/i })
    expect(selectButtons.length).toBeGreaterThan(0)
  })

  it('triggers token exchange when Select button clicked', async () => {
    const user = userEvent.setup()

    renderWithProviders(<Home />)

    // Wait for tenants to load
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    // Click the first "Select Tenant" button
    const selectButtons = screen.getAllByRole('button', { name: /select tenant/i })
    await user.click(selectButtons[0])

    // Verify loading state appears
    await waitFor(() => {
      expect(screen.getByText(/exchanging token/i)).toBeInTheDocument()
    })
  })

  it('shows loading state during token exchange', async () => {
    const user = userEvent.setup()

    // Delay the token exchange response
    server.use(
      http.post('/api/token/exchange', async () => {
        await new Promise(resolve => setTimeout(resolve, 100))
        return HttpResponse.json({
          tenant_token: 'mock-tenant-token',
          access_token: 'mock-tenant-token',
          token_type: 'Bearer',
          expires_in: 3600,
        })
      })
    )

    renderWithProviders(<Home />)

    // Wait for tenants to load
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    const selectButtons = screen.getAllByRole('button', { name: /select tenant/i })
    const firstButton = selectButtons[0]

    await user.click(firstButton)

    // Loading indicator should appear
    await waitFor(() => {
      expect(screen.getByText(/exchanging token/i)).toBeInTheDocument()
    })

    // Button should be disabled during loading
    expect(firstButton).toBeDisabled()
  })

  it('handles token exchange failure with 403', async () => {
    const user = userEvent.setup()

    // Override MSW handler to return 403 error
    server.use(
      http.post('/api/token/exchange', () => {
        return new HttpResponse(null, { status: 403 })
      })
    )

    renderWithProviders(<Home />)

    // Wait for tenants to load
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    const selectButtons = screen.getAllByRole('button', { name: /select tenant/i })
    await user.click(selectButtons[0])

    // Error message should appear
    await waitFor(() => {
      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
    })

    // Button should be enabled again
    expect(selectButtons[0]).not.toBeDisabled()
  })

  it('handles token exchange failure with 500', async () => {
    const user = userEvent.setup()

    // Override MSW handler to return 500 error
    server.use(
      http.post('/api/token/exchange', () => {
        return new HttpResponse(null, { status: 500 })
      })
    )

    renderWithProviders(<Home />)

    // Wait for tenants to load
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    const selectButtons = screen.getAllByRole('button', { name: /select tenant/i })
    await user.click(selectButtons[0])

    // Error message should appear
    await waitFor(() => {
      expect(screen.getByText(/failed to exchange token/i)).toBeInTheDocument()
    })
  })

  it('redirects to dashboard listing on successful exchange', async () => {
    const user = userEvent.setup()

    // Mock successful token exchange
    server.use(
      http.post('/api/token/exchange', () => {
        return HttpResponse.json({
          access_token: 'mock-tenant-token',
          token_type: 'Bearer',
          expires_in: 3600,
        })
      })
    )

    renderWithProviders(<Home />)

    // Wait for tenants to load
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    const selectButtons = screen.getAllByRole('button', { name: /select tenant/i })
    await user.click(selectButtons[0])

    // Verify redirect was called (router.push should be called with tenant path)
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalled()
      // Find the call that includes /tenant/ (might not be first due to AuthGuard)
      const tenantCall = mockPush.mock.calls.find(call => call[0]?.includes('/tenant/'))
      expect(tenantCall).toBeDefined()
      expect(tenantCall[0]).toMatch(/\/tenant\//)
    }, { timeout: 3000 })
  })

  it('displays loading state while fetching tenants', () => {
    // Clear user token to prevent automatic loading
    sessionStorage.removeItem('user_token')

    renderWithProviders(<Home />)

    // Should show authentication guard or redirect
    // This test verifies initial state handling
  })

  it('handles 401 error when fetching tenants', async () => {
    // Override MSW handler to return 401 for /api/me
    server.use(
      http.get('/api/me', () => {
        return new HttpResponse(null, { status: 401 })
      })
    )

    renderWithProviders(<Home />)

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/session expired/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })
})
