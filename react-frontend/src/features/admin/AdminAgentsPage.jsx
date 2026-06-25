import { useState } from 'react'
import { FiRefreshCw, FiToggleLeft, FiToggleRight } from 'react-icons/fi'
import { PageHeader } from '../../components/admin/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { getApiErrorMessage } from '../../services/apiClient'
import { adminService } from '../../services/adminService'

export function AdminAgentsPage() {
  const [actionError, setActionError] = useState('')
  const { data: agents, loading, error, run, setData } = useAsync(adminService.listAllAgents, [])

  async function toggleEnabled(agent) {
    setActionError('')
    try {
      const updated = await adminService.updateAgent(agent.key, { is_enabled: !agent.is_enabled })
      setData((current) => current.map((a) => (a.key === agent.key ? { ...a, ...updated } : a)))
    } catch (e) {
      setActionError(getApiErrorMessage(e, 'Could not update agent.'))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Agent management"
        action={
          <Button variant="secondary" onClick={run} disabled={loading}>
            <FiRefreshCw /> Refresh
          </Button>
        }
      >
        All product-level agents including disabled ones. Enable or disable to control user visibility and selectability.
        Agent AI logic lives in the Agent Platform (not built yet).
      </PageHeader>

      {actionError ? <p className="rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{actionError}</p> : null}
      {error ? <StateBlock type="error" title="Could not load agents">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading agents...</p> : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(agents || []).map((agent) => (
          <Card key={agent.key}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold">{agent.display_name}</h2>
                <p className="font-mono text-xs text-slate-500">{agent.key}</p>
              </div>
              <Badge tone={agent.is_enabled ? 'green' : 'rose'}>{agent.is_enabled ? 'Enabled' : 'Disabled'}</Badge>
            </div>
            <p className="mt-3 min-h-10 text-sm leading-6 text-slate-600">{agent.short_description}</p>
            <div className="mt-4 grid gap-2 text-sm">
              <Row label="Type" value={agent.agent_type} />
              <Row label="Premium" value={agent.is_premium ? 'Yes' : 'No'} />
              <Row label="Sort order" value={agent.sort_order} />
            </div>
            <Button
              className="mt-5 w-full"
              variant={agent.is_enabled ? 'danger' : 'accent'}
              onClick={() => toggleEnabled(agent)}
            >
              {agent.is_enabled ? <><FiToggleLeft /> Disable agent</> : <><FiToggleRight /> Enable agent</>}
            </Button>
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
