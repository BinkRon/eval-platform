import client from './client'
import type { ProjectFile } from '../types/projectFile'

export const projectFileApi = {
  list: (projectId: string) =>
    client.get<ProjectFile[]>(`/projects/${projectId}/files`).then((r) => r.data),
  upload: (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client
      .post<ProjectFile>(`/projects/${projectId}/files`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },
  delete: (projectId: string, fileId: string) =>
    client.delete(`/projects/${projectId}/files/${fileId}`),
}
