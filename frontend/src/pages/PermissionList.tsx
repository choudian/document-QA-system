import { useState, useEffect } from 'react'
import { Table, Button, Space, Tag, message, Popconfirm, Select, Input } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { permissionApi, Permission } from '@/api/permission'
import { useCurrentUser } from '@/hooks/useCurrentUser'
import dayjs from 'dayjs'

const { Option } = Select

const PermissionList = () => {
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [loading, setLoading] = useState(false)
  const currentUser = useCurrentUser()
  const [filters, setFilters] = useState<{
    module?: string
    type?: string
    status?: boolean
  }>({})
  const navigate = useNavigate()

  const fetchPermissions = async () => {
    setLoading(true)
    try {
      // 租户管理员会自动使用其tenant_id，系统管理员不传tenant_id
      const data = await permissionApi.getList({
        ...filters,
        limit: 1000, // 获取所有权限
      })
      setPermissions(data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取权限列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPermissions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.module, filters.type, filters.status])

  const handleDelete = async (id: string) => {
    try {
      await permissionApi.delete(id)
      message.success('删除成功')
      fetchPermissions()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const handleStatusChange = async (id: string, status: boolean) => {
    try {
      await permissionApi.updateStatus(id, status)
      message.success(status ? '已启用' : '已停用')
      fetchPermissions()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      menu: 'blue',
      api: 'green',
      button: 'orange',
      tab: 'purple',
    }
    return colors[type] || 'default'
  }

  const getTypeText = (type: string) => {
    const texts: Record<string, string> = {
      menu: '菜单',
      api: '接口',
      button: '按钮',
      tab: 'Tab页',
    }
    return texts[type] || type
  }

  const columns = [
    {
      title: '权限码',
      dataIndex: 'code',
      key: 'code',
      width: 200,
      render: (text: string) => <code style={{ background: '#f5f5f5', padding: '2px 6px', borderRadius: 3 }}>{text}</code>,
    },
    {
      title: '权限名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: string) => (
        <Tag color={getTypeColor(type)}>{getTypeText(type)}</Tag>
      ),
    },
    {
      title: '所属模块',
      dataIndex: 'module',
      key: 'module',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: boolean) => (
        <Tag color={status ? 'green' : 'red'}>
          {status ? '启用' : '停用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: Permission) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/permissions/${record.id}/edit`)}
          >
            编辑
          </Button>
          <Button
            type="link"
            onClick={() => handleStatusChange(record.id, !record.status)}
          >
            {record.status ? '停用' : '启用'}
          </Button>
          <Popconfirm
            title="确定要删除这个权限吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 获取所有模块列表（去重）
  const modules = Array.from(new Set(permissions.map(p => p.module))).sort()

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>权限管理</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/permissions/new')}
        >
          新建权限
        </Button>
      </div>

      <div style={{ marginBottom: 16, display: 'flex', gap: 16 }}>
        <Select
          placeholder="筛选模块"
          allowClear
          style={{ width: 150 }}
          value={filters.module}
          onChange={(value) => setFilters({ ...filters, module: value })}
        >
          {modules.map(module => (
            <Option key={module} value={module}>{module}</Option>
          ))}
        </Select>
        <Select
          placeholder="筛选类型"
          allowClear
          style={{ width: 150 }}
          value={filters.type}
          onChange={(value) => setFilters({ ...filters, type: value })}
        >
          <Option value="menu">菜单</Option>
          <Option value="api">接口</Option>
          <Option value="button">按钮</Option>
          <Option value="tab">Tab页</Option>
        </Select>
        <Select
          placeholder="筛选状态"
          allowClear
          style={{ width: 150 }}
          value={filters.status}
          onChange={(value) => setFilters({ ...filters, status: value })}
        >
          <Option value={true}>启用</Option>
          <Option value={false}>停用</Option>
        </Select>
        <Button
          icon={<SearchOutlined />}
          onClick={fetchPermissions}
        >
          刷新
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={permissions}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />
    </div>
  )
}

export default PermissionList

