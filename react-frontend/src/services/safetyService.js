import { apiClient } from './apiClient'

export const safetyService = {
  createReport(payload) {
    return apiClient.post('/safety-reports/', payload).then((response) => response.data)
  },
  listMyReports() {
    return apiClient.get('/safety-reports/my/').then((response) => response.data)
  },
}
