import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { batchTestApi, BatchTestCreate } from '../api/batchTests'

export function useBatchTests(projectId: string) {
  return useQuery({
    queryKey: ['batch-tests', projectId],
    queryFn: () => batchTestApi.list(projectId),
    enabled: !!projectId,
    refetchInterval: (query) => {
      const data = query.state.data
      const hasRunning = data?.some((b) => b.status === 'running' || b.status === 'pending')
      return hasRunning ? 3000 : false
    },
    refetchIntervalInBackground: false,
  })
}

export function useCreateBatchTest(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: BatchTestCreate) => batchTestApi.create(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['batch-tests', projectId] }),
  })
}

export function useBatchTestDetail(projectId: string, batchId: string) {
  return useQuery({
    queryKey: ['batch-test-detail', projectId, batchId],
    queryFn: () => batchTestApi.get(projectId, batchId),
    enabled: !!projectId && !!batchId,
  })
}

export function useBatchTestProgress(projectId: string, batchId: string, enabled: boolean) {
  return useQuery({
    queryKey: ['batch-test-progress', projectId, batchId],
    queryFn: () => batchTestApi.progress(projectId, batchId),
    enabled: enabled && !!projectId && !!batchId,
    refetchInterval: 3000,
    refetchIntervalInBackground: false,
    retry: 0,
  })
}
