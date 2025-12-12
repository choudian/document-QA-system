import { useState, useEffect } from 'react'
import { Form, Input, Button, Switch, Space, message } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import { tenantApi, TenantCreate, TenantUpdate } from '@/api/tenant'

const { TextArea } = Input

const TenantForm = () => {
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (id) {
      fetchTenant()
    }
  }, [id])

  const fetchTenant = async () => {
    try {
      const tenant = await tenantApi.getById(id!)
      form.setFieldsValue({
        code: tenant.code,
        name: tenant.name,
        description: tenant.description,
        status: tenant.status,
      })
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取租户信息失败')
    }
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      if (id) {
        const updateData: TenantUpdate = {
          code: values.code,
          name: values.name,
          description: values.description,
          status: values.status,
        }
        await tenantApi.update(id, updateData)
        message.success('更新成功')
        navigate('/tenants')
      } else {
        // 创建租户
        const createData: TenantCreate = {
          code: values.code,
          name: values.name,
          description: values.description,
        }
        await tenantApi.create(createData)
        message.success('租户创建成功')
        navigate('/tenants')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 600 }}>
      <h2>{id ? '编辑租户' : '新建租户'}</h2>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{ status: true }}
      >
        <Form.Item
          label="租户编码"
          name="code"
          rules={[
            { required: true, message: '请输入租户编码' },
            { max: 50, message: '租户编码不能超过50个字符' },
            { pattern: /^[a-zA-Z0-9_-]+$/, message: '租户编码只能包含字母、数字、下划线和连字符' },
          ]}
        >
          <Input placeholder="请输入租户编码（字母、数字、下划线、连字符）" />
        </Form.Item>

        <Form.Item
          label="租户名称"
          name="name"
          rules={[
            { required: true, message: '请输入租户名称' },
            { max: 100, message: '租户名称不能超过100个字符' },
          ]}
        >
          <Input placeholder="请输入租户名称" />
        </Form.Item>

        <Form.Item
          label="描述"
          name="description"
          rules={[{ max: 500, message: '描述不能超过500个字符' }]}
        >
          <TextArea rows={4} placeholder="请输入描述" />
        </Form.Item>

        {id && (
          <Form.Item label="状态" name="status" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
        )}

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              {id ? '更新' : '创建'}
            </Button>
            <Button onClick={() => navigate('/tenants')}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  )
}

export default TenantForm

