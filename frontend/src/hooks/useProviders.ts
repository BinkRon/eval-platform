import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { providerApi } from '../api/providers'
import type { ProviderCreate, ProviderUpdate } from '../types/provider'

export function useProviders() {
  return useQuery({ queryKey: ['providers'], queryFn: providerApi.list })
}

export function useCreateProvider() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProviderCreate) => providerApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['providers'] })
      qc.invalidateQueries({ queryKey: ['model-options'] })
    },
  })
}

export function useUpdateProvider() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProviderUpdate }) => providerApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['providers'] })
      qc.invalidateQueries({ queryKey: ['model-options'] })
    },
  })
}

export function useDeleteProvider() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => providerApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['providers'] })
      qc.invalidateQueries({ queryKey: ['model-options'] })
    },
  })
}
