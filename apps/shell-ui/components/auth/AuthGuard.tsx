'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

interface AuthGuardProps {
  children: React.ReactNode
}

/**
 * AuthGuard component that protects routes by redirecting unauthenticated users to /login
 *
 * Usage:
 * Wrap any page or component that requires authentication:
 *
 * <AuthGuard>
 *   <ProtectedContent />
 * </AuthGuard>
 *
 * AC 7: Redirects to /login if not authenticated
 * AC 8: Wraps protected routes (home page, tenant pages)
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    // If not authenticated and not already on login page, redirect to login
    if (!isAuthenticated && pathname !== '/login') {
      router.push('/login')
    }
  }, [isAuthenticated, router, pathname])

  // If not authenticated, don't render children (prevents flash of protected content)
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    )
  }

  // User is authenticated, render protected content
  return <>{children}</>
}
