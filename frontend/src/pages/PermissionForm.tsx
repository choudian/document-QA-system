import { useState, useEffect } from 'react'
import { Form, Input, Button, Select, Switch, Space, message } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import { permissionApi, PermissionCreate, PermissionUpdate } from '@/api/permission'

const { TextArea } = Input
const { Option } = Select

const PermissionForm = () => {
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (id) {
      fetchPermission()
    }
  }, [id])

  const fetchPermission = async () => {
    try {
      const permission = await permissionApi.getById(id!)
      form.setFieldsValue({
        code: permission.code,
        name: permission.name,
        description: permission.description,
        type: permission.type,
        module: permission.module,
        status: permission.status,
      })
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取权限信息失败')
    }
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      if (id) {
        const updateData: PermissionUpdate = {
          code: values.code,
          name: values.name,
          description: values.description,
          type: values.type,
          module: values.module,
          status: values.status,
        }
        await permissionApi.update(id, updateData)
        message.success('更新成功')
        navigate('/permissions')
      } else {
        const createData: PermissionCreate = {
          code: values.code,
          name: values.name,
          description: values.description,
          type: values.type,
          module: values.module,
          status: values.status ?? true,
        }
        await permissionApi.create(createData)
        message.success('权限创建成功')
        navigate('/permissions')
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
      <h2>{id ? '编辑权限' : '新建权限'}</h2>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{ status: true, type: 'api' }}
      >
        <Form.Item
          label="权限码"
          name="code"
          rules={[
            { required: true, message: '请输入权限码' },
            { max: 100, message: '权限码不能超过100个字符' },
            {
              pattern: /^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$/,
              message: '权限码格式不正确，应为 module:resource:action 格式（如：doc:file:read）',
            },
          ]}
          extra="格式：module:resource:action，例如：doc:file:read"
        >
          <Input placeholder="请输入权限码（如：doc:file:read）" />
        </Form.Item>

        <Form.Item
          label="权限名称"
          name="name"
          rules={[
            { required: true, message: '请输入权限名称' },
            { max: 100, message: '权限名称不能超过100个字符' },
          ]}
        >
          <Input placeholder="请输入权限名称" />
        </Form.Item>

        <Form.Item
          label="描述"
          name="description"
          rules={[{ max: 500, message: '描述不能超过500个字符' }]}
        >
          <TextArea rows={3} placeholder="请输入权限描述" />
        </Form.Item>

        <Form.Item
          label="权限类型"
          name="type"
          rules={[{ required: true, message: '请选择权限类型' }]}
        >
          <Select placeholder="请选择权限类型">
            <Option value="menu">菜单</Option>
            <Option value="api">接口</Option>
            <Option value="button">按钮</Option>
            <Option value="tab">Tab页</Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="所属模块"
          name="module"
          rules={[
            { required: true, message: '请输入所属模块' },
            { max: 50, message: '模块名称不能超过50个字符' },
          ]}
          extra="例如：doc（文档管理）、system（系统管理）、qa（问答）"
        >
          <Input placeholder="请输入所属模块" />
        </Form.Item>

        <Form.Item label="状态" name="status" valuePropName="checked">
          <Switch checkedChildren="启用" unCheckedChildren="停用" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              {id ? '更新' : '创建'}
            </Button>
            <Button onClick={() => navigate('/permissions')}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  )
}

export default PermissionForm

