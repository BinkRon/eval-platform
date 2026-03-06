import client from './client'
import type { BatchTest, BatchTestCreate, BatchTestProgress, BatchTestDetail } from '../types/batchTest'

export type { BatchTest, BatchTestCreate, BatchTestProgress, TestResult, BatchTestDetail } from '../types/batchTest'

export const batchTestApi = {
  list: (projectId: string) =>
    client.get<BatchTest[]>(`/projects/${projectId}/batch-tests`).then((r) => r.data),
  create: (projectId: string, data: BatchTestCreate) =>
    client.post<BatchTest>(`/projects/${projectId}/batch-tests`, data).then((r) => r.data),
  get: (projectId: string, batchId: string) =>
    client.get<BatchTestDetail>(`/projects/${projectId}/batch-tests/${batchId}`).then((r) => r.data),
  progress: (projectId: string, batchId: string) =>
    client.get<BatchTestProgress>(`/projects/${projectId}/batch-tests/${batchId}/progress`).then((r) => r.data),
}
