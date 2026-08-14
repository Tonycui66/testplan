import client from './client'

export async function listConnections(projectId: string) {
  const { data } = await client.get(`/projects/${projectId}/repo/connections`)
  return data
}

export async function createConnection(projectId: string, payload: Record<string, unknown>) {
  const { data } = await client.post(`/projects/${projectId}/repo/connections`, payload)
  return data
}
