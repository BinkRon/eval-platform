import client from './client'
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '../types/auth'

export const authApi = {
  login: (data: LoginRequest) =>
    client.post<TokenResponse>('/auth/login', data).then((r) => r.data),

  register: (data: RegisterRequest) =>
    client.post<User>('/auth/register', data).then((r) => r.data),

  me: () => client.get<User>('/auth/me').then((r) => r.data),
}
