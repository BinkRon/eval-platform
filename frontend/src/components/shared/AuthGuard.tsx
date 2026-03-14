import { Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import { getToken } from '../../utils/auth'
import { useCurrentUser } from '../../hooks/useAuth'

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const token = getToken()
  const { isLoading } = useCurrentUser()

  if (!token) {
    return <Navigate to="/login" replace />
  }

  if (isLoading) {
    return <Spin style={{ display: 'block', margin: '100px auto' }} />
  }

  return <>{children}</>
}
