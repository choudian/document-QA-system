import client from './client'

export interface User {
  id: string
  tenant_id: string
  username: string
  phone: string
  status: string
  is_tenant_admin: boolean
  created_at: string
  updated_at: string
  created_by?: string
}

export interface UserCreate {
  tenant_id: string
  username: string
  phone: string
  password: string
  is_tenant_admin?: boolean
}

export interface UserUpdate {
  username?: string
  phone?: string
  password?: string
  status?: string
  is_tenant_admin?: boolean
  tenant_id?: string
}

export const userApi = {
  // 获取用户列表
  getList: async (tenantId: string, params?: { skip?: number; limit?: number; status?: string }) => {
    const response = await client.get<User[]>('/users', {
      params: { tenant_id: tenantId, ...params },
    })
    return response.data
  },

  // 获取单个用户
  getById: async (id: string) => {
    const response = await client.get<User>(`/users/${id}`)
    return response.data
  },

  // 创建用户
  create: async (data: UserCreate) => {
    const response = await client.post<User>('/users', data)
    return response.data
  },

  // 更新用户
  update: async (id: string, data: UserUpdate) => {
    const response = await client.put<User>(`/users/${id}`, data)
    return response.data
  },

  // 删除用户
  delete: async (id: string) => {
    await client.delete(`/users/${id}`)
  },

  // 启用/冻结用户
  updateStatus: async (id: string, status: string) => {
    const response = await client.patch<User>(`/users/${id}/status`, null, {
      params: { status },
    })
    return response.data
  },
}

