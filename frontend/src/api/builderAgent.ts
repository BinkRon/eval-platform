import client from './client'
import type { BuilderChatRequest, BuilderChatResponse } from '../types/builderAgent'

export const builderAgentApi = {
  chat: (projectId: string, data: BuilderChatRequest) =>
    client
      .post<BuilderChatResponse>(`/projects/${projectId}/builder-agent/chat`, data, {
        timeout: 120000, // LLM calls may take longer than the default 30s
      })
      .then((r) => r.data),
}
