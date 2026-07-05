import request from './request'

export interface User {
  id: number
  tenant_id: number
  username: string
  email: string
  role: string
  is_active: number
  is_super_admin: number
  is_tenant_admin: number
  department_id: number | null
  department_name: string | null
  last_login_at: string
  created_at: string
}

export interface UserListResponse {
  total: number
  page: number
  page_size: number
  list: User[]
}

export const userApi = {
  list(params?: { keyword?: string; page?: number; page_size?: number }) {
    return request.get<UserListResponse>('/auth/users', { params })
  },

  update(userId: number, data: { role?: string; department_id?: number | null; is_active?: number }) {
    return request.put(`/auth/users/${userId}`, data)
  }
}
