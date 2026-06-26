import { Link } from 'react-router-dom'
import { FiRefreshCw } from 'react-icons/fi'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useProduct } from '../../context/ProductContext'
import { useAsync } from '../../hooks/useAsync'

export function UsagePage() {
  const { usage, setUsage, refreshUsage } = useProduct()
  const { loading, error, run } = useAsync(async () => {
    const data = await refreshUsage()
    setUsage(data)
    return data
  }, [refreshUsage, setUsage])

  const percent = usage ? Math.min((usage.messages_used / usage.message_limit) * 100, 100) : 0

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Usage</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Daily message limits from `/api/usage/me/`.</p>
        </div>
        <Button variant="secondary" onClick={run}>
          <FiRefreshCw /> Refresh
        </Button>
      </div>

      {error ? <StateBlock type="error" title="Could not load usage">{error}</StateBlock> : null}
      <Card>
        {loading && !usage ? <p className="text-sm text-slate-500 dark:text-slate-400">Loading usage...</p> : null}
        {usage ? (
          <div>
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Messages used today</p>
                <p className="mt-2 text-5xl font-black">{usage.messages_used}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-500 dark:text-slate-400">Remaining</p>
                <p className="mt-2 text-3xl font-bold text-cyan-700 dark:text-cyan-400">{usage.remaining_messages}</p>
              </div>
            </div>
            <div className="mt-6 h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
              <div className="h-full rounded-full bg-cyan-500" style={{ width: `${percent}%` }} />
            </div>
            <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
              <Info label="Date" value={usage.date} />
              <Info label="Limit" value={usage.message_limit} />
              <Info label="Can send" value={usage.can_send_message ? 'Yes' : 'No'} />
            </div>
            {!usage.can_send_message ? (
              <div className="mt-5 rounded-2xl bg-amber-50 p-4 text-sm text-amber-900 dark:bg-amber-950/30 dark:text-amber-400">
                The backend says the limit is reached. Use this state to validate upgrade prompts and blocked send
                behavior in chat.
              </div>
            ) : null}
          </div>
        ) : null}
      </Card>

      <Card className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h2 className="font-bold">Need more capacity?</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">Plan upgrades are read-only in the current backend.</p>
        </div>
        <Link to="/subscriptions">
          <Button variant="accent">View plans</Button>
        </Link>
      </Card>
    </div>
  )
}

function Info({ label, value }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-1 font-bold text-slate-950 dark:text-white">{value}</p>
    </div>
  )
}
