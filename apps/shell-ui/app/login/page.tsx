'use client'

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Box, TextField, Button, Typography, Container, Paper, Alert } from '@mui/material'
import { Login as LoginIcon, Lock as LockIcon } from '@mui/icons-material'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Mock user emails
  const mockEmails = [
    { email: 'analyst@acme.com', label: 'analyst@acme.com (Multi-tenant user)' },
    { email: 'admin@acme.com', label: 'admin@acme.com (Admin user)' },
    { email: 'viewer@beta.com', label: 'viewer@beta.com (Single-tenant user)' }
  ]

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)

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
      const response = await fetch('/api/auth/mock-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      if (response.status === 404) {
        setError('User not found. Try one of the suggested emails.')
        setIsLoading(false)
        return
      }

      if (!response.ok) {
        setError('Authentication failed. Please try again.')
        setIsLoading(false)
        return
      }

      const data = await response.json()
      login(data.access_token)
      router.push('/')
    } catch (err) {
      console.error('Login error:', err)
      setError('Network error. Please check your connection and retry.')
      setIsLoading(false)
    }
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#f5f7fa',
      }}
    >
      <Container maxWidth="sm">
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          {/* Logo Icon */}
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              bgcolor: 'primary.main',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto',
              mb: 3,
            }}
          >
            <LoginIcon sx={{ fontSize: 40, color: 'white' }} />
          </Box>

          {/* Heading */}
          <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 600, color: '#1a1a1a' }}>
            Welcome to KYROS
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Sign in to access your analytics dashboard
          </Typography>
        </Box>

        <Paper elevation={0} sx={{ p: 4, borderRadius: 2, border: '1px solid #e0e0e0' }}>
          <form onSubmit={handleSubmit}>
            {/* Email Input */}
            <Typography variant="body2" sx={{ mb: 1, fontWeight: 500, color: '#555' }}>
              Email Address
            </Typography>
            <TextField
              fullWidth
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@acme.com"
              disabled={isLoading}
              sx={{ mb: 2 }}
              variant="outlined"
            />

            {/* Demo Environment Info Box */}
            <Box
              sx={{
                bgcolor: '#e3f2fd',
                border: '1px solid #90caf9',
                borderRadius: 1,
                p: 2,
                mb: 3,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
                <LockIcon sx={{ fontSize: 20, color: 'primary.main', mr: 1, mt: 0.2 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  Demo Environment
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ mb: 1, color: '#1976d2' }}>
                This is a mock authentication system. Use any of the pre-configured emails:
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                {mockEmails.map((user) => (
                  <li key={user.email}>
                    <Typography
                      variant="body2"
                      sx={{
                        color: 'primary.main',
                        cursor: 'pointer',
                        '&:hover': { textDecoration: 'underline' },
                      }}
                      onClick={() => setEmail(user.email)}
                    >
                      {user.label}
                    </Typography>
                  </li>
                ))}
              </Box>
            </Box>

            {/* Error Message */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={isLoading}
              startIcon={<LoginIcon />}
              sx={{
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 500,
                textTransform: 'none',
              }}
            >
              {isLoading ? 'Signing in...' : 'Sign in with Azure AD B2C'}
            </Button>
          </form>

          {/* Footer */}
          <Typography
            variant="caption"
            sx={{ display: 'block', textAlign: 'center', mt: 3, color: 'text.secondary' }}
          >
            © 2025 KYROS Analytics. All rights reserved.
          </Typography>
        </Paper>
      </Container>
    </Box>
  )
}
