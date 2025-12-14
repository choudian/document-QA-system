import { meApi, Permission } from '@/api/me'

/**
 * 根据用户权限获取默认跳转路径
 * 按照优先级顺序：租户管理 > 用户管理 > 角色管理 > 权限管理
 */
export async function getDefaultRoute(): Promise<string> {
  try {
    const permissions = await meApi.getPermissions()
    
    // 定义菜单路径和对应的权限码，按优先级排序
    const menuRoutes = [
      { path: '/tenants', permission: 'system:tenant:menu' },
      { path: '/users', permission: 'system:user:menu' },
      { path: '/roles', permission: 'system:role:read' },
      { path: '/permissions', permission: 'system:permission:read' },
      { path: '/configs', permission: 'system:config:menu' },
      { path: '/audit-logs', permission: 'system:audit:read' },
      { path: '/documents', permission: 'doc:file:read' },
    ]
    
    // 查找第一个有权限的菜单
    for (const route of menuRoutes) {
      const hasPermission = permissions.some(
        (p: Permission) => p.code === route.permission && p.type === 'menu'
      )
      if (hasPermission) {
        return route.path
      }
    }
    
    // 如果没有找到任何有权限的菜单，默认返回文档管理（普通用户通常有文档管理权限）
    return '/documents'
  } catch (error) {
    console.error('获取默认路由失败:', error)
    // 如果获取权限失败，默认返回用户管理
    return '/users'
  }
}
