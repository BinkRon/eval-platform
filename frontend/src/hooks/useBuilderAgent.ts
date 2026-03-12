import { useMutation, useQueryClient } from '@tanstack/react-query'
import { builderAgentApi } from '../api/builderAgent'
import type { ApplyConfigRequest, BuilderChatRequest } from '../types/builderAgent'

export function useSendBuilderMessage(projectId: string) {
  return useMutation({
    mutationFn: (data: BuilderChatRequest) => builderAgentApi.chat(projectId, data),
    // No invalidation here — ChatPanel manages optimistic updates via setQueryData
  })
}

export function useApplyConfig(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ApplyConfigRequest) =>
      builderAgentApi.applyConfig(projectId, data),
    onSuccess: (_data, variables) => {
      // Invalidate relevant queries after config is applied
      if (variables.config_type === 'test_cases') {
        queryClient.invalidateQueries({ queryKey: ['test-cases', projectId] })
      } else if (variables.config_type === 'judge_config') {
        queryClient.invalidateQueries({ queryKey: ['judge-config', projectId] })
      }
      // Always refresh readiness
      queryClient.invalidateQueries({ queryKey: ['readiness', projectId] })
    },
  })
}
