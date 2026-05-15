import { AdminPlaceholder } from '../../components/admin/AdminPlaceholder'
import { PageHeader } from '../../components/admin/PageHeader'
import { Card } from '../../components/ui/Card'
import { pendingAdminEndpoints } from '../../services/adminService'

export function AdminLlmProvidersPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="LLM provider configuration">
        React must never call provider APIs directly or expose secret keys. This page is reserved for safe Main
        Backend provider records once available.
      </PageHeader>
      <AdminPlaceholder title="LLM provider config endpoint pending" endpoint={pendingAdminEndpoints.llmProviders}>
        The current backend has Agent Gateway settings in environment variables, but no database-backed provider
        config model or REST endpoint. When implemented, API responses should mask secrets and expose only safe
        metadata such as provider name, model name, enabled state, and routing priority.
      </AdminPlaceholder>
      <Card>
        <h2 className="font-bold">Frontend safety rule</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          This React app will only call the Main Backend. Provider keys, model routing, LangGraph workflows, vector
          memory, and Agent Platform integration must stay behind backend APIs.
        </p>
      </Card>
    </div>
  )
}
