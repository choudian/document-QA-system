import { useState, useEffect } from 'react'
import { Form, Input, Button, Card, message, Space, Modal } from 'antd'
import { useNavigate } from 'react-router-dom'
import { authApi, LoginPayload } from '@/api/auth'
import { systemAdminApi } from '@/api/systemAdmin'

const Login = () => {
  const [loading, setLoading] = useState(false)
  const [initModalOpen, setInitModalOpen] = useState(false)
  const [initLoading, setInitLoading] = useState(false)
  const [initForm] = Form.useForm()
  const [showInit, setShowInit] = useState(false)
  const navigate = useNavigate()
  const [form] = Form.useForm()

  useEffect(() => {
    const checkSystemAdmin = async () => {
      try {
        const exists = await systemAdminApi.exists()
        setShowInit(!exists)
      } catch {
        setShowInit(true)
      }
    }
    checkSystemAdmin()
  }, [])

  const extractErrorMsg = (err: any) => {
    const detail = err?.response?.data?.detail
    if (!detail) return '登录失败'
    if (Array.isArray(detail)) {
      // Pydantic 校验错误时 detail 是数组，取 msg 组合
      return detail.map((d) => d?.msg || '').filter(Boolean).join('; ') || '登录失败'
    }
    if (typeof detail === 'string') return detail
    return JSON.stringify(detail)
  }

  const handleSubmit = async (values: LoginPayload) => {
    setLoading(true)
    try {
      const data = await authApi.login({
        phone: values.phone,
        password: values.password,
      })
      localStorage.setItem('token', data.access_token)
      message.success('登录成功')
      
      // 根据用户权限跳转到默认页面
      const { getDefaultRoute } = await import('@/utils/getDefaultRoute')
      const defaultRoute = await getDefaultRoute()
      navigate(defaultRoute)
    } catch (error: any) {
      message.error(extractErrorMsg(error))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f5f5f5' }}>
      <Card title="登录" style={{ width: 360 }}>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            label="手机号"
            name="phone"
            rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号' },
            ]}
          >
            <Input placeholder="请输入手机号" maxLength={11} />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
              { max: 72, message: '密码不能超过72个字符' },
            ]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              登录
            </Button>
          </Form.Item>

          {showInit && (
            <Form.Item style={{ marginBottom: 0 }}>
              <Button type="link" block onClick={() => setInitModalOpen(true)}>
                初始化平台管理员
              </Button>
            </Form.Item>
          )}
        </Form>
      </Card>

      <Modal
        title="初始化平台管理员"
        open={initModalOpen}
        onCancel={() => setInitModalOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form
          form={initForm}
          layout="vertical"
          onFinish={async (values) => {
            setInitLoading(true)
            try {
              await systemAdminApi.init(values)
              message.success('平台管理员创建成功，请使用该账号登录')
              setInitModalOpen(false)
              initForm.resetFields()
              // 重新检查系统管理员是否存在，隐藏初始化链接
              const exists = await systemAdminApi.exists()
              setShowInit(!exists)
            } catch (error: any) {
              const msg = error?.response?.data?.detail || '初始化失败'
              if (Array.isArray(msg)) {
                message.error(msg.map((d: any) => d?.msg || '').filter(Boolean).join('; ') || '初始化失败')
              } else if (typeof msg === 'string') {
                message.error(msg)
              } else {
                message.error(JSON.stringify(msg))
              }
            } finally {
              setInitLoading(false)
            }
          }}
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { max: 50, message: '用户名不能超过50个字符' },
            ]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>

          <Form.Item
            label="手机号"
            name="phone"
            rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号' },
            ]}
          >
            <Input placeholder="请输入手机号" maxLength={11} />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
              { max: 72, message: '密码不能超过72个字符' },
            ]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>

          <Form.Item>
            <Space style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button onClick={() => setInitModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={initLoading}>
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Login

