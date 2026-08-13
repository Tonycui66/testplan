import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  timeout: 10000
})

interface RetryConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryConfig | undefined
    if (error.response?.status !== 401 || !config || config._retry) {
      return Promise.reject(error)
    }
    config._retry = true
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      window.location.href = '/login'
      return Promise.reject(error)
    }
    try {
      const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      config.headers.Authorization = `Bearer ${data.access_token}`
      return client(config)
    } catch (refreshError) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
      return Promise.reject(refreshError)
    }
  }
)

export default client
