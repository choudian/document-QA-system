import client from './client'

export interface Permission {
  id: string
  code: string
  name: string
  description?: string
  type: 'menu' | 'api' | 'button' | 'tab'
  module: string
  tenant_id?: string
  status: boolean
  created_at: string
  updated_at: string
  created_by?: string
}

export interface PermissionCreate {
  code: string
  name: string
  description?: string
  type: 'menu' | 'api' | 'button' | 'tab'
  module: string
  tenant_id?: string
  status?: boolean
}

export interface PermissionUpdate {
  code?: string
  name?: string
  description?: string
  type?: 'menu' | 'api' | 'button' | 'tab'
  module?: string
  status?: boolean
}

export interface PermissionListParams {
  skip?: number
  limit?: number
  tenant_id?: string
  module?: string
  type?: 'menu' | 'api' | 'button' | 'tab'
  status?: boolean
}

export const permissionApi = {
  // 获取权限列表
  getList: async (params?: PermissionListParams) => {
    const response = await client.get<Permission[]>('/permissions', { params })
    return response.data
  },

  // 获取单个权限
  getById: async (id: string) => {
    const response = await client.get<Permission>(`/permissions/${id}`)
    return response.data
  },

  // 创建权限
  create: async (data: PermissionCreate) => {
    const response = await client.post<Permission>('/permissions', data)
    return response.data
  },

  // 更新权限
  update: async (id: string, data: PermissionUpdate) => {
    const response = await client.put<Permission>(`/permissions/${id}`, data)
    return response.data
  },

  // 删除权限
  delete: async (id: string) => {
    await client.delete(`/permissions/${id}`)
  },

  // 启用/停用权限
  updateStatus: async (id: string, status: boolean) => {
    const response = await client.patch<Permission>(`/permissions/${id}/status`, null, {
      params: { status },
    })
    return response.data
  },
}

