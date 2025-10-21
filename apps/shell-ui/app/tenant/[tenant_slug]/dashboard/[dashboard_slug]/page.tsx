'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useTenantStore } from '@/stores/useTenantStore';
import AuthGuard from '@/components/auth/AuthGuard';
import type { Dashboard } from '@/types/dashboard';
import { useTokenRefresh } from '@/hooks/useTokenRefresh';

interface DashboardPageParams {
  tenant_slug: string;
  dashboard_slug: string;
  [key: string]: string;
}

/**
 * Dashboard Embedding Page
 *
 * Embeds Dash dashboards within Shell UI using iframe that proxies
 * through Next.js API route (Story 5.1) for server-side token injection.
 *
 * Flow:
 * 1. Validate user has access to dashboard for this tenant
 * 2. Render iframe pointing to /api/proxy/dash/{dashboard_slug}/
 * 3. iframe requests go through reverse proxy with injected Authorization header
 * 4. Dash app receives authenticated request and renders
 */
export default function DashboardEmbedPage() {
  return (
    <AuthGuard>
      <DashboardEmbedContent />
    </AuthGuard>
  );
}

function DashboardEmbedContent() {
  const params = useParams<DashboardPageParams>();
  const router = useRouter();
  const { selectedTenant, tenantToken } = useTenantStore();

  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [iframeLoading, setIframeLoading] = useState(true);
  const [iframeError, setIframeError] = useState(false);

  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Enable proactive token refresh (Story 5.3)
  useTokenRefresh();

  // Validate tenant slug matches selected tenant
  useEffect(() => {
    if (!selectedTenant || selectedTenant.slug !== params.tenant_slug) {
      router.push('/');
      return;
    }

    // Fetch dashboard details and validate access
    fetchDashboardDetails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTenant, params.tenant_slug, params.dashboard_slug]);

  const fetchDashboardDetails = async () => {
    if (!selectedTenant || !tenantToken) {
      setError('Authentication required');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Fetch tenant's dashboards to verify access
      const response = await fetch(
        `/api/tenant/${selectedTenant.tenant_id}/dashboards`,
        {
          headers: {
            'Authorization': `Bearer ${tenantToken}`,
          },
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          setError('Session expired. Please log in again.');
          setTimeout(() => router.push('/'), 2000);
          return;
        }
        throw new Error('Failed to fetch dashboards');
      }

      const data = await response.json();
      const matchingDashboard = data.dashboards.find(
        (d: Dashboard) => d.slug === params.dashboard_slug
      );

      if (!matchingDashboard) {
        setError('Dashboard not found or not assigned to this tenant');
        setLoading(false);
        return;
      }

      setDashboard(matchingDashboard);
      setLoading(false);

    } catch (err) {
      const error = err as Error;
      console.error('Failed to fetch dashboard details:', error);
      setError(error.message || 'Failed to load dashboard');
      setLoading(false);
    }
  };

  const handleIframeLoad = () => {
    setIframeLoading(false);
    setIframeError(false);
  };

  const handleIframeError = () => {
    setIframeLoading(false);
    setIframeError(true);
  };

  const handleRetry = () => {
    setIframeError(false);
    setIframeLoading(true);
    // Force iframe reload by updating src
    if (iframeRef.current) {
      const currentSrc = iframeRef.current.src;
      iframeRef.current.src = '';
      setTimeout(() => {
        if (iframeRef.current) {
          iframeRef.current.src = currentSrc;
        }
      }, 100);
    }
  };

  const handleBackToDashboards = () => {
    router.push(`/tenant/${params.tenant_slug}`);
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex flex-col h-screen">
        {/* Header with loading skeleton */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-300 rounded w-48 mb-2"></div>
            <div className="h-6 bg-gray-300 rounded w-64"></div>
          </div>
        </header>

        {/* Main content loading skeleton */}
        <main className="flex-1 p-6">
          <div className="animate-pulse h-full bg-gray-200 rounded-lg"></div>
        </main>
      </div>
    );
  }

  // Error state (dashboard not found or access denied)
  if (error || !dashboard) {
    return (
      <div className="flex flex-col items-center justify-center h-screen p-6">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">🚫</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Dashboard Not Found
          </h2>
          <p className="text-gray-600 mb-6">
            {error || 'The requested dashboard is not available for this tenant.'}
          </p>
          <button
            onClick={handleBackToDashboards}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Dashboards
          </button>
        </div>
      </div>
    );
  }

  // Build iframe src using reverse proxy route
  // Pass tenant token as query parameter (will be extracted by proxy for header injection)
  const iframeSrc = `/api/proxy/dash/${dashboard.slug}/?token=${encodeURIComponent(tenantToken || '')}`;

  return (
    <div className="flex flex-col h-screen">
      {/* Header with breadcrumb and navigation */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            {/* Breadcrumb */}
            <nav className="text-sm text-gray-600 mb-1">
              <button
                onClick={() => router.push('/')}
                className="hover:text-blue-600 transition-colors"
              >
                Home
              </button>
              <span className="mx-2">/</span>
              <button
                onClick={handleBackToDashboards}
                className="hover:text-blue-600 transition-colors"
              >
                {selectedTenant?.name || 'Tenant'}
              </button>
              <span className="mx-2">/</span>
              <span className="text-gray-800 font-medium">Dashboards</span>
            </nav>

            {/* Dashboard title */}
            <h1 className="text-2xl font-bold text-gray-900">
              {dashboard.name}
            </h1>
          </div>

          {/* Back button */}
          <button
            onClick={handleBackToDashboards}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <span>←</span>
            <span>Back to Dashboards</span>
          </button>
        </div>
      </header>

      {/* Main content area with iframe */}
      <main className="flex-1 overflow-hidden relative">
        {/* Loading skeleton overlay */}
        {iframeLoading && !iframeError && (
          <div className="absolute inset-0 bg-gray-50 flex items-center justify-center z-10">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <p className="text-gray-600">Loading dashboard...</p>
            </div>
          </div>
        )}

        {/* Iframe error state */}
        {iframeError && (
          <div className="absolute inset-0 bg-gray-50 flex items-center justify-center z-10">
            <div className="text-center max-w-md p-6">
              <div className="text-6xl mb-4">⚠️</div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">
                Failed to Load Dashboard
              </h3>
              <p className="text-gray-600 mb-6">
                The dashboard could not be loaded. This may be due to a network error or the dashboard service being unavailable.
              </p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleRetry}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Retry
                </button>
                <button
                  onClick={handleBackToDashboards}
                  className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Back to Dashboards
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Embedded dashboard iframe */}
        <iframe
          ref={iframeRef}
          src={iframeSrc}
          className="w-full h-full border-0"
          title={dashboard.name}
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          allow="fullscreen"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        />
      </main>
    </div>
  );
}
