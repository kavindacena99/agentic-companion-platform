import { FiPlus, FiRefreshCw } from 'react-icons/fi'
import { AdminPlaceholder } from '../../components/admin/AdminPlaceholder'
import { PageHeader } from '../../components/admin/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { adminService, pendingAdminEndpoints } from '../../services/adminService'

export function AdminPlansPage() {
  const { data: plans, loading, error, run } = useAsync(adminService.listActivePlans, [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Subscription plan management"
        action={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={run}><FiRefreshCw /> Refresh</Button>
            <Button disabled><FiPlus /> Create plan</Button>
          </div>
        }
      >
        Showing active plans from the public plan endpoint. Admin create/edit/disable needs a protected backend API.
      </PageHeader>

      <AdminPlaceholder title="Plan CRUD endpoint pending" endpoint={pendingAdminEndpoints.plans}>
        Plans are currently managed by Django admin or `seed_plans`. React can list active plans, but cannot safely
        change pricing or usage limits until admin plan endpoints exist.
      </AdminPlaceholder>

      {error ? <StateBlock type="error" title="Could not load plans">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading plans...</p> : null}

      <div className="grid gap-4 md:grid-cols-3">
        {(plans || []).map((plan) => (
          <Card key={plan.code}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold">{plan.name}</h2>
                <p className="text-sm text-slate-500">{plan.code}</p>
              </div>
              <Badge tone={plan.can_access_premium_agents ? 'green' : 'blue'}>
                {plan.can_access_premium_agents ? 'Premium' : 'Standard'}
              </Badge>
            </div>
            <p className="mt-4 text-3xl font-black">{Number(plan.price) === 0 ? 'Free' : `${plan.currency} ${plan.price}`}</p>
            <p className="mt-3 min-h-12 text-sm leading-6 text-slate-600">{plan.description}</p>
            <div className="mt-4 space-y-2 text-sm">
              <Row label="Billing" value={plan.billing_period} />
              <Row label="Daily limit" value={plan.daily_message_limit || 'Unlimited'} />
              <Row label="Monthly limit" value={plan.monthly_message_limit || 'Not configured'} />
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
