import client from './client'

export interface Tenant {
  id: string
  code: string
  name: string
  description?: string
  status: boolean
  created_at: string
  updated_at: string
  created_by?: string
}

export interface TenantCreate {
  code: string
  name: string
  description?: string
}

export interface TenantUpdate {
  code?: string
  name?: string
  description?: string
  status?: boolean
}

export const tenantApi = {
  // 获取租户列表
  getList: async (params?: { skip?: number; limit?: number; status?: boolean }) => {
    const response = await client.get<Tenant[]>('/tenants', { params })
    return response.data
  },

  // 获取单个租户
  getById: async (id: string) => {
    const response = await client.get<Tenant>(`/tenants/${id}`)
    return response.data
  },

  // 创建租户
  create: async (data: TenantCreate) => {
    const response = await client.post<Tenant>('/tenants', data)
    return response.data
  },

  // 更新租户
  update: async (id: string, data: TenantUpdate) => {
    const response = await client.put<Tenant>(`/tenants/${id}`, data)
    return response.data
  },

  // 删除租户
  delete: async (id: string) => {
    await client.delete(`/tenants/${id}`)
  },

  // 启用/停用租户
  updateStatus: async (id: string, status: boolean) => {
    const response = await client.patch<Tenant>(`/tenants/${id}/status`, null, {
      params: { status },
    })
    return response.data
  },
}

