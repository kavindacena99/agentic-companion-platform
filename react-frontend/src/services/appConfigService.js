import { apiClient } from './apiClient'

export const appConfigService = {
  getPublicConfig() {
    return apiClient.get('/app-config/public/').then((response) => response.data)
  },
  health() {
    return apiClient.get('/health/').then((response) => response.data)
  },
}
