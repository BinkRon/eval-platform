import client from './client'
import type { Project, ProjectCreate, ProjectUpdate } from '../types/project'

export type { Project, ProjectCreate, ProjectUpdate }

export const projectApi = {
  list: () => client.get<Project[]>('/projects').then((r) => r.data),
  get: (id: string) => client.get<Project>(`/projects/${id}`).then((r) => r.data),
  create: (data: ProjectCreate) => client.post<Project>('/projects', data).then((r) => r.data),
  update: (id: string, data: ProjectUpdate) => client.put<Project>(`/projects/${id}`, data).then((r) => r.data),
  delete: (id: string) => client.delete(`/projects/${id}`),
}
