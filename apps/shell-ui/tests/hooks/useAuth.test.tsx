import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useAuth, AuthProvider } from '@/contexts/AuthContext'
import { ReactNode } from 'react'

// Helper wrapper
function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}

describe('useAuth Hook', () => {
  beforeEach(() => {
    // Clear sessionStorage before each test
    sessionStorage.clear()
  })

  it('returns initial state with no authentication', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.userToken).toBeNull()
    expect(typeof result.current.login).toBe('function')
    expect(typeof result.current.logout).toBe('function')
  })

  it('login stores token in state', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.userToken).toBeNull()

    // Perform login
    act(() => {
      result.current.login('test-token-123')
    })

    // Token should be stored
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.userToken).toBe('test-token-123')
  })

  it('logout clears token from state', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    // Login first
    act(() => {
      result.current.login('test-token-123')
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.userToken).toBe('test-token-123')

    // Perform logout
    act(() => {
      result.current.logout()
    })

    // Token should be cleared
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.userToken).toBeNull()
  })

  it('isAuthenticated reflects token state', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    // Initially not authenticated
    expect(result.current.isAuthenticated).toBe(false)

    // After login
    act(() => {
      result.current.login('test-token')
    })

    expect(result.current.isAuthenticated).toBe(true)

    // After logout
    act(() => {
      result.current.logout()
    })

    expect(result.current.isAuthenticated).toBe(false)
  })

  it('getUserToken returns current token', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    // No token initially
    expect(result.current.userToken).toBeNull()

    // Login
    act(() => {
      result.current.login('my-test-token')
    })

    // Token should be returned
    const token = result.current.userToken
    expect(token).toBe('my-test-token')
  })

  it('persists token in sessionStorage', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    // Login
    act(() => {
      result.current.login('persistent-token')
    })

    // Token should be in sessionStorage
    const storedToken = sessionStorage.getItem('user_token')
    expect(storedToken).toBe('persistent-token')
    expect(storedToken).toBe(result.current.userToken)
  })

  it('clears sessionStorage on logout', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    // Login
    act(() => {
      result.current.login('temp-token')
    })

    expect(sessionStorage.getItem('user_token')).toBe('temp-token')

    // Logout
    act(() => {
      result.current.logout()
    })

    // sessionStorage should be cleared
    expect(sessionStorage.getItem('user_token')).toBeNull()
  })

  it('restores token from sessionStorage on mount', () => {
    // Set token in sessionStorage before mounting
    const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U'
    sessionStorage.setItem('user_token', validToken)

    // Mount hook
    const { result } = renderHook(() => useAuth(), { wrapper })

    // Should be authenticated with the token from sessionStorage
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.userToken).toBe(validToken)
  })

  it('rejects invalid token format from sessionStorage', () => {
    // Set an invalid token (not JWT format - should have 3 parts)
    sessionStorage.setItem('user_token', 'invalid-token')

    // Mount hook
    const { result } = renderHook(() => useAuth(), { wrapper })

    // Should NOT be authenticated
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.userToken).toBeNull()

    // sessionStorage should be cleared
    expect(sessionStorage.getItem('user_token')).toBeNull()
  })

  it('handles multiple login/logout cycles', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    // Cycle 1
    act(() => {
      result.current.login('token1')
    })
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.userToken).toBe('token1')

    act(() => {
      result.current.logout()
    })
    expect(result.current.isAuthenticated).toBe(false)

    // Cycle 2
    act(() => {
      result.current.login('token2')
    })
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.userToken).toBe('token2')

    act(() => {
      result.current.logout()
    })
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('throws error when used outside AuthProvider', () => {
    // Attempt to use hook without provider
    expect(() => {
      renderHook(() => useAuth())
    }).toThrow('useAuth must be used within an AuthProvider')
  })
})
