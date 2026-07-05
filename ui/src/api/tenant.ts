import request from './request'

export interface Tenant {
  id: number
  name: string
  code: string
  status: number
  description: string
  user_count: number
  kb_count: number
  created_at: string
}

export interface TenantListResponse {
  total: number
  page: number
  page_size: number
  list: Tenant[]
}

export const tenantApi = {
  list(params?: { keyword?: string; page?: number; page_size?: number }) {
    return request.get<TenantListResponse>('/tenants', { params })
  },

  get(id: number) {
    return request.get<Tenant>(`/tenants/${id}`)
  },

  create(data: { name: string; code: string; description?: string }) {
    return request.post<Tenant>('/tenants', data)
  },

  update(id: number, data: { name?: string; description?: string; status?: number }) {
    return request.put<Tenant>(`/tenants/${id}`, data)
  },

  delete(id: number) {
    return request.delete(`/tenants/${id}`)
  }
}
