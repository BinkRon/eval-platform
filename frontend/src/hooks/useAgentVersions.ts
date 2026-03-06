import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { agentVersionApi } from '../api/agentVersions'
import type { AgentVersionCreate, AgentVersionUpdate } from '../types/agentVersion'

export function useAgentVersions(projectId: string) {
  return useQuery({
    queryKey: ['agent-versions', projectId],
    queryFn: () => agentVersionApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useCreateAgentVersion(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: AgentVersionCreate) => agentVersionApi.create(projectId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['agent-versions', projectId] }),
  })
}

export function useUpdateAgentVersion(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AgentVersionUpdate }) =>
      agentVersionApi.update(projectId, id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['agent-versions', projectId] }),
  })
}

export function useDeleteAgentVersion(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => agentVersionApi.delete(projectId, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['agent-versions', projectId] }),
  })
}
