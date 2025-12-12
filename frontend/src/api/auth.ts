import client from './client'

export interface LoginPayload {
  phone: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export const authApi = {
  login: async (data: LoginPayload) => {
    const response = await client.post<TokenResponse>('/auth/login', data)
    return response.data
  },
}

