import { Layout, Menu, Button } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  HomeOutlined,
  TeamOutlined,
  UserOutlined,
  SafetyOutlined,
  UsergroupAddOutlined,
} from '@ant-design/icons'
import { ReactNode, useState, useEffect } from 'react'
import { meApi, Permission } from '@/api/me'
import { useCurrentUser } from '@/hooks/useCurrentUser'

const { Header, Sider } = Layout

interface AppLayoutProps {
  children: ReactNode
}

const AppLayout = ({ children }: AppLayoutProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const [permissions, setPermissions] = useState<Permission[]>([])
  const currentUser = useCurrentUser()
  const isSystemAdmin = currentUser?.is_system_admin || false

  useEffect(() => {
    fetchPermissions()
  }, [])

  const fetchPermissions = async () => {
    try {
      const perms = await meApi.getPermissions()
      setPermissions(perms)
    } catch (error) {
      console.error('获取权限信息失败:', error)
    }
  }

  // 检查是否有菜单权限
  const hasMenuPermission = (permissionCode: string) => {
    // 所有用户（包括系统管理员）都通过权限列表判断
    return permissions.some(p => p.code === permissionCode && p.type === 'menu')
  }

  const allMenuItems = [
    {
      key: '/tenants',
      icon: <TeamOutlined />,
      label: '租户管理',
      permission: 'system:tenant:read',
    },
    {
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
      permission: 'system:user:read',
    },
    {
      key: '/permissions',
      icon: <SafetyOutlined />,
      label: '权限管理',
      permission: 'system:permission:read',
    },
    {
      key: '/roles',
      icon: <UsergroupAddOutlined />,
      label: '角色管理',
      permission: 'system:role:read',
    },
  ]

  // 根据权限过滤菜单
  const menuItems = allMenuItems
    .filter(item => hasMenuPermission(item.permission))
    .map(({ permission, ...item }) => item) // 移除permission字段

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login', { replace: true })
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          background: '#001529',
          justifyContent: 'space-between',
          padding: '0 16px',
        }}
      >
        <div style={{ color: '#fff', fontSize: '20px', fontWeight: 'bold' }}>
          智能文档问答系统
        </div>
        <Button type="primary" danger onClick={handleLogout}>
          退出登录
        </Button>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname.split('/')[1] ? `/${location.pathname.split('/')[1]}` : '/']}
            items={menuItems}
            onClick={handleMenuClick}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Layout style={{ padding: '0 24px 24px' }}>
          {children}
        </Layout>
      </Layout>
    </Layout>
  )
}

export default AppLayout

