import client from './client'

export interface MenuItem {
  id: string
  parent_id?: string
  name: string
  path?: string
  icon?: string
  permission_code?: string
  sort_order: number
  visible: boolean
  tenant_id?: string
  status: boolean
  created_at: string
  updated_at: string
  created_by?: string
  children?: MenuItem[]
}

export const menuApi = {
  // 获取当前用户的可见菜单（动态菜单接口）
  getMyMenus: async () => {
    const response = await client.get<MenuItem[]>('/menus/my')
    return response.data
  },

  // 获取菜单列表（树形结构）
  getMenus: async (tenantId?: string, includeInvisible = false) => {
    const params = new URLSearchParams()
    if (tenantId) {
      params.append('tenant_id', tenantId)
    }
    if (includeInvisible) {
      params.append('include_invisible', 'true')
    }
    const queryString = params.toString()
    const url = queryString ? `/menus?${queryString}` : '/menus'
    const response = await client.get<MenuItem[]>(url)
    return response.data
  },

  // 获取单个菜单
  getMenu: async (menuId: string) => {
    const response = await client.get<MenuItem>(`/menus/${menuId}`)
    return response.data
  },

  // 创建菜单
  createMenu: async (menu: Partial<MenuItem>) => {
    const response = await client.post<MenuItem>('/menus', menu)
    return response.data
  },

  // 更新菜单
  updateMenu: async (menuId: string, menu: Partial<MenuItem>) => {
    const response = await client.put<MenuItem>(`/menus/${menuId}`, menu)
    return response.data
  },

  // 删除菜单
  deleteMenu: async (menuId: string) => {
    await client.delete(`/menus/${menuId}`)
  },

  // 启用/停用菜单
  updateMenuStatus: async (menuId: string, status: boolean) => {
    const response = await client.patch<MenuItem>(`/menus/${menuId}/status?status=${status}`)
    return response.data
  },

  // 批量更新菜单排序
  updateMenuSort: async (menuOrders: Array<{ id: string; sort_order: number }>) => {
    await client.post('/menus/sort', { menu_orders: menuOrders })
  },
}

