import { FiMessageCircle, FiRefreshCw, FiUsers } from 'react-icons/fi'
import { PageHeader } from '../../components/admin/PageHeader'
import { StatCard } from '../../components/admin/StatCard'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { adminService } from '../../services/adminService'
import { usageService } from '../../services/usageService'

export function AdminUsagePage() {
  const { data: stats, loading: statsLoading, error: statsError, run: refreshStats } = useAsync(adminService.getStats, [])
  const { data: myUsage, loading: myLoading } = useAsync(usageService.getUsage, [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Usage overview"
        action={
          <Button variant="secondary" onClick={refreshStats} disabled={statsLoading}>
            <FiRefreshCw /> Refresh
          </Button>
        }
      >
        Platform-level usage metrics. Per-user daily usage is tracked via DailyUsage records on the backend.
        Individual record management is out of scope for this admin panel.
      </PageHeader>

      {statsError ? <StateBlock type="error" title="Could not load stats">{statsError}</StateBlock> : null}
      {statsLoading ? <p className="text-sm text-slate-500">Loading stats...</p> : null}

      {stats ? (
        <div className="grid gap-4 md:grid-cols-3">
          <StatCard icon={FiMessageCircle} label="Messages today (all users)" value={stats.total_messages_today} helper="Resets at midnight UTC" />
          <StatCard icon={FiUsers} label="Total active users" value={stats.active_users} helper={`of ${stats.total_users} registered`} />
          <StatCard icon={FiMessageCircle} label="Total chat sessions" value={stats.total_chat_sessions} />
        </div>
      ) : null}

      {!myLoading && myUsage ? (
        <Card>
          <h2 className="font-bold text-slate-950">Your own usage today</h2>
          <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">
            <Info label="Date" value={myUsage.date} />
            <Info label="Used" value={myUsage.messages_used} />
            <Info label="Limit" value={myUsage.message_limit} />
            <Info label="Remaining" value={myUsage.remaining_messages} />
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
