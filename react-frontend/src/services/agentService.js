import { apiClient } from './apiClient'

export const agentService = {
  listAgents() {
    return apiClient.get('/agents/').then((response) => response.data)
  },
  getAgent(id) {
    return apiClient.get(`/agents/${id}/`).then((response) => response.data)
  },
  getSelectedAgent() {
    return apiClient.get('/agents/selected/').then((response) => response.data)
  },
  selectAgent(agentKey) {
    return apiClient.post('/agents/select/', { agent_key: agentKey }).then((response) => response.data)
  },
}
