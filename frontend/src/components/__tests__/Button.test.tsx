import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Button } from 'antd'

describe('Button Component', () => {
  it('should render button with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('should render button with different types', () => {
    const { rerender } = render(<Button type="primary">Primary</Button>)
    expect(screen.getByText('Primary')).toBeInTheDocument()

    rerender(<Button type="default">Default</Button>)
    expect(screen.getByText('Default')).toBeInTheDocument()
  })

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByText('Disabled')).toBeDisabled()
  })
})
