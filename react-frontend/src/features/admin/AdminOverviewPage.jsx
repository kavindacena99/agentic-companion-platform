import { Link } from 'react-router-dom'
import { FiCreditCard, FiFlag, FiSettings, FiShield, FiSmile, FiUsers } from 'react-icons/fi'
import { AdminPlaceholder } from '../../components/admin/AdminPlaceholder'
import { PageHeader } from '../../components/admin/PageHeader'
import { StatCard } from '../../components/admin/StatCard'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { adminService, pendingAdminEndpoints } from '../../services/adminService'

export function AdminOverviewPage() {
  const { data, loading, error } = useAsync(adminService.overview, [])
  const enabledAgents = data?.agents?.filter((agent) => agent.is_available).length || 0
  const enabledFeatures = data?.publicConfig?.features
    ? Object.values(data.publicConfig.features).filter(Boolean).length
    : 0

  return (
    <div className="space-y-6">
      <PageHeader title="Admin overview">
        Product-control readiness for the current Main Backend. This dashboard never calls provider APIs or the
        future Agent Platform directly.
      </PageHeader>

      {error ? <StateBlock type="error" title="Could not load admin overview">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading overview...</p> : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={FiSmile} label="Visible agents" value={data?.agents?.length ?? '-'} helper={`${enabledAgents} available now`} />
        <StatCard icon={FiCreditCard} label="Active plans" value={data?.plans?.length ?? '-'} helper="Read from public plans API" />
        <StatCard icon={FiShield} label="My reports" value={data?.mySafetyReports?.length ?? '-'} helper="Global admin report API pending" />
        <StatCard icon={FiSettings} label="Feature flags" value={data?.publicConfig?.features ? Object.keys(data.publicConfig.features).length : '-'} helper={`${enabledFeatures} enabled`} />
      </div>

      <AdminPlaceholder title="Analytics endpoints pending" endpoint="/api/admin/overview/">
        Total users, active users, global usage, revenue state, and global safety report counts require dedicated
        admin endpoints. Current cards use available public/user-scoped APIs.
      </AdminPlaceholder>

      <div className="grid gap-4 lg:grid-cols-3">
        <AdminShortcut to="/admin/users" icon={FiUsers} title="Users" endpoint={pendingAdminEndpoints.users} />
        <AdminShortcut to="/admin/agents" icon={FiSmile} title="Agents" endpoint={pendingAdminEndpoints.agents} />
        <AdminShortcut to="/admin/plans" icon={FiCreditCard} title="Plans" endpoint={pendingAdminEndpoints.plans} />
        <AdminShortcut to="/admin/safety-reports" icon={FiShield} title="Safety reports" endpoint={pendingAdminEndpoints.safetyReports} />
        <AdminShortcut to="/admin/app-config" icon={FiSettings} title="App config" endpoint={pendingAdminEndpoints.appConfig} />
        <AdminShortcut to="/admin/testing-lab" icon={FiFlag} title="Testing Lab" endpoint="Uses existing user APIs" />
      </div>
    </div>
  )
}

function AdminShortcut({ to, icon: Icon, title, endpoint }) {
  return (
    <Link to={to}>
      <Card className="h-full transition hover:border-cyan-300 hover:shadow-md">
        <div className="flex items-center justify-between gap-3">
          <Icon className="h-6 w-6 text-cyan-700" />
          <Badge tone="amber">Partial</Badge>
        </div>
        <h2 className="mt-4 font-bold">{title}</h2>
        <p className="mt-2 break-words font-mono text-xs text-slate-500">{endpoint}</p>
        <Button className="mt-4" variant="secondary">Open</Button>
      </Card>
    </Link>
  )
}
