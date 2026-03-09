import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { modelConfigApi, modelOptionsApi } from '../api/modelConfig'
import type { ModelConfigUpdate } from '../types/modelConfig'

export function useModelConfig(projectId: string) {
  return useQuery({
    queryKey: ['model-config', projectId],
    queryFn: () => modelConfigApi.get(projectId),
    enabled: !!projectId,
  })
}

export function useUpdateModelConfig(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ModelConfigUpdate) => modelConfigApi.update(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['model-config', projectId] })
      qc.invalidateQueries({ queryKey: ['projects', projectId, 'readiness'] })
    },
  })
}

export function useModelOptions() {
  return useQuery({ queryKey: ['model-options'], queryFn: modelOptionsApi.list })
}
