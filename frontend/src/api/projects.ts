import client from './client'

export interface Project {
  id: string
  name: string
  key: string
  description?: string
  is_archived: boolean
  created_at: string
}

export async function listProjects(search = '') {
  const { data } = await client.get<{ items: Project[]; meta: { total: number } }>('/projects', {
    params: { search }
  })
  return data
}

export async function createProject(payload: { name: string; key: string; description?: string }) {
  const { data } = await client.post<Project>('/projects', payload)
  return data
}
