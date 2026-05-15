import { AdminPlaceholder } from '../../components/admin/AdminPlaceholder'
import { PageHeader } from '../../components/admin/PageHeader'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { subscriptionService } from '../../services/subscriptionService'
import { pendingAdminEndpoints } from '../../services/adminService'

export function AdminSubscriptionsPage() {
  const { data, loading, error } = useAsync(subscriptionService.getCurrentSubscription, [])

  return (
    <div className="space-y-6">
      <PageHeader title="Subscription records">
        Global subscription management requires admin endpoints. Current view shows only the logged-in user's status.
      </PageHeader>
      <AdminPlaceholder title="Global subscription endpoint pending" endpoint={pendingAdminEndpoints.subscriptions}>
        Needed for viewing active, expired, cancelled, and manually assigned subscriptions across users.
      </AdminPlaceholder>
      {error ? <StateBlock type="error" title="Could not load current subscription">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading current subscription...</p> : null}
      {data ? (
        <Card>
          <h2 className="font-bold">Current user's subscription</h2>
          <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
            <Info label="Plan" value={data.plan_name} />
            <Info label="Status" value={data.status} />
            <Info label="Daily limit" value={data.daily_message_limit || 'Unlimited'} />
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
