import { defineStore } from 'pinia'
import client from '../api/client'

interface User {
  id: string
  email: string
  name: string
  avatar_url?: string
}

interface AuthState {
  user: User | null
  accessToken: string
  refreshToken: string
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    accessToken: localStorage.getItem('access_token') ?? '',
    refreshToken: localStorage.getItem('refresh_token') ?? ''
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken)
  },
  actions: {
    async login(email: string, password: string) {
      const { data } = await client.post('/auth/login', { email, password })
      this.setSession(data)
    },
    async register(email: string, password: string, name: string) {
      const { data } = await client.post('/auth/register', { email, password, name })
      this.setSession(data)
    },
    async me() {
      const { data } = await client.get('/auth/me')
      this.user = data
    },
    setSession(data: { access_token: string; refresh_token: string; user: User }) {
      this.accessToken = data.access_token
      this.refreshToken = data.refresh_token
      this.user = data.user
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
    },
    async logout() {
      try {
        if (this.refreshToken) {
          await client.post('/auth/logout', { refresh_token: this.refreshToken })
        }
      } finally {
        this.user = null
        this.accessToken = ''
        this.refreshToken = ''
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
    }
  }
})
