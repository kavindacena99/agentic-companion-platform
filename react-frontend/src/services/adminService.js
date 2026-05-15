import { agentService } from './agentService'
import { appConfigService } from './appConfigService'
import { safetyService } from './safetyService'
import { subscriptionService } from './subscriptionService'
import { usageService } from './usageService'

export const pendingAdminEndpoints = {
  users: '/api/admin/users/',
  agents: '/api/admin/agents/',
  plans: '/api/admin/plans/',
  subscriptions: '/api/admin/subscriptions/',
  usage: '/api/admin/usage/',
  safetyReports: '/api/admin/safety-reports/',
  appConfig: '/api/admin/app-config/',
  featureFlags: '/api/admin/feature-flags/',
  llmProviders: '/api/admin/llm-providers/',
}

export const adminService = {
  async overview() {
    const [agents, plans, publicConfig, usage, safetyReports] = await Promise.allSettled([
      agentService.listAgents(),
      subscriptionService.listPlans(),
      appConfigService.getPublicConfig(),
      usageService.getUsage(),
      safetyService.listMyReports(),
    ])

    return {
      agents: agents.status === 'fulfilled' ? agents.value : [],
      plans: plans.status === 'fulfilled' ? plans.value : [],
      publicConfig: publicConfig.status === 'fulfilled' ? publicConfig.value : null,
      currentUserUsage: usage.status === 'fulfilled' ? usage.value : null,
      mySafetyReports: safetyReports.status === 'fulfilled' ? safetyReports.value : [],
      errors: [agents, plans, publicConfig, usage, safetyReports]
        .filter((result) => result.status === 'rejected')
        .map((result) => result.reason),
    }
  },
  listVisibleAgents: agentService.listAgents,
  listActivePlans: subscriptionService.listPlans,
  getPublicAppConfig: appConfigService.getPublicConfig,
  listMySafetyReports: safetyService.listMyReports,
  getCurrentUserUsage: usageService.getUsage,
}
