import request from './request'

export interface LoginData {
  tenant_code: string
  username: string
  password: string
}

export interface RegisterData {
  tenant_name: string
  tenant_code: string
  username: string
  email: string
  password: string
}

export interface UserInfo {
  id: number
  tenant_id: number
  username: string
  email: string
  is_active: number
  is_super_admin: number
  last_login_at: string
  created_at: string
}

export interface TokenInfo {
  access_token: string
  token_type: string
  expires_in: number
}

export const authApi = {
  login(data: LoginData) {
    return request.post<TokenInfo>('/auth/login', data)
  },

  register(data: RegisterData) {
    return request.post<UserInfo>('/auth/register', data)
  },

  getCurrentUser() {
    return request.get<UserInfo>('/auth/me')
  }
}
