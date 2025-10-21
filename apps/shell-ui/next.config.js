/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  },
  async rewrites() {
    const apiBaseUrl = process.env.API_BASE_URL || 'http://localhost:8000'
    return [
      {
        // Proxy /api/tenant/* and /api/dashboards/* to Python API
        // Exclude /api/proxy/* (handled by Next.js API routes)
        source: '/api/tenant/:path*',
        destination: `${apiBaseUrl}/api/tenant/:path*`,
      },
      {
        source: '/api/dashboards/:path*',
        destination: `${apiBaseUrl}/api/dashboards/:path*`,
      },
      {
        source: '/api/auth/:path*',
        destination: `${apiBaseUrl}/api/auth/:path*`,
      },
      {
        source: '/api/token/:path*',
        destination: `${apiBaseUrl}/api/token/:path*`,
      },
      {
        source: '/api/me',
        destination: `${apiBaseUrl}/api/me`,
      },
    ]
  },
}

module.exports = nextConfig
