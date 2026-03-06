import axios from 'axios'
import { message } from 'antd'

const client = axios.create({
  baseURL: '/api',
})

client.interceptors.response.use(
  (res) => res,
  (error) => {
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
