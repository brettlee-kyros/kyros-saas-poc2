import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const apiBaseUrl = process.env.API_BASE_URL || 'http://localhost:8000'
    const response = await fetch(`${apiBaseUrl}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'API health check failed' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Health check error:', error)
    return NextResponse.json(
      { error: 'Failed to connect to API' },
      { status: 503 }
    )
  }
}
