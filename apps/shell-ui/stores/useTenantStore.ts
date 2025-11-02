import { create } from 'zustand'
import type { Tenant } from '@/types/tenant'
import type { Dashboard } from '@/types/dashboard'

interface TenantStore {
  selectedTenant: Tenant | null
  tenantToken: string | null
  selectedDashboard: Dashboard | null
  setSelectedTenant: (tenant: Tenant) => void
  setTenantToken: (token: string) => void
  setSelectedDashboard: (dashboard: Dashboard | null) => void
  clearTenant: () => void
}

/**
 * Zustand store for tenant selection and tenant-scoped token management
 *
 * AC 7: Stores selected tenant metadata (id, name, slug) and tenant-scoped token
 *
 * Usage:
 * const { selectedTenant, tenantToken, setSelectedTenant, setTenantToken, clearTenant } = useTenantStore()
 */
export const useTenantStore = create<TenantStore>((set) => ({
  selectedTenant: null,
  tenantToken: null,
  selectedDashboard: null,

  setSelectedTenant: (tenant: Tenant) => {
    set({ selectedTenant: tenant })
  },

  setTenantToken: (token: string) => {
    set({ tenantToken: token })
  },

  setSelectedDashboard: (dashboard: Dashboard | null) => {
    set({ selectedDashboard: dashboard })
  },

  clearTenant: () => {
    set({ selectedTenant: null, tenantToken: null, selectedDashboard: null })
  },
}))
