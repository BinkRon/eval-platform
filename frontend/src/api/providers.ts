import client from './client'
import type { Provider, ProviderCreate, ProviderUpdate } from '../types/provider'

export type { Provider, ProviderCreate, ProviderUpdate }

export const providerApi = {
  list: () => client.get<Provider[]>('/providers').then((r) => r.data),
  create: (data: ProviderCreate) => client.post<Provider>('/providers', data).then((r) => r.data),
  update: (id: string, data: ProviderUpdate) => client.put<Provider>(`/providers/${id}`, data).then((r) => r.data),
  delete: (id: string) => client.delete(`/providers/${id}`),
  test: (id: string) => client.post<{ status: string; error?: string }>(`/providers/${id}/test`).then((r) => r.data),
}
