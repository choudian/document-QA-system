import { useState, useEffect } from 'react'
import { Table, Button, Space, Tag, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { tenantApi, Tenant } from '@/api/tenant'
import dayjs from 'dayjs'

const TenantList = () => {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const fetchTenants = async () => {
    setLoading(true)
    try {
      const data = await tenantApi.getList()
      setTenants(data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取租户列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTenants()
  }, [])

  const handleDelete = async (id: string) => {
    try {
      await tenantApi.delete(id)
      message.success('删除成功')
      fetchTenants()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const handleStatusChange = async (id: string, status: boolean) => {
    try {
      await tenantApi.updateStatus(id, status)
      message.success(status ? '已启用' : '已停用')
      fetchTenants()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const columns = [
    {
      title: '租户编码',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '租户名称',
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
      title: '状态',
      dataIndex: 'status',
      key: 'status',
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
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Tenant) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/tenants/${record.id}/edit`)}
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
            title="确定要删除这个租户吗？"
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
        <h2>租户管理</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/tenants/new')}
        >
          新建租户
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={tenants}
        rowKey="id"
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />
    </div>
  )
}

export default TenantList

