import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/contexts/AuthContext'
import DebugPanel from '@/components/dashboard/DebugPanel'
import { ToastContainer } from '@/components/ui/Toast'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { theme } from './theme'
import '@fontsource/roboto/300.css'
import '@fontsource/roboto/400.css'
import '@fontsource/roboto/500.css'
import '@fontsource/roboto/700.css'

export const metadata: Metadata = {
  title: 'Kyros SaaS PoC',
  description: 'Multi-tenant dashboard platform with tenant-isolated data access',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <AuthProvider>
            {children}
            <DebugPanel />
            <ToastContainer />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
