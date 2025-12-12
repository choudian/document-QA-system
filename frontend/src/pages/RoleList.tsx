import { useState, useEffect } from 'react'
import { Table, Button, Space, Tag, message, Popconfirm, Select, Modal, Checkbox } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SafetyOutlined, UserOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { roleApi, Role } from '@/api/role'
import { permissionApi, Permission } from '@/api/permission'
import { userApi, User } from '@/api/user'
import { tenantApi } from '@/api/tenant'
import { useCurrentUser } from '@/hooks/useCurrentUser'
import dayjs from 'dayjs'

const RoleList = () => {
  const [roles, setRoles] = useState<Role[]>([])
  const [selectedTenantId, setSelectedTenantId] = useState<string>('')  // 用于创建角色时传递tenant_id
  const currentUser = useCurrentUser()
  const [loading, setLoading] = useState(false)
  const [permissionModalVisible, setPermissionModalVisible] = useState(false)
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [allPermissions, setAllPermissions] = useState<Permission[]>([])
  const [selectedPermissionIds, setSelectedPermissionIds] = useState<string[]>([])
  const [permissionLoading, setPermissionLoading] = useState(false)
  const [userModalVisible, setUserModalVisible] = useState(false)
  const [allUsers, setAllUsers] = useState<User[]>([])
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([])
  const [userLoading, setUserLoading] = useState(false)
  const [userSelectTenantId, setUserSelectTenantId] = useState<string>('')
  const [tenants, setTenants] = useState<any[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    // 非系统管理员自动使用其tenant_id（用于创建角色时）
    if (currentUser && !currentUser.is_system_admin && currentUser.tenant_id) {
      setSelectedTenantId(currentUser.tenant_id)
    }
  }, [currentUser])

  const fetchRoles = async () => {
    setLoading(true)
    try {
      // 后端会根据当前用户自动处理：
      // - 系统管理员：tenant_id=None，只查询系统级角色（tenant_id IS NULL）
      // - 非系统管理员：tenant_id=当前用户的tenant_id，只查询该租户的角色
      const data = await roleApi.getList({})
      setRoles(data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取角色列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchPermissions = async () => {
    setPermissionLoading(true)
    try {
      // 后端会根据当前用户自动处理权限过滤
      const data = await permissionApi.getList({})
      setAllPermissions(data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取权限列表失败')
    } finally {
      setPermissionLoading(false)
    }
  }

  const fetchUsers = async () => {
    // 非系统管理员自动使用其tenant_id
    // 系统管理员在分配用户时，需要根据角色所属租户来获取用户列表
    // 这里暂时不获取，在打开分配用户弹窗时再获取
    if (!currentUser?.tenant_id && !currentUser?.is_system_admin) return
    
    setUserLoading(true)
    try {
      // 非系统管理员使用其tenant_id
      const tenantId = currentUser?.tenant_id
      if (tenantId) {
        const data = await userApi.getList(tenantId)
        setAllUsers(data)
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取用户列表失败')
    } finally {
      setUserLoading(false)
    }
  }

  useEffect(() => {
    if (currentUser) {
      fetchRoles()
      fetchPermissions()
      // 非系统管理员自动获取用户列表
      if (!currentUser.is_system_admin && currentUser.tenant_id) {
        fetchUsers()
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser])

  const handleDelete = async (id: string) => {
    try {
      await roleApi.delete(id)
      message.success('删除成功')
      fetchRoles()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const handleStatusChange = async (id: string, status: boolean) => {
    try {
      await roleApi.updateStatus(id, status)
      message.success(status ? '已启用' : '已停用')
      fetchRoles()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const handleAssignPermissions = async (role: Role) => {
    setSelectedRole(role)
    setPermissionModalVisible(true)
    try {
      const permissions = await roleApi.getPermissions(role.id)
      setSelectedPermissionIds(permissions.map((p: any) => p.id))
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取权限列表失败')
    }
  }

  const handleSavePermissions = async () => {
    if (!selectedRole) return
    try {
      await roleApi.assignPermissions(selectedRole.id, {
        permission_ids: selectedPermissionIds,
      })
      message.success('权限分配成功')
      setPermissionModalVisible(false)
      setSelectedRole(null)
      setSelectedPermissionIds([])
    } catch (error: any) {
      message.error(error.response?.data?.detail || '权限分配失败')
    }
  }

  const handleAssignUsers = async (role: Role) => {
    setSelectedRole(role)
    setUserModalVisible(true)
    try {
      // 获取角色已分配的用户
      const users = await roleApi.getUsers(role.id)
      setSelectedUserIds(users.map((u: any) => u.id))
      
      // 获取可分配的用户列表
      // 系统级角色可以分配给任何租户的用户，租户级角色只能分配给本租户的用户
      if (role.tenant_id) {
        // 租户级角色：获取该租户的用户
        const data = await userApi.getList(role.tenant_id)
        setAllUsers(data)
        setUserSelectTenantId(role.tenant_id)
      } else {
        // 系统级角色：如果是系统管理员，需要选择租户；如果是租户管理员，使用其tenant_id
        if (currentUser?.is_system_admin) {
          // 系统管理员：获取租户列表，默认选择第一个租户
          const tenantsList = await tenantApi.getList({ status: true })
          setTenants(tenantsList)
          if (tenantsList.length > 0) {
            const firstTenantId = tenantsList[0].id
            setUserSelectTenantId(firstTenantId)
            const data = await userApi.getList(firstTenantId)
            setAllUsers(data)
          } else {
            setAllUsers([])
            setUserSelectTenantId('')
          }
        } else if (currentUser?.tenant_id) {
          // 租户管理员使用其tenant_id
          setTenants([])
          setUserSelectTenantId(currentUser.tenant_id)
          const data = await userApi.getList(currentUser.tenant_id)
          setAllUsers(data)
        } else {
          setAllUsers([])
          setUserSelectTenantId('')
          setTenants([])
        }
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取用户列表失败')
    }
  }

  const handleUserTenantChange = async (tenantId: string) => {
    if (!selectedRole) return
    setUserSelectTenantId(tenantId)
    setUserLoading(true)
    try {
      const data = await userApi.getList(tenantId)
      setAllUsers(data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取用户列表失败')
    } finally {
      setUserLoading(false)
    }
  }

  const handleSaveUsers = async () => {
    if (!selectedRole) return
    try {
      await roleApi.assignUsers(selectedRole.id, {
        user_ids: selectedUserIds,
      })
      message.success('用户分配成功')
      setUserModalVisible(false)
      setSelectedRole(null)
      setSelectedUserIds([])
    } catch (error: any) {
      message.error(error.response?.data?.detail || '用户分配失败')
    }
  }

  const columns = [
    {
      title: '角色名称',
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
      render: (_: any, record: Role) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => navigate(`/roles/${record.id}/edit`)}
          >
            编辑
          </Button>
          <Button
            type="link"
            icon={<SafetyOutlined />}
            onClick={() => handleAssignPermissions(record)}
          >
            分配权限
          </Button>
          <Button
            type="link"
            icon={<UserOutlined />}
            onClick={() => handleAssignUsers(record)}
          >
            分配用户
          </Button>
          <Button
            type="link"
            onClick={() => handleStatusChange(record.id, !record.status)}
          >
            {record.status ? '停用' : '启用'}
          </Button>
          <Popconfirm
            title="确定要删除这个角色吗？"
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
        <h2>角色管理</h2>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              // 系统管理员可以创建系统级角色（tenant_id=null）或租户级角色
              // 非系统管理员只能创建租户级角色（使用其tenant_id）
              const tenantId = currentUser?.is_system_admin ? null : (currentUser?.tenant_id || null)
              navigate(`/roles/new${tenantId ? `?tenant_id=${tenantId}` : ''}`)
            }}
            disabled={!currentUser?.is_system_admin && !currentUser?.tenant_id}
          >
            新建角色
          </Button>
        </Space>
      </div>
      <Table
        columns={columns}
        dataSource={roles}
        rowKey="id"
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />

      <Modal
        title={`为角色"${selectedRole?.name}"分配权限`}
        open={permissionModalVisible}
        onOk={handleSavePermissions}
        onCancel={() => {
          setPermissionModalVisible(false)
          setSelectedRole(null)
          setSelectedPermissionIds([])
        }}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <div style={{ maxHeight: 400, overflowY: 'auto' }}>
          {permissionLoading ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>加载中...</div>
          ) : (
            <Checkbox.Group
              value={selectedPermissionIds}
              onChange={(values) => setSelectedPermissionIds(values as string[])}
              style={{ width: '100%' }}
            >
              {allPermissions.map((permission) => (
                <div key={permission.id} style={{ marginBottom: 8 }}>
                  <Checkbox value={permission.id}>
                    <span style={{ marginRight: 8 }}>
                      <code style={{ background: '#f5f5f5', padding: '2px 6px', borderRadius: 3 }}>
                        {permission.code}
                      </code>
                    </span>
                    {permission.name}
                  </Checkbox>
                </div>
              ))}
            </Checkbox.Group>
          )}
        </div>
      </Modal>

      <Modal
        title={`为角色"${selectedRole?.name}"分配用户`}
        open={userModalVisible}
        onOk={handleSaveUsers}
        onCancel={() => {
          setUserModalVisible(false)
          setSelectedRole(null)
          setSelectedUserIds([])
          setUserSelectTenantId('')
          setTenants([])
        }}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <div>
          {selectedRole && !selectedRole.tenant_id && currentUser?.is_system_admin && tenants.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <span style={{ marginRight: 8 }}>选择租户：</span>
              <Select
                style={{ width: 200 }}
                value={userSelectTenantId}
                onChange={handleUserTenantChange}
                options={tenants.map((t) => ({ label: t.name, value: t.id }))}
              />
            </div>
          )}
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {userLoading ? (
              <div style={{ textAlign: 'center', padding: '20px' }}>加载中...</div>
            ) : allUsers.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                {!userSelectTenantId ? '请先选择租户' : '该租户下暂无用户'}
              </div>
            ) : (
              <Checkbox.Group
                value={selectedUserIds}
                onChange={(values) => setSelectedUserIds(values as string[])}
                style={{ width: '100%' }}
              >
                {allUsers.map((user) => (
                  <div key={user.id} style={{ marginBottom: 8 }}>
                    <Checkbox value={user.id}>
                      <span style={{ marginRight: 8 }}>{user.username}</span>
                      <span style={{ color: '#999' }}>({user.phone})</span>
                    </Checkbox>
                  </div>
                ))}
              </Checkbox.Group>
            )}
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default RoleList

