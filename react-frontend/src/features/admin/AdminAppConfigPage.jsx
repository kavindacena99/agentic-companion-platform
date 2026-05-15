import { AdminPlaceholder } from '../../components/admin/AdminPlaceholder'
import { PageHeader } from '../../components/admin/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { appConfigService } from '../../services/appConfigService'
import { pendingAdminEndpoints } from '../../services/adminService'

export function AdminAppConfigPage() {
  const { data, loading, error } = useAsync(appConfigService.getPublicConfig, [])
  const appEntries = Object.entries(data?.app || {})
  const featureEntries = Object.entries(data?.features || {})

  return (
    <div className="space-y-6">
      <PageHeader title="App configuration">
        Public app config and public feature flags are connected. Editing requires admin config endpoints.
      </PageHeader>
      <AdminPlaceholder title="Config write endpoints pending" endpoint={`${pendingAdminEndpoints.appConfig} and ${pendingAdminEndpoints.featureFlags}`}>
        Needed for maintenance mode, public URLs, feature flags, rollout percentages, and usage defaults.
      </AdminPlaceholder>
      {error ? <StateBlock type="error" title="Could not load public app config">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading app config...</p> : null}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="font-bold">Public app config</h2>
          <div className="mt-4 space-y-2">
            {appEntries.map(([key, value]) => (
              <ConfigRow key={key} label={key} value={String(value)} />
            ))}
          </div>
        </Card>
        <Card>
          <h2 className="font-bold">Public feature flags</h2>
          <div className="mt-4 space-y-2">
            {featureEntries.map(([key, value]) => (
              <div key={key} className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                <span className="font-mono text-xs font-semibold text-slate-700">{key}</span>
                <Badge tone={value ? 'green' : 'slate'}>{value ? 'Enabled' : 'Disabled'}</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}

function ConfigRow({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
      <span className="font-mono text-xs font-semibold text-slate-700">{label}</span>
      <span className="break-all text-right text-sm text-slate-600">{value || 'empty'}</span>
    </div>
  )
}
