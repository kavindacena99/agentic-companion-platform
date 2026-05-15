import { apiClient } from './apiClient'

export const profileService = {
  getProfile() {
    return apiClient.get('/profile/me/').then((response) => response.data)
  },
  updateProfile(payload) {
    return apiClient.patch('/profile/me/', payload).then((response) => response.data)
  },
}
