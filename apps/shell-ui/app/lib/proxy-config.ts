/**
 * Dashboard configuration for reverse proxy routing.
 *
 * This module provides configuration for mapping dashboard slugs to
 * Dash application ports and URLs.
 */

export interface DashboardConfig {
  slug: string;
  port: number;
  name: string;
  baseUrl?: string; // For Docker Compose service names
}

/**
 * Dashboard configurations
 *
 * Maps dashboard slugs to Dash application ports and URLs.
 * Supports both local development (localhost) and Docker Compose
 * deployment (service names) via environment variables.
 */
export const DASHBOARD_CONFIGS: Record<string, DashboardConfig> = {
  'customer-lifetime-value': {
    slug: 'customer-lifetime-value',
    port: 8050,
    name: 'Customer Lifetime Value',
    // Use Docker service names when running in container, localhost for local dev
    baseUrl: process.env.DASH_CLV_URL || process.env.NODE_ENV === 'production'
      ? 'http://dash-app-clv:8050'
      : 'http://localhost:8050',
  },
  'risk-analysis': {
    slug: 'risk-analysis',
    port: 8051,
    name: 'Risk Analysis',
    // Use Docker service names when running in container, localhost for local dev
    baseUrl: process.env.DASH_RISK_URL || process.env.NODE_ENV === 'production'
      ? 'http://dash-app-risk:8051'
      : 'http://localhost:8051',
  },
};

/**
 * Get dashboard configuration by slug.
 *
 * @param slug - Dashboard slug (e.g., 'customer-lifetime-value')
 * @returns Dashboard configuration or undefined if not found
 */
export function getDashboardConfig(slug: string): DashboardConfig | undefined {
  return DASHBOARD_CONFIGS[slug];
}

/**
 * Get all available dashboard slugs.
 *
 * @returns Array of dashboard slugs
 */
export function getDashboardSlugs(): string[] {
  return Object.keys(DASHBOARD_CONFIGS);
}

/**
 * Validate if a dashboard slug is allowed for proxying.
 *
 * This provides SSRF protection by only allowing known dashboards.
 *
 * @param slug - Dashboard slug to validate
 * @returns true if slug is valid, false otherwise
 */
export function isValidDashboardSlug(slug: string): boolean {
  return slug in DASHBOARD_CONFIGS;
}
