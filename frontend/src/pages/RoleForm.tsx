import { useState, useEffect } from 'react'
import { Form, Input, Button, Switch, Space, message, Select } from 'antd'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { roleApi, RoleCreate, RoleUpdate } from '@/api/role'
import { tenantApi, Tenant } from '@/api/tenant'

const { TextArea } = Input
const { Option } = Select

const RoleForm = () => {
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [tenants, setTenants] = useState<Tenant[]>([])
  const tenantIdFromQuery = searchParams.get('tenant_id')

  useEffect(() => {
    fetchTenants()
    if (id) {
      fetchRole()
    } else if (tenantIdFromQuery) {
      form.setFieldsValue({ tenant_id: tenantIdFromQuery })
    }
  }, [id, tenantIdFromQuery])

  const fetchTenants = async () => {
    try {
      const data = await tenantApi.getList()
      setTenants(data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取租户列表失败')
    }
  }

  const fetchRole = async () => {
    try {
      const role = await roleApi.getById(id!)
      form.setFieldsValue({
        tenant_id: role.tenant_id,
        name: role.name,
        description: role.description,
        status: role.status,
      })
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取角色信息失败')
    }
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      if (id) {
        const updateData: RoleUpdate = {
          name: values.name,
          description: values.description,
          status: values.status,
        }
        await roleApi.update(id, updateData)
        message.success('更新成功')
        navigate('/roles')
      } else {
        const createData: RoleCreate = {
          tenant_id: values.tenant_id,
          name: values.name,
          description: values.description,
          status: values.status ?? true,
        }
        await roleApi.create(createData)
        message.success('角色创建成功')
        navigate('/roles')
      }
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      if (Array.isArray(detail)) {
        message.error(detail.map((d: any) => d?.msg || '').filter(Boolean).join('; ') || '操作失败')
      } else if (typeof detail === 'string') {
        message.error(detail)
      } else {
        message.error('操作失败')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 600 }}>
      <h2>{id ? '编辑角色' : '新建角色'}</h2>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{ status: true }}
      >
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

        <Form.Item
          label="角色名称"
          name="name"
          rules={[
            { required: true, message: '请输入角色名称' },
            { max: 100, message: '角色名称不能超过100个字符' },
          ]}
        >
          <Input placeholder="请输入角色名称" />
        </Form.Item>

        <Form.Item
          label="描述"
          name="description"
          rules={[{ max: 500, message: '描述不能超过500个字符' }]}
        >
          <TextArea rows={3} placeholder="请输入角色描述" />
        </Form.Item>

        <Form.Item label="状态" name="status" valuePropName="checked">
          <Switch checkedChildren="启用" unCheckedChildren="停用" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              {id ? '更新' : '创建'}
            </Button>
            <Button onClick={() => navigate('/roles')}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  )
}

export default RoleForm

