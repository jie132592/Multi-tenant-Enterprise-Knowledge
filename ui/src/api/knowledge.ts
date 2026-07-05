import request from './request'

export interface KnowledgeBase {
  id: number
  tenant_id: number
  user_id?: number
  name: string
  description: string
  status: number
  document_count: number
  paragraph_count: number
  creator_username?: string
  created_at: string
  updated_at: string
}

export interface KnowledgeBaseCreate {
  name: string
  description?: string
}

export interface KnowledgeBaseUpdate {
  name?: string
  description?: string
  status?: number
}

export const knowledgeApi = {
  list(params?: { page?: number; page_size?: number; keyword?: string }) {
    return request.get<KnowledgeBase[]>('/kb', { params })
  },

  get(id: number) {
    return request.get<KnowledgeBase>(`/kb/${id}`)
  },

  create(data: KnowledgeBaseCreate) {
    return request.post<KnowledgeBase>('/kb', data)
  },

  update(id: number, data: KnowledgeBaseUpdate) {
    return request.put<KnowledgeBase>(`/kb/${id}`, data)
  },

  delete(id: number) {
    return request.delete(`/kb/${id}`)
  }
}
