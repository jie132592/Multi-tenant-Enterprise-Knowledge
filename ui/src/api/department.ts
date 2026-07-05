import request from './request'

export interface Department {
  id: number
  tenant_id: number
  name: string
  code: string
  parent_id?: number
  leader_user_id?: number
  leader_username?: string
  description: string
  user_count: number
  created_at: string
  updated_at: string
}

export interface DepartmentTree {
  id: number
  name: string
  code: string
  parent_id?: number
  description: string
  user_count: number
  children: DepartmentTree[]
}

export const departmentApi = {
  list(params?: { keyword?: string }) {
    return request.get<Department[]>('/departments', { params })
  },

  getTree() {
    return request.get<DepartmentTree[]>('/departments/tree')
  },

  get(id: number) {
    return request.get<Department>(`/departments/${id}`)
  },

  create(data: {
    name: string
    code: string
    parent_id?: number
    description?: string
  }) {
    return request.post<Department>('/departments', data)
  },

  update(id: number, data: {
    name?: string
    code?: string
    parent_id?: number
    leader_user_id?: number
    description?: string
  }) {
    return request.put<Department>(`/departments/${id}`, data)
  },

  delete(id: number) {
    return request.delete(`/departments/${id}`)
  }
}
