import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { providerApi, ProviderCreate, ProviderUpdate } from '../api/providers'

export function useProviders() {
  return useQuery({ queryKey: ['providers'], queryFn: providerApi.list })
}

export function useCreateProvider() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProviderCreate) => providerApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['providers'] }),
  })
}

export function useUpdateProvider() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProviderUpdate }) => providerApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['providers'] }),
  })
}

export function useDeleteProvider() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => providerApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['providers'] }),
  })
}
