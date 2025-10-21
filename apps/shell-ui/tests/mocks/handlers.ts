import { http, HttpResponse } from 'msw'

export const handlers = [
  // Mock login endpoint
  http.post('/api/auth/mock-login', async ({ request }) => {
    const { email } = await request.json() as { email: string }
    return HttpResponse.json({
      token: 'mock-user-token',
      user: {
        id: 'user-123',
        email: email,
      },
    })
  }),

  // Mock token exchange endpoint
  http.post('/api/token/exchange', async ({ request }) => {
    const { tenant_id } = await request.json() as { tenant_id: string }
    const authHeader = request.headers.get('Authorization')

    if (!authHeader) {
      return new HttpResponse(null, { status: 401 })
    }

    return HttpResponse.json({
      access_token: 'mock-tenant-token',
      token_type: 'Bearer',
      expires_in: 3600,
    })
  }),

  // Mock /api/me endpoint
  http.get('/api/me', ({ request }) => {
    const authHeader = request.headers.get('Authorization')

    if (!authHeader) {
      return new HttpResponse(null, { status: 401 })
    }

    return HttpResponse.json({
      user_id: 'user-123',
      email: 'analyst@acme.com',
      name: 'Alice Analyst',
      tenants: [
        {
          tenant_id: 'tenant-1',
          name: 'Acme Corp',
          slug: 'acme-corp',
          config_json: {
            branding: {
              primary_color: '#2563eb',
            },
            description: 'Acme Corporation tenant',
          },
        },
        {
          tenant_id: 'tenant-2',
          name: 'Beta Industries',
          slug: 'beta-industries',
          config_json: {
            branding: {
              primary_color: '#059669',
            },
            description: 'Beta Industries tenant',
          },
        },
      ],
    })
  }),
]
