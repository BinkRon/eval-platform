import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { testCaseApi } from '../api/testCases'
import type { TestCaseCreate, TestCaseUpdate } from '../types/testCase'

export function useTestCases(projectId: string) {
  return useQuery({
    queryKey: ['test-cases', projectId],
    queryFn: () => testCaseApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useCreateTestCase(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: TestCaseCreate) => testCaseApi.create(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['test-cases', projectId] }),
  })
}

export function useUpdateTestCase(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TestCaseUpdate }) => testCaseApi.update(projectId, id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['test-cases', projectId] }),
  })
}

export function useDeleteTestCase(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => testCaseApi.delete(projectId, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['test-cases', projectId] }),
  })
}
