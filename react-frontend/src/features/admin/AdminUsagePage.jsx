import { AdminPlaceholder } from '../../components/admin/AdminPlaceholder'
import { PageHeader } from '../../components/admin/PageHeader'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { usageService } from '../../services/usageService'
import { pendingAdminEndpoints } from '../../services/adminService'

export function AdminUsagePage() {
  const { data, loading, error } = useAsync(usageService.getUsage, [])

  return (
    <div className="space-y-6">
      <PageHeader title="Usage management">
        User-wide usage records and limit overrides need an admin endpoint. Current data is scoped to the logged-in user.
      </PageHeader>
      <AdminPlaceholder title="Global usage endpoint pending" endpoint={pendingAdminEndpoints.usage}>
        Needed for listing user usage records, inspecting reset dates, and testing plan-limit behavior across accounts.
      </AdminPlaceholder>
      {error ? <StateBlock type="error" title="Could not load current usage">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading usage...</p> : null}
      {data ? (
        <Card>
          <h2 className="font-bold">Current user's daily usage</h2>
          <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">
            <Info label="Date" value={data.date} />
            <Info label="Used" value={data.messages_used} />
            <Info label="Limit" value={data.message_limit} />
            <Info label="Remaining" value={data.remaining_messages} />
          </div>
        </Card>
      ) : null}
    </div>
  )
}

function Info({ label, value }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 font-bold text-slate-950">{value}</p>
    </div>
  )
}
