import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { builderConversationApi } from '../api/builderConversation'

export function useBuilderConversation(projectId: string) {
  return useQuery({
    queryKey: ['builder-conversation', projectId],
    queryFn: () => builderConversationApi.get(projectId),
    enabled: !!projectId,
  })
}

export function useClearConversation(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => builderConversationApi.clear(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['builder-conversation', projectId] })
    },
  })
}
