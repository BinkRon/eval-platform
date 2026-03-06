import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { projectApi } from '../api/projects'
import type { ProjectCreate, ProjectUpdate } from '../types/project'

export function useProjects() {
  return useQuery({ queryKey: ['projects'], queryFn: projectApi.list })
}

export function useProject(id: string) {
  return useQuery({ queryKey: ['projects', id], queryFn: () => projectApi.get(id), enabled: !!id })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProjectCreate) => projectApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useUpdateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProjectUpdate }) => projectApi.update(id, data),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['projects'] })
      qc.invalidateQueries({ queryKey: ['projects', id] })
    },
  })
}

export function useDeleteProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => projectApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}
