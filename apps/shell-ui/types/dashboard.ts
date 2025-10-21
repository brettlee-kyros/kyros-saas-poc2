// Dashboard-related TypeScript interfaces

export interface Dashboard {
  dashboard_id: string
  name: string
  slug: string
  description?: string
  framework: 'dash' | 'streamlit' | 'other'
  entry_point?: string
  config_json?: {
    thumbnail?: string
    icon?: string
    [key: string]: any
  }
}

export interface DashboardListResponse {
  tenant_id: string
  tenant_name: string
  dashboards: Dashboard[]
}

// Story 5.2: Dashboard Embedding Page interfaces
export interface DashboardPageParams {
  tenant_slug: string
  dashboard_slug: string
}

export interface DashboardEmbedState {
  dashboard: Dashboard | null
  loading: boolean
  error: string | null
  iframeLoading: boolean
  iframeError: boolean
}
