import { NextRequest, NextResponse } from 'next/server';
import { getDashboardConfig, isValidDashboardSlug } from '@/app/lib/proxy-config';

/**
 * Reverse Proxy API Route for Dash Applications
 *
 * This route acts as a reverse proxy to Dash applications, injecting
 * the tenant-scoped JWT token as an Authorization header server-side.
 * This prevents token exposure to client-side JavaScript.
 *
 * Route: /api/proxy/dash/[...path]
 * Example: /api/proxy/dash/customer-lifetime-value/ -> http://localhost:8050/
 */

interface ProxyParams {
  params: {
    path: string[];
  };
}

/**
 * Handle proxied GET requests to Dash applications
 */
export async function GET(request: NextRequest, { params }: ProxyParams) {
  return handleProxyRequest(request, params.path);
}

/**
 * Handle proxied POST requests to Dash applications
 */
export async function POST(request: NextRequest, { params }: ProxyParams) {
  return handleProxyRequest(request, params.path);
}

/**
 * Core proxy request handler
 *
 * Flow:
 * 1. Extract dashboard slug from path
 * 2. Validate slug and get port mapping
 * 3. Extract tenant token from request header
 * 4. Build target Dash app URL
 * 5. Inject Authorization header with token
 * 6. Forward request to Dash app
 * 7. Return response to client
 */
async function handleProxyRequest(
  request: NextRequest,
  pathSegments: string[]
): Promise<NextResponse> {
  const startTime = Date.now();

  console.log('[Proxy] Request:', {
    method: request.method,
    path: pathSegments,
    url: request.url,
  });

  // Extract dashboard slug from path (first segment)
  const dashboardSlug = pathSegments[0];
  const remainingPath = pathSegments.slice(1).join('/');

  // Validate dashboard slug (SSRF protection)
  if (!dashboardSlug || !isValidDashboardSlug(dashboardSlug)) {
    console.error('[Proxy] Invalid dashboard slug:', dashboardSlug);
    return NextResponse.json(
      {
        error: 'INVALID_DASHBOARD',
        message: `Dashboard '${dashboardSlug}' not found`
      },
      { status: 404 }
    );
  }

  // Get dashboard configuration
  const dashboardConfig = getDashboardConfig(dashboardSlug)!;

  // Check if this is a static asset or internal Dash API route
  // Static assets: component suites, CSS, JS, images
  // Internal API routes: _dash-layout, _dash-dependencies, callbacks
  // These use session-based authentication instead of per-request tokens
  const isAssetRequest = remainingPath.startsWith('_dash-component-suites/') ||
                         remainingPath.startsWith('assets/') ||
                         remainingPath.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/);

  const isDashApiRoute = remainingPath.includes('_dash-layout') ||
                         remainingPath.includes('_dash-dependencies') ||
                         remainingPath.includes('_dash-update-component') ||
                         remainingPath.includes('_reload-hash');

  // Extract tenant token from X-Tenant-Token header or query parameter
  // Header: for direct fetch() calls from client
  // Query param: for iframe src (since iframes can't set custom headers)
  // For AJAX requests, extract from Referer header
  let tenantToken: string | null = null;

  if (isAssetRequest) {
    // Assets don't need tokens
    console.log('[Proxy] Skipping token for asset request');
  } else if (isDashApiRoute) {
    // For Dash API routes (AJAX calls), try to extract token from Referer header
    const referer = request.headers.get('referer');
    if (referer) {
      try {
        const refererUrl = new URL(referer);
        tenantToken = refererUrl.searchParams.get('token');
        if (tenantToken) {
          console.log('[Proxy] Extracted token from Referer header for Dash API route');
        }
      } catch (e) {
        console.warn('[Proxy] Failed to parse Referer header:', e);
      }
    }

    if (!tenantToken) {
      console.error('[Proxy] Missing token in Referer for Dash API route');
      return NextResponse.json(
        {
          error: 'UNAUTHORIZED',
          message: 'Tenant token required'
        },
        { status: 401 }
      );
    }
  } else {
    // Initial page load or direct requests
    tenantToken = request.headers.get('X-Tenant-Token');

    if (!tenantToken) {
      // Fallback to query parameter for iframe requests
      tenantToken = request.nextUrl.searchParams.get('token');
    }

    if (!tenantToken) {
      console.error('[Proxy] Missing tenant token in request header or query param');
      return NextResponse.json(
        {
          error: 'UNAUTHORIZED',
          message: 'Tenant token required'
        },
        { status: 401 }
      );
    }
  }

  // Build target Dash app URL using baseUrl from config
  // This supports both local development and Docker Compose
  // Important: Include the full proxy path since Dash app is configured with url_base_pathname
  const baseUrl = dashboardConfig.baseUrl;
  const fullPath = `/api/proxy/dash/${dashboardSlug}/${remainingPath}`;
  const targetUrl = new URL(`${baseUrl}${fullPath}`);

  // Preserve query parameters (except 'token' which should not be forwarded to Dash app)
  request.nextUrl.searchParams.forEach((value, key) => {
    if (key !== 'token') {
      targetUrl.searchParams.append(key, value);
    }
  });

  console.log('[Proxy] Target URL:', targetUrl.toString());

  try {
    // Build proxied request
    const headers: Record<string, string> = {
      // Forward other relevant headers
      'Content-Type': request.headers.get('content-type') || 'application/json',
      'Accept': request.headers.get('accept') || '*/*',
    };

    // Add Authorization header only for non-asset requests
    if (tenantToken) {
      headers['Authorization'] = `Bearer ${tenantToken}`;
    }

    const proxyRequestInit: RequestInit = {
      method: request.method,
      headers,
    };

    // Include body for POST requests
    if (request.method === 'POST') {
      proxyRequestInit.body = await request.text();
    }

    // Make proxied request to Dash app
    const proxyResponse = await fetch(targetUrl.toString(), proxyRequestInit);
    const duration = Date.now() - startTime;

    console.log('[Proxy] Response:', {
      status: proxyResponse.status,
      duration: `${duration}ms`,
      dashboardSlug,
    });

    // Handle 401 responses from Dash apps (expired/invalid tokens)
    if (proxyResponse.status === 401) {
      console.warn('[Proxy] 401 Unauthorized from Dash app - token expired or invalid');

      // Return standardized TOKEN_EXPIRED error
      return NextResponse.json(
        {
          error: 'TOKEN_EXPIRED',
          message: 'Your session has expired. Please select your tenant again.',
          dashboardSlug,
        },
        { status: 401 }
      );
    }

    // Forward response from Dash app
    const responseBody = await proxyResponse.text();
    const responseHeaders = new Headers();

    // Forward important headers (whitelist approach for security)
    ['content-type', 'content-length', 'cache-control'].forEach((header) => {
      const value = proxyResponse.headers.get(header);
      if (value) {
        responseHeaders.set(header, value);
      }
    });

    return new NextResponse(responseBody, {
      status: proxyResponse.status,
      headers: responseHeaders,
    });

  } catch (error) {
    const duration = Date.now() - startTime;
    const err = error as Error & { code?: string; cause?: { code?: string } };

    console.error('[Proxy] Error:', {
      dashboardSlug,
      error: err.message,
      code: err.code,
      duration: `${duration}ms`,
    });

    // Handle connection errors (Dash app not running)
    if (err.code === 'ECONNREFUSED' || err.cause?.code === 'ECONNREFUSED') {
      return NextResponse.json(
        {
          error: 'SERVICE_UNAVAILABLE',
          message: `Dashboard service '${dashboardSlug}' is unavailable`,
        },
        { status: 503 }
      );
    }

    // Handle timeout errors
    if (err.name === 'TimeoutError') {
      return NextResponse.json(
        {
          error: 'GATEWAY_TIMEOUT',
          message: 'Dashboard request timed out'
        },
        { status: 504 }
      );
    }

    // Generic error
    return NextResponse.json(
      {
        error: 'PROXY_ERROR',
        message: 'Failed to proxy request to dashboard'
      },
      { status: 500 }
    );
  }
}
