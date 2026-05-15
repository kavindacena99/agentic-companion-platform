import { apiClient } from './apiClient'

export const settingsService = {
  getNotificationPreferences() {
    return apiClient.get('/notifications/preferences/').then((response) => response.data)
  },
  updateNotificationPreferences(payload) {
    return apiClient.patch('/notifications/preferences/', payload).then((response) => response.data)
  },
}
