'use client';

import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { jwtDecode } from 'jwt-decode';
import { useTenantStore } from '@/stores/useTenantStore';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/components/ui/Toast';

/**
 * Token Refresh Hook
 *
 * Proactively refreshes tenant-scoped token before expiry.
 * Monitors token expiration and triggers exchange 5 minutes before expiry.
 *
 * Story 5.3 AC 7-10: Optional proactive token refresh
 */

interface JWTPayload {
  exp: number;
  sub: string;
  tenant_id?: string;
  tenant_ids?: string[];
}

const REFRESH_BEFORE_EXPIRY = 5 * 60 * 1000; // 5 minutes in milliseconds

export function useTokenRefresh() {
  const router = useRouter();
  const { tenantToken, setTenantToken, selectedTenant, clearTenant } = useTenantStore();
  const { userToken, logout } = useAuth();
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isRefreshingRef = useRef(false);

  useEffect(() => {
    // Clear any existing timer
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }

    if (!tenantToken || !userToken || !selectedTenant) {
      // No token to refresh
      return;
    }

    try {
      // Decode tenant token to get expiry
      const decoded = jwtDecode<JWTPayload>(tenantToken);
      const expiresAt = decoded.exp * 1000; // Convert to milliseconds
      const now = Date.now();
      const timeUntilExpiry = expiresAt - now;

      if (timeUntilExpiry <= 0) {
        // Token already expired
        console.warn('[TokenRefresh] Token already expired');
        handleTokenExpired();
        return;
      }

      // Calculate when to trigger refresh (5 minutes before expiry)
      const refreshIn = timeUntilExpiry - REFRESH_BEFORE_EXPIRY;

      if (refreshIn <= 0) {
        // Token expiring soon, refresh immediately
        console.log('[TokenRefresh] Token expiring soon, refreshing now');
        performTokenRefresh();
        return;
      }

      // Schedule refresh
      console.log(`[TokenRefresh] Scheduling refresh in ${Math.round(refreshIn / 1000)}s`);
      refreshTimerRef.current = setTimeout(() => {
        performTokenRefresh();
      }, refreshIn);

    } catch (error) {
      console.error('[TokenRefresh] Failed to decode token:', error);
    }

    // Cleanup timer on unmount or token change
    return () => {
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current);
        refreshTimerRef.current = null;
      }
    };
  }, [tenantToken, userToken, selectedTenant]);

  const performTokenRefresh = async () => {
    if (isRefreshingRef.current) {
      console.log('[TokenRefresh] Refresh already in progress, skipping');
      return;
    }

    if (!userToken || !selectedTenant) {
      console.error('[TokenRefresh] Missing user token or tenant');
      return;
    }

    isRefreshingRef.current = true;

    try {
      console.log(`[TokenRefresh] Refreshing token for tenant: ${selectedTenant.tenant_id}`);

      // Call token exchange endpoint
      const response = await fetch('/api/token/exchange', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`,
        },
        body: JSON.stringify({
          tenant_id: selectedTenant.tenant_id,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          // User token expired
          console.warn('[TokenRefresh] User token expired during refresh');
          toast.error('Please log in again.');
          logout();
          router.push('/login');
          return;
        }

        throw new Error(`Token exchange failed: ${response.status}`);
      }

      const data = await response.json();
      const newTenantToken = data.tenant_token;

      // Update store with new token
      setTenantToken(newTenantToken);

      // Show success notification
      toast.success('Session refreshed');

      console.log('[TokenRefresh] Token refreshed successfully');

    } catch (error) {
      const err = error as Error;
      console.error('[TokenRefresh] Failed to refresh token:', err);

      // Show error notification
      toast.error('Failed to refresh session. Please select your tenant again.');

      // Clear tenant state
      clearTenant();
      router.push('/');

    } finally {
      isRefreshingRef.current = false;
    }
  };

  const handleTokenExpired = () => {
    console.warn('[TokenRefresh] Token expired, redirecting to tenant selection');
    toast.error('Your session has expired. Please select your tenant again.');
    clearTenant();
    router.push('/');
  };
}
