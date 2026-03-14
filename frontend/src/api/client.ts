import axios from 'axios'
import { message } from 'antd'
import { getToken, removeToken } from '../utils/auth'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Request interceptor: attach JWT token
client.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle errors + 401 redirect
client.interceptors.response.use(
  (res) => res,
  (error) => {
    // 401: clear token and redirect to login
    if (error.response?.status === 401) {
      removeToken()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    const detail = error.response?.data?.detail
    let errorMsg = '请求失败'
    if (typeof detail === 'string') {
      errorMsg = detail
    } else if (Array.isArray(detail)) {
      errorMsg = detail
        .map((e: { loc?: string[]; msg?: string }) => {
          const field = e.loc?.slice(-1)[0] || ''
          return field ? `${field}: ${e.msg}` : e.msg || ''
        })
        .filter(Boolean)
        .join('; ') || '参数校验失败'
    }
    message.error(errorMsg)
    return Promise.reject(error)
  },
)

export default client
