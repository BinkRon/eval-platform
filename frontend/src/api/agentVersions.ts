import client from './client'
import type { AgentVersion, AgentVersionCreate, AgentVersionUpdate } from '../types/agentVersion'

export type { AgentVersion, AgentVersionCreate, AgentVersionUpdate }

export const agentVersionApi = {
  list: (projectId: string) =>
    client.get<AgentVersion[]>(`/projects/${projectId}/agent-versions`).then((r) => r.data),
  create: (projectId: string, data: AgentVersionCreate) =>
    client.post<AgentVersion>(`/projects/${projectId}/agent-versions`, data).then((r) => r.data),
  update: (projectId: string, id: string, data: AgentVersionUpdate) =>
    client.put<AgentVersion>(`/projects/${projectId}/agent-versions/${id}`, data).then((r) => r.data),
  delete: (projectId: string, id: string) =>
    client.delete(`/projects/${projectId}/agent-versions/${id}`),
  test: (projectId: string, id: string) =>
    client.post<{ status: string; reply?: string; error?: string }>(`/projects/${projectId}/agent-versions/${id}/test`).then((r) => r.data),
}
