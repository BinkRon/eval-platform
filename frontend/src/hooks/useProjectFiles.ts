import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { projectFileApi } from '../api/projectFiles'

export function useProjectFiles(projectId: string) {
  return useQuery({
    queryKey: ['project-files', projectId],
    queryFn: () => projectFileApi.list(projectId),
    enabled: !!projectId,
  })
}

export function useUploadFile(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => projectFileApi.upload(projectId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project-files', projectId] })
    },
  })
}

export function useDeleteFile(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (fileId: string) => projectFileApi.delete(projectId, fileId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project-files', projectId] })
    },
  })
}
