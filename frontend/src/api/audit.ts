import client from './client'

export interface AuditLog {
  id: string
  user_id?: string
  tenant_id?: string
  method: string
  path: string
  query_params?: string
  request_body?: string
  response_status: number
  response_body?: string
  request_size?: number
  response_size?: number
  duration_ms: number
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface AuditLogListResponse {
  items: AuditLog[]
  total: number
  page: number
  page_size: number
}

export interface AuditLogQueryParams {
  user_id?: string
  tenant_id?: string
  method?: string
  path?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export const auditApi = {
  getList: async (params?: AuditLogQueryParams) => {
    const queryString = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryString.append(key, String(value))
        }
      })
    }
    const url = `/audit-logs${queryString.toString() ? `?${queryString.toString()}` : ''}`
    const res = await client.get<AuditLogListResponse>(url)
    return res.data
  },
  getById: async (id: string) => {
    const res = await client.get<AuditLog>(`/audit-logs/${id}`)
    return res.data
  },
}

