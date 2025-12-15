import { useState, useEffect } from 'react'
import { Form, Input, Button, Select, Space, message } from 'antd'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import { userApi, UserCreate, UserUpdate } from '@/api/user'
import { tenantApi, Tenant } from '@/api/tenant'
import { useCurrentUser } from '@/hooks/useCurrentUser'

const UserForm = () => {
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const [loading, setLoading] = useState(false)
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [tenantDisplayName, setTenantDisplayName] = useState<string>('')
  const [tenantsLoading, setTenantsLoading] = useState(false)
  const currentUser = useCurrentUser()

  // 初始化：获取租户列表
  useEffect(() => {
    if (!currentUser || tenants.length > 0 || tenantsLoading) return
    
    const fetchTenants = async () => {
      setTenantsLoading(true)
      try {
        const data = await tenantApi.getList({ status: true })
        setTenants(data)
        
        // 如果是租户管理员，自动设置其tenant_id并更新显示名称
        if (!currentUser.is_system_admin && currentUser.tenant_id) {
          form.setFieldsValue({ tenant_id: currentUser.tenant_id })
          const tenant = data.find(t => t.id === currentUser.tenant_id)
          if (tenant) {
            setTenantDisplayName(tenant.name)
          }
        }
      } catch (error: any) {
        message.error(error.response?.data?.detail || '获取租户列表失败')
      } finally {
        setTenantsLoading(false)
      }
    }
    
    fetchTenants()
  }, [currentUser])

  // 更新租户显示名称
  useEffect(() => {
    if (!currentUser?.is_system_admin && currentUser?.tenant_id && tenants.length > 0) {
      const formTenantId = form.getFieldValue('tenant_id')
      const tenantId = formTenantId || currentUser?.tenant_id
      
      if (tenantId) {
        const tenant = tenants.find(t => t.id === tenantId)
        if (tenant) {
          setTenantDisplayName(tenant.name)
        } else {
          setTenantDisplayName(tenantId)
        }
      }
    }
  }, [tenants, currentUser?.tenant_id, currentUser?.is_system_admin])

  // 加载用户数据（编辑模式）或设置默认值（新建模式）
  useEffect(() => {
    if (!currentUser || tenantsLoading) return
    
    const loadData = async () => {
      if (id) {
        await fetchUser()
      } else {
        // 新建时，如果有 tenant_id 参数，设置默认值
        const params = new URLSearchParams(location.search)
        const tenantId = params.get('tenant_id') || currentUser?.tenant_id
        if (tenantId) {
          form.setFieldsValue({ tenant_id: tenantId })
          // 更新显示名称
          if (tenants.length > 0) {
            const tenant = tenants.find(t => t.id === tenantId)
            if (tenant) {
              setTenantDisplayName(tenant.name)
            } else {
              setTenantDisplayName(tenantId)
            }
          }
        }
      }
    }
    loadData()
  }, [id, currentUser?.tenant_id, tenants.length, tenantsLoading])


  const fetchUser = async () => {
    try {
      const user = await userApi.getById(id!)
      form.setFieldsValue({
        tenant_id: user.tenant_id,
        username: user.username,
        phone: user.phone,
        status: user.status,
        is_tenant_admin: user.is_tenant_admin,
      })
      // 更新显示名称（租户列表应该已经加载）
      if (tenants.length > 0) {
        const tenant = tenants.find(t => t.id === user.tenant_id)
        if (tenant) {
          setTenantDisplayName(tenant.name)
        } else if (user.tenant_id) {
          setTenantDisplayName(user.tenant_id)
        }
      } else if (user.tenant_id) {
        // 如果租户列表还没加载，先显示ID，等租户列表加载后会自动更新
        setTenantDisplayName(user.tenant_id)
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取用户信息失败')
    }
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      if (id) {
        const updateData: UserUpdate = {
          username: values.username,
          phone: values.phone,
          status: values.status,
          is_tenant_admin: values.is_tenant_admin,
        }
        if (values.password) {
          updateData.password = values.password
        }
        // 租户管理员不能修改tenant_id，系统管理员可以
        if (currentUser?.is_system_admin && values.tenant_id) {
          updateData.tenant_id = values.tenant_id
        }
        await userApi.update(id, updateData)
        message.success('更新成功')
      } else {
        // 租户管理员自动使用其tenant_id
        const tenantId = currentUser?.is_system_admin ? values.tenant_id : (currentUser?.tenant_id || values.tenant_id)
        const createData: UserCreate = {
          tenant_id: tenantId,
          username: values.username,
          phone: values.phone,
          password: values.password,
          is_tenant_admin: false,
        }
        await userApi.create(createData)
        message.success('创建成功')
      }
      navigate('/users')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 600 }}>
      <h2>{id ? '编辑用户' : '新建用户'}</h2>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{ status: 'active' }}
      >
        {currentUser?.is_system_admin && (
          <Form.Item
            label="租户"
            name="tenant_id"
            rules={[{ required: true, message: '请选择租户' }]}
          >
            <Select
              placeholder="请选择租户"
              disabled={!!id}
              options={tenants.map((t) => ({ label: t.name, value: t.id }))}
            />
          </Form.Item>
        )}
        {!currentUser?.is_system_admin && currentUser?.tenant_id && (
          <Form.Item label="租户">
            <Form.Item name="tenant_id" noStyle hidden>
              <Input type="hidden" />
            </Form.Item>
            <Input disabled value={tenantDisplayName} readOnly />
          </Form.Item>
        )}

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
            // {
            //   pattern: /^1[3-9]\d{9}$/,
            //   message: '请输入有效的11位手机号',
            // },
          ]}
        >
          <Input placeholder="请输入手机号（必填，用作登录账号）" />
        </Form.Item>

        {!id && (
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
        )}

        {id && (
          <Form.Item
            label="新密码"
            name="password"
            rules={[
              { min: 6, message: '密码至少6个字符' },
              { max: 72, message: '密码不能超过72个字符' },
            ]}
          >
            <Input.Password placeholder="留空则不修改密码" />
          </Form.Item>
        )}

        <Form.Item label="状态" name="status">
          <Select>
            <Select.Option value="active">启用</Select.Option>
            <Select.Option value="frozen">冻结</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              {id ? '更新' : '创建'}
            </Button>
            <Button onClick={() => navigate('/users')}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  )
}

export default UserForm

