/**
 * JWT Token 工具函数
 */

export interface TokenPayload {
  sub: string // 用户ID
  tenant_id: string | null // 租户ID
  is_system_admin: boolean // 是否系统管理员
  is_tenant_admin: boolean // 是否租户管理员
  exp: number // 过期时间
}

/**
 * 解析JWT token的payload
 */
export function parseToken(token: string): TokenPayload | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) {
      return null
    }
    
    // payload是base64编码的JSON
    const payload = parts[1]
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    const parsed = JSON.parse(decoded)
    
    return {
      sub: parsed.sub,
      tenant_id: parsed.tenant_id || null,
      is_system_admin: parsed.is_system_admin || false,
      is_tenant_admin: parsed.is_tenant_admin || false,
      exp: parsed.exp,
    }
  } catch (error) {
    console.error('解析token失败:', error)
    return null
  }
}

/**
 * 从localStorage获取token并解析
 */
export function getTokenPayload(): TokenPayload | null {
  const token = localStorage.getItem('token')
  if (!token) {
    return null
  }
  return parseToken(token)
}

/**
 * 检查token是否过期
 */
export function isTokenExpired(token: string): boolean {
  const payload = parseToken(token)
  if (!payload) {
    return true
  }
  
  // exp是Unix时间戳（秒），需要转换为毫秒
  const exp = payload.exp * 1000
  return Date.now() >= exp
}

