import request from './request'

export interface Document {
  id: number
  tenant_id: number
  kb_id: number
  name: string
  char_length: number
  status: number
  error_message?: string
  paragraph_count: number
  user_id?: number
  uploader_username?: string
  created_at: string
  updated_at: string
}

export interface DocumentUploadResponse {
  id: number
  name: string
  status: number
  char_length: number
  message: string
}

export const documentApi = {
  upload(kbId: number, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<DocumentUploadResponse>(`/documents/upload/${kbId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  list(kbId: number, params?: { page?: number; page_size?: number }) {
    return request.get<Document[]>(`/documents/list/${kbId}`, { params })
  },

  get(id: number) {
    return request.get<Document>(`/documents/${id}`)
  },

  delete(id: number) {
    return request.delete(`/documents/${id}`)
  },

  parse(id: number) {
    return request.post(`/documents/${id}/parse`)
  },

  getContent(id: number) {
    return request.get<{ id: number; name: string; content: string; char_length: number }>(`/documents/${id}/content`)
  }
}
