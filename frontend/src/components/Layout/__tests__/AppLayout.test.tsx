import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import AppLayout from '../AppLayout'

// Mock useAuth hook
vi.mock('../../../hooks/useAuth', () => ({
  default: () => ({
    user: {
      id: '1',
      username: 'testuser',
      tenant_id: 'tenant1',
    },
    permissions: ['doc:file:read', 'doc:file:upload'],
  }),
}))

describe('AppLayout Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render layout with header and sidebar', () => {
    render(
      <BrowserRouter>
        <AppLayout>
          <div>Test Content</div>
        </AppLayout>
      </BrowserRouter>
    )

    expect(screen.getByText(/智能文档问答系统/i)).toBeInTheDocument()
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('should render menu items based on permissions', () => {
    render(
      <BrowserRouter>
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      </BrowserRouter>
    )

    // 检查菜单项是否根据权限显示
    // 这里需要根据实际的菜单结构来调整
    expect(screen.getByText(/文档管理/i)).toBeInTheDocument()
  })
})
