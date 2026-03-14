import { Button, Layout, Menu } from 'antd'
import { LogoutOutlined, ProjectOutlined, SettingOutlined } from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { SEMANTIC_COLORS } from '../theme/themeConfig'
import { useCurrentUser, useLogout } from '../hooks/useAuth'

const { Sider, Content } = Layout

const SIDER_WIDTH = 232

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { data: user } = useCurrentUser()
  const logout = useLogout()

  const selectedKey = location.pathname.startsWith('/settings') ? '/settings/providers' : '/projects'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        width={SIDER_WIDTH}
        style={{
          position: 'fixed',
          left: 0,
          top: 0,
          height: '100vh',
          borderRight: `1px solid ${SEMANTIC_COLORS.borderDefault}`,
          overflowY: 'auto',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
          {/* Logo */}
          <div
            style={{
              padding: '20px 16px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              cursor: 'pointer',
            }}
            onClick={() => navigate('/projects')}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                background: SEMANTIC_COLORS.brandPrimary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontSize: 16,
                fontWeight: 700,
                flexShrink: 0,
              }}
            >
              A
            </div>
            <span style={{ fontSize: 15, fontWeight: 600 }}>
              Agent 评测平台
            </span>
          </div>

          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            onClick={({ key }) => navigate(key)}
            items={[
              { key: '/projects', icon: <ProjectOutlined />, label: '项目列表' },
              { key: '/settings/providers', icon: <SettingOutlined />, label: '模型管理' },
            ]}
            style={{ border: 'none', flex: 1 }}
          />

          {/* User info + logout */}
          {user && (
            <div
              style={{
                padding: '12px 16px',
                borderTop: `1px solid ${SEMANTIC_COLORS.borderDefault}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ fontSize: 13, color: SEMANTIC_COLORS.textSecondary, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.username}
              </span>
              <Button
                type="text"
                size="small"
                icon={<LogoutOutlined />}
                onClick={logout}
                title="退出登录"
              />
            </div>
          )}
        </div>
      </Sider>

      <Layout style={{ marginLeft: SIDER_WIDTH }}>
        <Content style={{ padding: '24px 28px' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
