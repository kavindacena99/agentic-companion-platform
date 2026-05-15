import { apiClient } from './apiClient'

export const usageService = {
  getUsage() {
    return apiClient.get('/usage/me/').then((response) => response.data)
  },
}
