'use client'

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import type { LoginRequest, LoginResponse, ErrorResponse } from '@/types/auth'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)

  // Mock user emails from Story 3.1 AC 4
  const mockEmails = [
    'analyst@acme.com',
    'admin@acme.com',
    'viewer@beta.com'
  ]

  // Client-side email validation (AC 9)
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)

    // Client-side validation (AC 9)
    if (!email.trim()) {
      setError('Email is required')
      return
    }

    if (!validateEmail(email)) {
      setError('Invalid email format')
      return
    }

    setIsLoading(true)

    try {
      // Call POST /api/auth/mock-login (AC 5)
      const response = await fetch('/api/auth/mock-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email } as LoginRequest),
      })

      // Handle 404 - user not found (AC 7)
      if (response.status === 404) {
        setError('User not found. Try one of the suggested emails.')
        setIsLoading(false)
        return
      }

      // Handle 401 - invalid credentials (AC 7)
      if (response.status === 401) {
        setError('Authentication failed. Please check your email.')
        setIsLoading(false)
        return
      }

      // Handle other errors (AC 8)
      if (!response.ok) {
        const errorData: ErrorResponse = await response.json()
        setError(errorData.detail?.error?.message || 'Authentication failed')
        setIsLoading(false)
        return
      }

      // Success - store token using auth context and redirect (AC 6)
      const data: LoginResponse = await response.json()

      // Use auth context login() function (Story 3.2)
      login(data.access_token)

      // Redirect to home page (AC 6)
      router.push('/')
    } catch (err) {
      // Network error handling (AC 8)
      console.error('Login error:', err)
      setError('Network error. Please check your connection and retry.')
      setIsLoading(false)
    }
  }

  const handleEmailClick = (selectedEmail: string) => {
    setEmail(selectedEmail)
    setShowSuggestions(false)
    setError(null)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 px-4">
      <div className="w-full max-w-md">
        {/* Login Card - Centered layout (AC 2, 11) */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Welcome to Kyros
            </h1>
            <p className="text-gray-600">
              Multi-Tenant Dashboard PoC
            </p>
          </div>

          {/* Login Form (AC 1) */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Input Field (AC 2, 3) */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onFocus={() => setShowSuggestions(true)}
                placeholder="analyst@acme.com"
                disabled={isLoading}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
                required
              />

              {/* Mock Email Suggestions (AC 4) */}
              {showSuggestions && !isLoading && (
                <div className="mt-2 bg-blue-50 border border-blue-200 rounded-md p-3">
                  <p className="text-xs text-blue-800 font-semibold mb-2">
                    Mock Users (for PoC):
                  </p>
                  <div className="space-y-1">
                    {mockEmails.map((mockEmail) => (
                      <button
                        key={mockEmail}
                        type="button"
                        onClick={() => handleEmailClick(mockEmail)}
                        className="block w-full text-left px-3 py-2 text-sm text-blue-700 hover:bg-blue-100 rounded transition-colors"
                      >
                        {mockEmail}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Error Message (AC 7, 8) */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">
                  <span className="font-semibold">Error:</span> {error}
                </p>
              </div>
            )}

            {/* Submit Button (AC 2, 3) */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 text-white font-semibold py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Authenticating...
                </span>
              ) : (
                'Log In'
              )}
            </button>
          </form>

          {/* PoC Notice */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              This is a PoC demonstration. Use one of the mock emails above to log in.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
