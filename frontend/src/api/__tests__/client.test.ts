import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import client from '../client'

// Mock axios
vi.mock('axios')
const mockedAxios = axios as any

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock localStorage
    Storage.prototype.getItem = vi.fn()
    Storage.prototype.setItem = vi.fn()
    Storage.prototype.removeItem = vi.fn()
  })

  it('should create axios instance with correct baseURL', () => {
    expect(mockedAxios.create).toHaveBeenCalled()
    const callArgs = mockedAxios.create.mock.calls[0][0]
    expect(callArgs.baseURL).toBe('/api/v1')
  })

  it('should add Authorization header when token exists', async () => {
    Storage.prototype.getItem = vi.fn(() => 'test-token')
    
    // Re-import to trigger interceptor setup
    await import('../client')
    
    // The token should be in localStorage
    expect(localStorage.getItem).toHaveBeenCalledWith('token')
  })

  it('should handle 401 error and redirect to login', async () => {
    const mockError = {
      response: {
        status: 401,
      },
    }

    // Mock axios interceptor
    const interceptor = {
      use: vi.fn((onFulfilled, onRejected) => {
        if (onRejected) {
          onRejected(mockError)
        }
      }),
    }

    mockedAxios.create.mockReturnValue({
      interceptors: {
        response: interceptor,
      },
    })

    await import('../client')

    // Should remove token and redirect
    expect(localStorage.removeItem).toHaveBeenCalled()
  })
})
