// Tenant-related TypeScript interfaces

export interface Tenant {
  tenant_id: string
  name: string
  slug: string
  config_json?: {
    branding?: {
      primary_color?: string
      secondary_color?: string
    }
    description?: string
    [key: string]: any
  }
}

export interface UserInfoResponse {
  user_id: string
  email: string
  tenants: Tenant[]
}

export interface TokenExchangeRequest {
  tenant_id: string
}

export interface TokenExchangeResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface TenantStore {
  selectedTenant: Tenant | null
  tenantToken: string | null
  setSelectedTenant: (tenant: Tenant) => void
  setTenantToken: (token: string) => void
  clearTenant: () => void
}
