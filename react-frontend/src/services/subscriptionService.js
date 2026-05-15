import { apiClient } from './apiClient'

export const subscriptionService = {
  listPlans() {
    return apiClient.get('/subscriptions/plans/').then((response) => response.data)
  },
  getCurrentSubscription() {
    return apiClient.get('/subscriptions/me/').then((response) => response.data)
  },
}
