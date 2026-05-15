import { apiClient } from './apiClient'

export const authService = {
  register(payload) {
    return apiClient.post('/auth/register/', payload).then((response) => response.data)
  },
  login(payload) {
    return apiClient.post('/auth/login/', payload).then((response) => response.data)
  },
  me() {
    return apiClient.get('/auth/me/').then((response) => response.data)
  },
}
