import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { judgeConfigApi } from '../api/judgeConfig'
import type { JudgeConfigUpdate } from '../types/judgeConfig'

export function useJudgeConfig(projectId: string) {
  return useQuery({
    queryKey: ['judge-config', projectId],
    queryFn: () => judgeConfigApi.get(projectId),
    enabled: !!projectId,
  })
}

export function useUpdateJudgeConfig(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: JudgeConfigUpdate) => judgeConfigApi.update(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['judge-config', projectId] })
      qc.invalidateQueries({ queryKey: ['projects', projectId, 'readiness'] })
    },
  })
}
