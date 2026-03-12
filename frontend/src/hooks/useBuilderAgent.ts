import { useMutation } from '@tanstack/react-query'
import { builderAgentApi } from '../api/builderAgent'
import type { BuilderChatRequest } from '../types/builderAgent'

export function useSendBuilderMessage(projectId: string) {
  return useMutation({
    mutationFn: (data: BuilderChatRequest) => builderAgentApi.chat(projectId, data),
    // No invalidation here — ChatPanel manages optimistic updates via setQueryData
  })
}
