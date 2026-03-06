import { Layout, Menu } from 'antd'
import { ProjectOutlined, SettingOutlined } from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const { Header, Content } = Layout

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  const selectedKey = location.pathname.startsWith('/settings') ? '/settings/providers' : '/projects'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{ color: '#fff', fontSize: 18, fontWeight: 600, marginRight: 40, whiteSpace: 'nowrap' }}>
          Agent 评测平台
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[selectedKey]}
          onClick={({ key }) => navigate(key)}
          items={[
            { key: '/projects', icon: <ProjectOutlined />, label: '项目列表' },
            { key: '/settings/providers', icon: <SettingOutlined />, label: '模型管理' },
          ]}
          style={{ flex: 1 }}
        />
      </Header>
      <Content style={{ padding: 24 }}>
        <Outlet />
      </Content>
    </Layout>
  )
}
