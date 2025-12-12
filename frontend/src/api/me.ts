import client from './client'

export interface User {
  id: string
  tenant_id?: string
  username: string
  phone: string
  status: string
  is_tenant_admin: boolean
  is_system_admin: boolean
  created_at: string
  updated_at: string
  created_by?: string
}

export interface Permission {
  code: string
  name: string
  type: 'menu' | 'api' | 'button' | 'tab'
}

export const meApi = {
  // 获取当前用户信息
  getMe: async () => {
    const response = await client.get<User>('/me')
    return response.data
  },

  // 获取当前用户权限
  getPermissions: async () => {
    const response = await client.get<Permission[]>('/me/permissions')
    return response.data
  },
}

