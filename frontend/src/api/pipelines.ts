import client from './client'

export interface Pipeline {
  id: string
  project_id: string
  name: string
  description?: string
  is_enabled: boolean
  run_counter: number
}

export async function listPipelines(projectId: string) {
  const { data } = await client.get(`/projects/${projectId}/pipelines`)
  return data
}

export async function createPipeline(projectId: string, payload: Record<string, unknown>) {
  const { data } = await client.post(`/projects/${projectId}/pipelines`, payload)
  return data
}

export async function triggerPipeline(projectId: string, pipelineId: string, payload = {}) {
  const { data } = await client.post(`/projects/${projectId}/pipelines/${pipelineId}/run`, payload)
  return data
}
