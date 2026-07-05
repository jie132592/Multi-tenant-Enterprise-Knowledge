import request from './request'

export interface ChatSession {
  id: number
  tenant_id: number
  user_id: number
  kb_id: number | null
  title: string
  is_active: number
  message_count: number
  last_message?: string
  last_message_at?: string
  created_at: string
}

export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  meta: Record<string, any>
  created_at: string
}

export interface Citation {
  paragraph_id: number
  content: string
  score: number
  document_name: string
}

export interface TokenUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
  message_id: number
  token_usage?: TokenUsage
}

export interface CreateSessionData {
  kb_id: number
  title?: string
}

export interface SendMessageData {
  content: string
  kb_id?: number
}

export const chatApi = {
  createSession(data: CreateSessionData) {
    return request.post<ChatSession>('/chat', data)
  },

  listSessions(params?: { kb_id?: number; page?: number; page_size?: number }) {
    return request.get<ChatSession[]>('/chat', { params })
  },

  getSession(id: number) {
    return request.get<{ session: any; messages: ChatMessage[] }>(`/chat/${id}`)
  },

  deleteSession(id: number) {
    return request.delete(`/chat/${id}`)
  },

  sendMessage(sessionId: number, data: SendMessageData) {
    return request.post<ChatResponse>(`/chat/${sessionId}/message`, data)
  },

  sendMessageStream(
    sessionId: number,
    data: SendMessageData,
    onChunk: (content: string) => void
  ): Promise<{ citations: Citation[]; tokenUsage?: TokenUsage }> {
    return new Promise((resolve, reject) => {
      const token = localStorage.getItem('token')
      const baseURL = 'http://localhost:8000/api'

      fetch(`${baseURL}/chat/${sessionId}/message/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify(data)
      }).then(response => {
        const reader = response.body?.getReader()
        const decoder = new TextDecoder()

        if (!reader) {
          reject(new Error('No reader available'))
          return
        }

        const processStream = () => {
          reader.read().then(({ done, value }) => {
            if (done) {
              return
            }

            const chunk = decoder.decode(value, { stream: true })
            const lines = chunk.split('\n')

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6))
                if (data.content) {
                  onChunk(data.content)
                }
                if (data.done) {
                  resolve({
                    citations: data.citations || [],
                    tokenUsage: data.token_usage
                  })
                }
              }
            }

            processStream()
          }).catch(reject)
        }

        processStream()
      }).catch(reject)
    })
  },

  clearHistory(sessionId: number) {
    return request.post(`/chat/${sessionId}/clear`)
  }
}
