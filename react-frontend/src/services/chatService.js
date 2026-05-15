import { apiClient } from './apiClient'

export const chatService = {
  listSessions() {
    return apiClient.get('/chats/sessions/').then((response) => response.data)
  },
  createSession(payload = {}) {
    return apiClient.post('/chats/sessions/', payload).then((response) => response.data)
  },
  getSession(sessionId) {
    return apiClient.get(`/chats/sessions/${sessionId}/`).then((response) => response.data)
  },
  listMessages(sessionId) {
    return apiClient.get(`/chats/sessions/${sessionId}/messages/`).then((response) => response.data)
  },
  sendMessage(sessionId, content) {
    return apiClient
      .post(`/chats/sessions/${sessionId}/messages/`, { content })
      .then((response) => response.data)
  },
}
