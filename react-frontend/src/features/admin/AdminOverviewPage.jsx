import { Link } from 'react-router-dom'
import { FiCreditCard, FiMessageCircle, FiRefreshCw, FiSettings, FiShield, FiSmile, FiUsers } from 'react-icons/fi'
import { PageHeader } from '../../components/admin/PageHeader'
import { StatCard } from '../../components/admin/StatCard'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { adminService } from '../../services/adminService'

export function AdminOverviewPage() {
  const { data: stats, loading, error, run } = useAsync(adminService.getStats, [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin overview"
        action={
          <Button variant="secondary" onClick={run} disabled={loading}>
            <FiRefreshCw /> Refresh
          </Button>
        }
      >
        Live dashboard from the Main Backend admin APIs. No Agent Platform or provider APIs are called here.
      </PageHeader>

      {error ? <StateBlock type="error" title="Could not load stats">{error}</StateBlock> : null}
      {loading && !stats ? <p className="text-sm text-slate-500">Loading stats...</p> : null}

      {stats ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard icon={FiUsers} label="Total users" value={stats.total_users} helper={`${stats.active_users} active`} />
          <StatCard icon={FiSmile} label="Agents" value={stats.total_agents} helper={`${stats.enabled_agents} enabled`} />
          <StatCard icon={FiCreditCard} label="Active subscriptions" value={stats.active_subscriptions} helper={`${stats.total_plans} plans`} />
          <StatCard icon={FiMessageCircle} label="Messages today" value={stats.total_messages_today} helper={`${stats.total_chat_sessions} sessions total`} />
        </div>
      ) : null}

      {stats?.pending_safety_reports > 0 ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          <strong>{stats.pending_safety_reports}</strong> safety report{stats.pending_safety_reports !== 1 ? 's' : ''} pending review.{' '}
          <Link className="font-semibold underline" to="/admin/safety-reports">Review now</Link>
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <AdminShortcut to="/admin/users" icon={FiUsers} title="Users" description="View accounts, toggle active/admin" />
        <AdminShortcut to="/admin/agents" icon={FiSmile} title="Agents" description="Enable or disable product agents" />
        <AdminShortcut to="/admin/plans" icon={FiCreditCard} title="Plans" description="View and activate subscription plans" />
        <AdminShortcut to="/admin/safety-reports" icon={FiShield} title="Safety reports" description="Review and resolve user reports" />
        <AdminShortcut to="/admin/app-config" icon={FiSettings} title="App config" description="Manage config values and feature flags" />
        <AdminShortcut to="/admin/subscriptions" icon={FiCreditCard} title="Subscriptions" description="Browse all user subscriptions" />
      </div>
    </div>
  )
}

function AdminShortcut({ to, icon: Icon, title, description }) {
  return (
    <Link to={to}>
      <Card className="h-full transition hover:border-cyan-300 hover:shadow-md">
        <Icon className="h-6 w-6 text-cyan-700" />
        <h2 className="mt-4 font-bold">{title}</h2>
        <p className="mt-1 text-sm text-slate-500">{description}</p>
      </Card>
    </Link>
  )
}
