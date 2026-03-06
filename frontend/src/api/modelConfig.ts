import client from './client'
import type { ModelConfig, ModelConfigUpdate, ModelOption } from '../types/modelConfig'

export type { ModelConfig, ModelConfigUpdate, ModelOption }

export const modelConfigApi = {
  get: (projectId: string) =>
    client.get<ModelConfig | null>(`/projects/${projectId}/model-config`).then((r) => r.data),
  update: (projectId: string, data: ModelConfigUpdate) =>
    client.put<ModelConfig>(`/projects/${projectId}/model-config`, data).then((r) => r.data),
}

export const modelOptionsApi = {
  list: () => client.get<ModelOption[]>('/providers/models').then((r) => r.data),
}
