import { Button, Card, Form, Input, message } from 'antd'
import { LockOutlined, MailOutlined, UserOutlined } from '@ant-design/icons'
import { useNavigate, Link } from 'react-router-dom'
import { useRegister } from '../hooks/useAuth'
import { SEMANTIC_COLORS } from '../theme/themeConfig'

export default function RegisterPage() {
  const navigate = useNavigate()
  const registerMutation = useRegister()

  const onFinish = async (values: { username: string; password: string; email?: string }) => {
    try {
      await registerMutation.mutateAsync(values)
      message.success('注册成功，请登录')
      navigate('/login', { replace: true })
    } catch {
      // Error already handled by interceptor
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: SEMANTIC_COLORS.pageBg,
      }}
    >
      <Card style={{ width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              background: SEMANTIC_COLORS.brandPrimary,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 22,
              fontWeight: 700,
              marginBottom: 12,
            }}
          >
            A
          </div>
          <h2 style={{ margin: 0 }}>注册账号</h2>
        </div>

        <Form onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }, { min: 2, message: '用户名至少 2 个字符' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="email">
            <Input prefix={<MailOutlined />} placeholder="邮箱（可选）" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }, { min: 6, message: '密码至少 6 位' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) return Promise.resolve()
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={registerMutation.isPending}
              block
            >
              注册
            </Button>
          </Form.Item>
          <div style={{ textAlign: 'center' }}>
            已有账号？ <Link to="/login">返回登录</Link>
          </div>
        </Form>
      </Card>
    </div>
  )
}
