import { apiClient } from './apiClient'

// Still-pending endpoints (no backend support yet)
export const pendingAdminEndpoints = {
  llmProviders: '/api/admin/llm-providers/',
}

export const adminService = {
  // ── Dashboard stats ────────────────────────────────────────────────────────
  getStats() {
    return apiClient.get('/admin/stats/').then((r) => r.data)
  },

  // ── Users ─────────────────────────────────────────────────────────────────
  listUsers(params = {}) {
    return apiClient.get('/admin/users/', { params }).then((r) => r.data)
  },
  updateUser(id, data) {
    return apiClient.patch(`/admin/users/${id}/`, data).then((r) => r.data)
  },

  // ── Agents (admin — includes disabled) ────────────────────────────────────
  listAllAgents() {
    return apiClient.get('/admin/agents/').then((r) => r.data)
  },
  updateAgent(key, data) {
    return apiClient.patch(`/admin/agents/${key}/`, data).then((r) => r.data)
  },

  // ── Plans (admin — includes inactive) ─────────────────────────────────────
  listAllPlans() {
    return apiClient.get('/admin/plans/').then((r) => r.data)
  },
  updatePlan(code, data) {
    return apiClient.patch(`/admin/plans/${code}/`, data).then((r) => r.data)
  },

  // ── Subscriptions ──────────────────────────────────────────────────────────
  listAllSubscriptions(params = {}) {
    return apiClient.get('/admin/subscriptions/', { params }).then((r) => r.data)
  },

  // ── Safety reports ─────────────────────────────────────────────────────────
  listAllSafetyReports(params = {}) {
    return apiClient.get('/admin/safety-reports/', { params }).then((r) => r.data)
  },
  reviewSafetyReport(id, data) {
    return apiClient.patch(`/admin/safety-reports/${id}/`, data).then((r) => r.data)
  },

  // ── App config ─────────────────────────────────────────────────────────────
  listAppConfigs() {
    return apiClient.get('/admin/app-config/').then((r) => r.data)
  },
  updateAppConfig(key, data) {
    return apiClient.patch(`/admin/app-config/${key}/`, data).then((r) => r.data)
  },

  // ── Feature flags ──────────────────────────────────────────────────────────
  listFeatureFlags() {
    return apiClient.get('/admin/feature-flags/').then((r) => r.data)
  },
  updateFeatureFlag(key, data) {
    return apiClient.patch(`/admin/feature-flags/${key}/`, data).then((r) => r.data)
  },
}
