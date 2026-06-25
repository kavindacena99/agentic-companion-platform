import { FiRefreshCw } from 'react-icons/fi'
import { PageHeader } from '../../components/admin/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { adminService } from '../../services/adminService'

const statusTone = {
  active: 'green',
  trialing: 'blue',
  expired: 'rose',
  cancelled: 'rose',
  past_due: 'amber',
  inactive: 'slate',
}

export function AdminSubscriptionsPage() {
  const { data: subscriptions, loading, error, run } = useAsync(adminService.listAllSubscriptions, [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Subscription records"
        action={
          <Button variant="secondary" onClick={run} disabled={loading}>
            <FiRefreshCw /> Refresh
          </Button>
        }
      >
        All user subscriptions from the Main Backend. Manual or provider-assigned plans appear here.
      </PageHeader>

      {error ? <StateBlock type="error" title="Could not load subscriptions">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading subscriptions...</p> : null}
      {!loading && subscriptions?.length === 0 ? (
        <StateBlock title="No subscriptions found">Users on the free plan do not appear here.</StateBlock>
      ) : null}

      <div className="grid gap-4">
        {(subscriptions || []).map((sub) => (
          <Card key={sub.id}>
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
              <div>
                <p className="font-semibold text-slate-950">{sub.user_email}</p>
                <p className="mt-1 text-sm text-slate-500">
                  {sub.plan_name} · {sub.provider}
                  {sub.provider_subscription_id ? ` · ${sub.provider_subscription_id}` : ''}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={statusTone[sub.status] || 'slate'}>{sub.status}</Badge>
                {sub.expires_at ? (
                  <span className="text-xs text-slate-500">
                    Expires {new Date(sub.expires_at).toLocaleDateString()}
                  </span>
                ) : (
                  <span className="text-xs text-slate-500">No expiry</span>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
