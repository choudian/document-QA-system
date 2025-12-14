import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import AppLayout from './components/Layout/AppLayout'
import DefaultRoute from './components/DefaultRoute'
import TenantList from './pages/TenantList'
import TenantForm from './pages/TenantForm'
import UserList from './pages/UserList'
import UserForm from './pages/UserForm'
import PermissionList from './pages/PermissionList'
import PermissionForm from './pages/PermissionForm'
import RoleList from './pages/RoleList'
import RoleForm from './pages/RoleForm'
import Login from './pages/Login'
import ConfigPage from './pages/ConfigPage'
import AuditLogPage from './pages/AuditLogPage'
import DocumentList from './pages/DocumentList'
import './App.css'

const { Content } = Layout

const RequireAuth = ({ children }: { children: JSX.Element }) => {
  const token = localStorage.getItem('token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <AppLayout>
                <Content style={{ padding: '24px', minHeight: '100vh' }}>
                  <Routes>
                    <Route path="/" element={<DefaultRoute />} />
                    <Route path="/tenants" element={<TenantList />} />
                    <Route path="/tenants/new" element={<TenantForm />} />
                    <Route path="/tenants/:id/edit" element={<TenantForm />} />
                    <Route path="/users" element={<UserList />} />
                    <Route path="/users/new" element={<UserForm />} />
                    <Route path="/users/:id/edit" element={<UserForm />} />
                    <Route path="/permissions" element={<PermissionList />} />
                    <Route path="/permissions/new" element={<PermissionForm />} />
                    <Route path="/permissions/:id/edit" element={<PermissionForm />} />
                    <Route path="/roles" element={<RoleList />} />
                    <Route path="/roles/new" element={<RoleForm />} />
                    <Route path="/roles/:id/edit" element={<RoleForm />} />
                    <Route path="/configs" element={<ConfigPage />} />
                    <Route path="/audit-logs" element={<AuditLogPage />} />
                    <Route path="/documents" element={<DocumentList />} />
                  </Routes>
                </Content>
              </AppLayout>
            </RequireAuth>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App

