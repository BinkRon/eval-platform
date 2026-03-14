import { Layout, Menu } from 'antd'
import { ProjectOutlined, SettingOutlined } from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { SEMANTIC_COLORS } from '../theme/themeConfig'

const { Sider, Content } = Layout

const SIDER_WIDTH = 232

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()

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
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
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
          <span style={{ fontSize: 15, fontWeight: 600, color: '#1c1c1a' }}>
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
      </Sider>

      <Layout style={{ marginLeft: SIDER_WIDTH }}>
        <Content style={{ padding: '24px 28px' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
