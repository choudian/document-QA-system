import client from './client'

export interface ConfigItem {
  category: string
  key: string
  value: any
  status: boolean
}

export interface ConfigUpdateRequest {
  items: ConfigItem[]
}

export interface EffectiveConfigResponse {
  configs: Record<string, Record<string, any>>
}

export interface FieldDefinition {
  name: string
  type: 'string' | 'number' | 'boolean' | 'array'
  required: boolean
  sensitive: boolean
  min?: number
  max?: number
  allowed_values?: any[]
  label?: string
  placeholder?: string
}

export interface ConfigDefinitionItem {
  category: string
  key: string
  label: string
  fields: FieldDefinition[]
}

export interface ConfigDefinitionsResponse {
  definitions: ConfigDefinitionItem[]
}

export const configApi = {
  getDefinitions: async () => {
    const res = await client.get<ConfigDefinitionsResponse>('/configs/definitions')
    return res.data
  },
  getEffective: async () => {
    const res = await client.get<EffectiveConfigResponse>('/configs/effective')
    return res.data
  },
  getMyConfig: async () => {
    const res = await client.get<EffectiveConfigResponse>('/configs/my-config')
    return res.data
  },
  updateConfig: async (payload: ConfigUpdateRequest) => {
    await client.put('/configs', payload)
  },
  updateSystem: async (payload: ConfigUpdateRequest) => {
    await client.put('/configs/system', payload)
  },
  updateTenant: async (payload: ConfigUpdateRequest, tenantId?: string) => {
    const params = tenantId ? `?tenant_id=${tenantId}` : ''
    await client.put(`/configs/tenant${params}`, payload)
  },
  updateUser: async (payload: ConfigUpdateRequest, userId?: string) => {
    const params = userId ? `?user_id=${userId}` : ''
    await client.put(`/configs/user${params}`, payload)
  },
}

