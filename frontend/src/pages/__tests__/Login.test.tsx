import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Login from '../Login'
import * as authApi from '../../api/auth'

// Mock API
vi.mock('../../api/auth')

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render login form', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )
    
    expect(screen.getByPlaceholderText(/手机号/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/密码/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument()
  })

  it('should handle login success', async () => {
    const mockLogin = vi.spyOn(authApi, 'login').mockResolvedValue({
      access_token: 'test-token',
      token_type: 'bearer',
    })

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    const phoneInput = screen.getByPlaceholderText(/手机号/i)
    const passwordInput = screen.getByPlaceholderText(/密码/i)
    const submitButton = screen.getByRole('button', { name: /登录/i })

    fireEvent.change(phoneInput, { target: { value: '13800138000' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        phone: '13800138000',
        password: 'password123',
      })
    })
  })

  it('should show error message on login failure', async () => {
    const mockLogin = vi.spyOn(authApi, 'login').mockRejectedValue({
      response: {
        data: { detail: '登录失败' },
      },
    })

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    const phoneInput = screen.getByPlaceholderText(/手机号/i)
    const passwordInput = screen.getByPlaceholderText(/密码/i)
    const submitButton = screen.getByRole('button', { name: /登录/i })

    fireEvent.change(phoneInput, { target: { value: '13800138000' } })
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled()
    })
  })
})
