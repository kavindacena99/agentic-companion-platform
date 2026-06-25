import { useState } from 'react'
import { FiCheck, FiRefreshCw, FiToggleLeft, FiToggleRight } from 'react-icons/fi'
import { PageHeader } from '../../components/admin/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { getApiErrorMessage } from '../../services/apiClient'
import { adminService } from '../../services/adminService'

export function AdminPlansPage() {
  const [actionError, setActionError] = useState('')
  const { data: plans, loading, error, run, setData } = useAsync(adminService.listAllPlans, [])

  async function toggleActive(plan) {
    setActionError('')
    try {
      const updated = await adminService.updatePlan(plan.code, { is_active: !plan.is_active })
      setData((current) => current.map((p) => (p.code === plan.code ? { ...p, ...updated } : p)))
    } catch (e) {
      setActionError(getApiErrorMessage(e, 'Could not update plan.'))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Subscription plan management"
        action={
          <Button variant="secondary" onClick={run} disabled={loading}>
            <FiRefreshCw /> Refresh
          </Button>
        }
      >
        All subscription plans including inactive ones. Activate or deactivate plans to control user visibility.
        Payment provider integration is separate and pending.
      </PageHeader>

      {actionError ? <p className="rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{actionError}</p> : null}
      {error ? <StateBlock type="error" title="Could not load plans">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading plans...</p> : null}

      <div className="grid gap-4 md:grid-cols-3">
        {(plans || []).map((plan) => (
          <Card key={plan.code}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold">{plan.name}</h2>
                <p className="font-mono text-xs text-slate-500">{plan.code}</p>
              </div>
              <Badge tone={plan.is_active ? 'green' : 'rose'}>{plan.is_active ? 'Active' : 'Inactive'}</Badge>
            </div>
            <p className="mt-4 text-3xl font-black">
              {Number(plan.price) === 0 ? 'Free' : `${plan.currency} ${plan.price}`}
            </p>
            <p className="mt-3 min-h-10 text-sm leading-6 text-slate-600">{plan.description}</p>
            <div className="mt-4 space-y-2 text-sm">
              <Feature>{plan.daily_message_limit || 'Unlimited'} daily messages</Feature>
              <Feature>{plan.can_access_premium_agents ? 'Premium agents included' : 'Standard agents only'}</Feature>
              <Feature>Billing: {plan.billing_period}</Feature>
            </div>
            <Button
              className="mt-5 w-full"
              variant={plan.is_active ? 'danger' : 'accent'}
              onClick={() => toggleActive(plan)}
            >
              {plan.is_active ? <><FiToggleLeft /> Deactivate</> : <><FiToggleRight /> Activate</>}
            </Button>
          </Card>
        ))}
      </div>
    </div>
  )
}

function Feature({ children }) {
  return (
    <p className="flex items-center gap-2 text-slate-700">
      <FiCheck className="h-4 w-4 text-cyan-600" /> {children}
    </p>
  )
}
