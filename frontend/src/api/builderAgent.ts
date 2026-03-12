import client from './client'
import type {
  ApplyConfigRequest,
  ApplyConfigResponse,
  BuilderChatRequest,
  BuilderChatResponse,
} from '../types/builderAgent'

export const builderAgentApi = {
  chat: (projectId: string, data: BuilderChatRequest) =>
    client
      .post<BuilderChatResponse>(`/projects/${projectId}/builder-agent/chat`, data, {
        timeout: 120000, // LLM calls may take longer than the default 30s
      })
      .then((r) => r.data),

  applyConfig: (projectId: string, data: ApplyConfigRequest) =>
    client
      .post<ApplyConfigResponse>(`/projects/${projectId}/builder-agent/apply-config`, data)
      .then((r) => r.data),
}
