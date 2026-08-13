import { defineStore } from 'pinia'

interface AuthState {
  user: null | Record<string, unknown>
  accessToken: string
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    accessToken: ''
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken)
  }
})
