import { FiCheck, FiRefreshCw } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useProduct } from '../../context/ProductContext'
import { useAsync } from '../../hooks/useAsync'
import { subscriptionService } from '../../services/subscriptionService'

export function SubscriptionsPage() {
  const { subscription, setSubscription, refreshSubscription } = useProduct()
  const { data: plans, loading, error, run } = useAsync(async () => {
    const [planList, current] = await Promise.all([subscriptionService.listPlans(), refreshSubscription()])
    setSubscription(current)
    return planList
  }, [refreshSubscription, setSubscription])

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Plans and subscriptions</h1>
          <p className="mt-2 text-sm text-slate-600">Read-only subscription testing against the Main Backend.</p>
        </div>
        <Button variant="secondary" onClick={run}>
          <FiRefreshCw /> Refresh
        </Button>
      </div>

      {subscription ? (
        <Card className="bg-slate-950 text-white">
          <p className="text-sm text-slate-300">Current plan</p>
          <div className="mt-2 flex flex-col justify-between gap-3 md:flex-row md:items-end">
            <div>
              <h2 className="text-3xl font-black">{subscription.plan_name}</h2>
              <p className="mt-2 text-sm text-slate-300">Status: {subscription.status}</p>
            </div>
            <Badge tone={subscription.can_access_premium_agents ? 'green' : 'amber'}>
              {subscription.can_access_premium_agents ? 'Premium agents enabled' : 'Standard agents only'}
            </Badge>
          </div>
        </Card>
      ) : null}

      {error ? <StateBlock type="error" title="Could not load plans">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading plans...</p> : null}

      <div className="grid gap-4 md:grid-cols-3">
        {(plans || []).map((plan) => (
          <Card key={plan.code} className={subscription?.plan_code === plan.code ? 'ring-2 ring-cyan-400' : ''}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold">{plan.name}</h2>
                <p className="text-sm capitalize text-slate-500">{plan.billing_period}</p>
              </div>
              {subscription?.plan_code === plan.code ? <Badge tone="green">Current</Badge> : null}
            </div>
            <p className="mt-4 text-3xl font-black">
              {Number(plan.price) === 0 ? 'Free' : `${plan.currency} ${plan.price}`}
            </p>
            <p className="mt-3 min-h-12 text-sm leading-6 text-slate-600">{plan.description}</p>
            <div className="mt-5 space-y-2 text-sm">
              <Feature>{plan.daily_message_limit || 'Unlimited'} daily messages</Feature>
              <Feature>{plan.monthly_message_limit || 'No monthly cap configured'}</Feature>
              <Feature>{plan.can_access_premium_agents ? 'Premium agents' : 'Standard agents'}</Feature>
            </div>
            <Button className="mt-6 w-full" disabled variant="secondary">
              Payment integration pending
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
