import { FiPlus, FiRefreshCw } from 'react-icons/fi'
import { AdminPlaceholder } from '../../components/admin/AdminPlaceholder'
import { PageHeader } from '../../components/admin/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { adminService, pendingAdminEndpoints } from '../../services/adminService'

export function AdminAgentsPage() {
  const { data: agents, loading, error, run } = useAsync(adminService.listVisibleAgents, [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Agent management"
        action={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={run}><FiRefreshCw /> Refresh</Button>
            <Button disabled><FiPlus /> Create agent</Button>
          </div>
        }
      >
        Connected to the current user-visible agent list. Create, edit, and enable/disable actions need admin APIs.
      </PageHeader>

      <AdminPlaceholder title="Agent CRUD endpoint pending" endpoint={pendingAdminEndpoints.agents}>
        Product-level agent records exist in the Main Backend, but only Django admin and seed commands can currently
        create or edit them. The React admin can safely display available agents now.
      </AdminPlaceholder>

      {error ? <StateBlock type="error" title="Could not load agents">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading agents...</p> : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(agents || []).map((agent) => (
          <Card key={agent.agent_key}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold">{agent.display_name}</h2>
                <p className="text-sm text-slate-500">{agent.agent_key}</p>
              </div>
              <Badge tone={agent.is_available ? 'green' : 'rose'}>{agent.availability_status}</Badge>
            </div>
            <p className="mt-4 min-h-12 text-sm leading-6 text-slate-600">{agent.short_description}</p>
            <div className="mt-4 grid gap-2 text-sm">
              <Row label="Type" value={agent.agent_type} />
              <Row label="Runtime" value={agent.runtime_status || 'unknown'} />
              <Row label="Premium" value={agent.requires_premium ? 'Yes' : 'No'} />
              <Row label="Features" value={agent.supported_features?.join(', ') || 'none'} />
            </div>
            <Button className="mt-5 w-full" disabled variant="secondary">Edit pending backend endpoint</Button>
          </Card>
        ))}
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
      <span className="font-medium text-slate-500">{label}</span>
      <span className="text-right font-semibold text-slate-900">{value}</span>
    </div>
  )
}
