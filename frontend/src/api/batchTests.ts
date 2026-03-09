import client from './client'
import type { BatchTest, BatchTestCreate, BatchTestDetail } from '../types/batchTest'

export type { BatchTest, BatchTestCreate, TestResult, BatchTestDetail } from '../types/batchTest'

export const batchTestApi = {
  list: (projectId: string) =>
    client.get<BatchTest[]>(`/projects/${projectId}/batch-tests`).then((r) => r.data),
  create: (projectId: string, data: BatchTestCreate) =>
    client.post<BatchTest>(`/projects/${projectId}/batch-tests`, data).then((r) => r.data),
  get: (projectId: string, batchId: string) =>
    client.get<BatchTestDetail>(`/projects/${projectId}/batch-tests/${batchId}`).then((r) => r.data),
  delete: (projectId: string, batchId: string) =>
    client.delete(`/projects/${projectId}/batch-tests/${batchId}`),
}
