import { useState, useEffect } from 'react'
import { Table, Button, Space, Tag, message, Popconfirm, Select } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { userApi, User } from '@/api/user'
import { tenantApi, Tenant } from '@/api/tenant'
import { useCurrentUser } from '@/hooks/useCurrentUser'
import dayjs from 'dayjs'

const UserList = () => {
  const [users, setUsers] = useState<User[]>([])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [selectedTenantId, setSelectedTenantId] = useState<string>('')
  const currentUser = useCurrentUser()
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    // 如果是租户管理员，自动使用其tenant_id
    if (currentUser && !currentUser.is_system_admin && currentUser.tenant_id) {
      setSelectedTenantId(currentUser.tenant_id)
    }
  }, [currentUser])

  const fetchTenants = async () => {
    try {
      const data = await tenantApi.getList()
      setTenants(data)
      // 只有系统管理员才需要选择租户
      if (currentUser?.is_system_admin && data.length > 0 && !selectedTenantId) {
        setSelectedTenantId(data[0].id)
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取租户列表失败')
    }
  }

  const fetchUsers = async () => {
    // 租户管理员自动使用其tenant_id，系统管理员需要选择租户
    const tenantId = currentUser?.is_system_admin ? selectedTenantId : (currentUser?.tenant_id || selectedTenantId)
    if (!tenantId) return
    setLoading(true)
    try {
      const data = await userApi.getList(tenantId)
      setUsers(data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (currentUser?.is_system_admin) {
      fetchTenants()
    }
  }, [currentUser])

  useEffect(() => {
    if (currentUser) {
      const tenantId = currentUser.is_system_admin ? selectedTenantId : (currentUser.tenant_id || selectedTenantId)
      if (tenantId) {
        fetchUsers()
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTenantId, currentUser])

  const handleDelete = async (id: string) => {
    try {
      await userApi.delete(id)
      message.success('删除成功')
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const handleStatusChange = async (id: string, status: string) => {
    try {
      await userApi.updateStatus(id, status)
      message.success(status === 'active' ? '已启用' : '已冻结')
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '启用' : '冻结'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: User) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/users/${record.id}/edit`)}
          >
            编辑
          </Button>
          <Button
            type="link"
            onClick={() =>
              handleStatusChange(record.id, record.status === 'active' ? 'frozen' : 'active')
            }
          >
            {record.status === 'active' ? '冻结' : '启用'}
          </Button>
          <Popconfirm
            title="确定要删除这个用户吗？"
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

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>用户管理</h2>
        <Space>
          {currentUser?.is_system_admin && (
            <Select
              style={{ width: 200 }}
              placeholder="选择租户"
              value={selectedTenantId}
              onChange={setSelectedTenantId}
              options={tenants.map((t) => ({ label: t.name, value: t.id }))}
            />
          )}
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              // 系统管理员可以在表单中选择租户，非系统管理员使用其tenant_id
              const tenantId = currentUser?.is_system_admin ? selectedTenantId : (currentUser?.tenant_id || selectedTenantId)
              navigate(`/users/new${tenantId ? `?tenant_id=${tenantId}` : ''}`)
            }}
            disabled={!currentUser?.is_system_admin && !currentUser?.tenant_id}
          >
            新建用户
          </Button>
        </Space>
      </div>
      {(selectedTenantId || currentUser?.tenant_id) ? (
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      ) : (
        <div style={{ textAlign: 'center', padding: '50px 0', color: '#999' }}>
          请先选择租户
        </div>
      )}
    </div>
  )
}

export default UserList

