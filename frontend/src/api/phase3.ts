import client from './client'

export async function listSuites(projectId: string) {
  const { data } = await client.get(`/projects/${projectId}/tests/suites`)
  return data
}

export async function listEnvironments(projectId: string) {
  const { data } = await client.get(`/projects/${projectId}/deploy/environments`)
  return data
}

export async function listArtifactRepositories(projectId: string) {
  const { data } = await client.get(`/projects/${projectId}/artifacts/repositories`)
  return data
}
