import client from './client'
import type { TestCase, TestCaseCreate, TestCaseUpdate } from '../types/testCase'

export type { TestCase, TestCaseCreate, TestCaseUpdate }

export const testCaseApi = {
  list: (projectId: string) =>
    client.get<TestCase[]>(`/projects/${projectId}/test-cases`).then((r) => r.data),
  create: (projectId: string, data: TestCaseCreate) =>
    client.post<TestCase>(`/projects/${projectId}/test-cases`, data).then((r) => r.data),
  update: (projectId: string, id: string, data: TestCaseUpdate) =>
    client.put<TestCase>(`/projects/${projectId}/test-cases/${id}`, data).then((r) => r.data),
  delete: (projectId: string, id: string) =>
    client.delete(`/projects/${projectId}/test-cases/${id}`),
}
