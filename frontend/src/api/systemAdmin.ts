import client from './client'

export interface SystemAdminInitPayload {
  username: string
  phone: string
  password: string
}

export const systemAdminApi = {
  init: async (data: SystemAdminInitPayload) => {
    const res = await client.post('/system-admin/init', data)
    return res.data
  },
  exists: async () => {
    const res = await client.get<{ exists: boolean }>('/system-admin/exists')
    return res.data.exists
  },
}

