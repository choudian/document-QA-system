import client from './client'

export interface Role {
  id: string
  name: string
  description?: string
  tenant_id: string | null  // 系统级角色为null
  status: boolean
  created_at: string
  updated_at: string
  created_by?: string
}

export interface RoleCreate {
  name: string
  description?: string
  tenant_id: string | null  // 系统级角色为null
  status?: boolean
}

export interface RoleUpdate {
  name?: string
  description?: string
  status?: boolean
}

export interface RoleListParams {
  skip?: number
  limit?: number
  status?: boolean
}

export interface AssignPermissionsRequest {
  permission_ids: string[]
}

export interface AssignRolesRequest {
  role_ids: string[]
}

export interface AssignUsersRequest {
  user_ids: string[]
}

export const roleApi = {
  // 获取角色列表
  getList: async (params: RoleListParams) => {
    const response = await client.get<Role[]>('/roles', { params })
    return response.data
  },

  // 获取单个角色
  getById: async (id: string) => {
    const response = await client.get<Role>(`/roles/${id}`)
    return response.data
  },

  // 创建角色
  create: async (data: RoleCreate) => {
    const response = await client.post<Role>('/roles', data)
    return response.data
  },

  // 更新角色
  update: async (id: string, data: RoleUpdate) => {
    const response = await client.put<Role>(`/roles/${id}`, data)
    return response.data
  },

  // 删除角色
  delete: async (id: string) => {
    await client.delete(`/roles/${id}`)
  },

  // 启用/停用角色
  updateStatus: async (id: string, status: boolean) => {
    const response = await client.patch<Role>(`/roles/${id}/status`, null, {
      params: { status },
    })
    return response.data
  },

  // 为角色分配权限
  assignPermissions: async (id: string, data: AssignPermissionsRequest) => {
    const response = await client.post<Role>(`/roles/${id}/permissions`, data)
    return response.data
  },

  // 获取角色的权限列表
  getPermissions: async (id: string) => {
    const response = await client.get<any[]>(`/roles/${id}/permissions`)
    return response.data
  },

  // 为用户分配角色
  assignRolesToUser: async (userId: string, data: AssignRolesRequest) => {
    const response = await client.post<any>(`/roles/users/${userId}/roles`, data)
    return response.data
  },

  // 为角色分配用户
  assignUsers: async (id: string, data: AssignUsersRequest) => {
    const response = await client.post<Role>(`/roles/${id}/users`, data)
    return response.data
  },

  // 获取角色的用户列表
  getUsers: async (id: string) => {
    const response = await client.get<any[]>(`/roles/${id}/users`)
    return response.data
  },
}

