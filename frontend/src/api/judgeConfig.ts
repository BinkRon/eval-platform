import client from './client'
import type { JudgeConfig, JudgeConfigUpdate } from '../types/judgeConfig'

export type { ChecklistItem, EvalDimension, JudgeConfig, JudgeConfigUpdate } from '../types/judgeConfig'

export const judgeConfigApi = {
  get: (projectId: string) =>
    client.get<JudgeConfig | null>(`/projects/${projectId}/judge-config`).then((r) => r.data),
  update: (projectId: string, data: JudgeConfigUpdate) =>
    client.put<JudgeConfig>(`/projects/${projectId}/judge-config`, data).then((r) => r.data),
}
