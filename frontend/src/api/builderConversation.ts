import client from './client'
import type { BuilderConversation } from '../types/builderConversation'

export const builderConversationApi = {
  get: (projectId: string) =>
    client
      .get<BuilderConversation>(`/projects/${projectId}/builder-conversation`)
      .then((r) => r.data),
  appendMessage: (projectId: string, message: { role: 'user' | 'assistant'; content: string }) =>
    client
      .post<BuilderConversation>(`/projects/${projectId}/builder-conversation/messages`, {
        message,
      })
      .then((r) => r.data),
  clear: (projectId: string) =>
    client
      .delete<BuilderConversation>(`/projects/${projectId}/builder-conversation/messages`)
      .then((r) => r.data),
}
