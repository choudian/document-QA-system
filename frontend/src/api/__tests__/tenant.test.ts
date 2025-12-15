import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import * as tenantApi from '../tenant'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as any

describe('Tenant API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedAxios.create.mockReturnValue({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    })
  })

  it('should get tenant list', async () => {
    const mockTenants = [
      { id: '1', name: '租户1', code: 'tenant1' },
      { id: '2', name: '租户2', code: 'tenant2' },
    ]

    const mockGet = vi.fn().mockResolvedValue({ data: mockTenants })
    mockedAxios.create.mockReturnValue({
      get: mockGet,
    })

    // 重新导入以使用新的mock
    const { getTenants } = await import('../tenant')
    const result = await getTenants()

    expect(mockGet).toHaveBeenCalledWith('/tenants')
    expect(result).toEqual(mockTenants)
  })

  it('should create tenant', async () => {
    const newTenant = {
      name: '新租户',
      code: 'new_tenant',
      status: 'active',
    }

    const mockPost = vi.fn().mockResolvedValue({ data: { id: '1', ...newTenant } })
    mockedAxios.create.mockReturnValue({
      post: mockPost,
    })

    const { createTenant } = await import('../tenant')
    const result = await createTenant(newTenant)

    expect(mockPost).toHaveBeenCalledWith('/tenants', newTenant)
    expect(result.name).toBe(newTenant.name)
  })
})
