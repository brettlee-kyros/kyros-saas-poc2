'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import type { Tenant } from '@/types/tenant'

// User interface
export interface User {
  user_id?: string
  email: string
  name?: string
  tenants?: Tenant[]
}

// AuthContextType interface (AC 1, AC 10)
export interface AuthContextType {
  isAuthenticated: boolean
  userToken: string | null
  user: User | null
  login: (token: string) => void
  logout: () => void
  setUser: (user: User | null) => void
}

// Create AuthContext with default undefined value
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// AuthProvider component (AC 1, AC 3, AC 4, AC 5)
interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [userToken, setUserToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)

  // Token persistence check on mount (AC 9)
  useEffect(() => {
    // Check sessionStorage for existing token
    const storedToken = sessionStorage.getItem('user_token')

    if (storedToken) {
      // TODO: In future, validate token by calling /api/me
      // For now, accept any token from sessionStorage
      try {
        // Basic validation: check if it looks like a JWT (3 parts separated by dots)
        const parts = storedToken.split('.')
        if (parts.length === 3) {
          setUserToken(storedToken)
          setIsAuthenticated(true)
        } else {
          // Invalid token format, clear it
          sessionStorage.removeItem('user_token')
        }
      } catch (error) {
        console.error('Error validating stored token:', error)
        sessionStorage.removeItem('user_token')
      }
    }
  }, [])

  // login() function (AC 4)
  const login = (token: string) => {
    setUserToken(token)
    setIsAuthenticated(true)
    // Persist to sessionStorage
    sessionStorage.setItem('user_token', token)
  }

  // logout() function (AC 5)
  const logout = () => {
    setUserToken(null)
    setUser(null)
    setIsAuthenticated(false)
    // Clear from sessionStorage
    sessionStorage.removeItem('user_token')
    sessionStorage.removeItem('tenant_token')
  }

  const value: AuthContextType = {
    isAuthenticated,
    userToken,
    user,
    login,
    logout,
    setUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// useAuth hook (AC 6)
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)

  // Error handling if used outside provider (AC 6)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}
