import { useState } from 'react'
import { FiRefreshCw, FiToggleLeft, FiToggleRight } from 'react-icons/fi'
import { PageHeader } from '../../components/admin/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { getApiErrorMessage } from '../../services/apiClient'
import { adminService } from '../../services/adminService'

export function AdminAppConfigPage() {
  const [configError, setConfigError] = useState('')
  const [flagError, setFlagError] = useState('')
  const { data: configs, loading: configsLoading, error: configsError, run: refreshConfigs, setData: setConfigs } = useAsync(adminService.listAppConfigs, [])
  const { data: flags, loading: flagsLoading, error: flagsError, run: refreshFlags, setData: setFlags } = useAsync(adminService.listFeatureFlags, [])

  async function toggleFlag(flag) {
    setFlagError('')
    try {
      const updated = await adminService.updateFeatureFlag(flag.key, { is_enabled: !flag.is_enabled })
      setFlags((current) => current.map((f) => (f.key === flag.key ? { ...f, ...updated } : f)))
    } catch (e) {
      setFlagError(getApiErrorMessage(e, 'Could not update feature flag.'))
    }
  }

  async function toggleConfig(config) {
    setConfigError('')
    try {
      const updated = await adminService.updateAppConfig(config.key, { is_active: !config.is_active })
      setConfigs((current) => current.map((c) => (c.key === config.key ? { ...c, ...updated } : c)))
    } catch (e) {
      setConfigError(getApiErrorMessage(e, 'Could not update config.'))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="App configuration">
        Runtime config values and feature flags. Editing values inline (beyond active toggles) requires a future
        editor UI. Feature flag toggles take effect immediately for all users.
      </PageHeader>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* App config */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-950">Config values</h2>
            <Button variant="secondary" onClick={refreshConfigs} disabled={configsLoading}>
              <FiRefreshCw />
            </Button>
          </div>
          {configError ? <p className="rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{configError}</p> : null}
          {configsError ? <StateBlock type="error" title="Could not load configs">{configsError}</StateBlock> : null}
          {configsLoading ? <p className="text-sm text-slate-500">Loading...</p> : null}
          <Card>
            <div className="space-y-3">
              {(configs || []).map((c) => (
                <div key={c.key} className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                  <div>
                    <p className="font-mono text-xs font-semibold text-slate-700">{c.key}</p>
                    <p className="mt-0.5 text-xs text-slate-500">{c.description || 'No description'}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <span className="max-w-24 break-all text-right text-sm text-slate-800">{c.value || 'empty'}</span>
                    <Badge tone={c.is_active ? 'green' : 'slate'}>{c.is_active ? 'Active' : 'Off'}</Badge>
                    <button
                      className="rounded-lg p-1.5 hover:bg-slate-200"
                      onClick={() => toggleConfig(c)}
                      title={c.is_active ? 'Deactivate' : 'Activate'}
                    >
                      {c.is_active ? <FiToggleRight className="h-4 w-4 text-cyan-600" /> : <FiToggleLeft className="h-4 w-4 text-slate-400" />}
                    </button>
                  </div>
                </div>
              ))}
              {!configsLoading && (configs || []).length === 0 ? (
                <p className="py-4 text-center text-sm text-slate-500">No config values found.</p>
              ) : null}
            </div>
          </Card>
        </div>

        {/* Feature flags */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-950">Feature flags</h2>
            <Button variant="secondary" onClick={refreshFlags} disabled={flagsLoading}>
              <FiRefreshCw />
            </Button>
          </div>
          {flagError ? <p className="rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{flagError}</p> : null}
          {flagsError ? <StateBlock type="error" title="Could not load feature flags">{flagsError}</StateBlock> : null}
          {flagsLoading ? <p className="text-sm text-slate-500">Loading...</p> : null}
          <Card>
            <div className="space-y-3">
              {(flags || []).map((flag) => (
                <div key={flag.key} className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                  <div>
                    <p className="font-mono text-xs font-semibold text-slate-700">{flag.key}</p>
                    <p className="mt-0.5 text-xs text-slate-500">{flag.name}{flag.description ? ` — ${flag.description}` : ''}</p>
                    {flag.rollout_percentage !== null && flag.rollout_percentage < 100 ? (
                      <p className="mt-0.5 text-xs text-amber-700">{flag.rollout_percentage}% rollout</p>
                    ) : null}
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge tone={flag.is_enabled ? 'green' : 'slate'}>{flag.is_enabled ? 'Enabled' : 'Off'}</Badge>
                    <button
                      className="rounded-lg p-1.5 hover:bg-slate-200"
                      onClick={() => toggleFlag(flag)}
                      title={flag.is_enabled ? 'Disable' : 'Enable'}
                    >
                      {flag.is_enabled ? <FiToggleRight className="h-4 w-4 text-cyan-600" /> : <FiToggleLeft className="h-4 w-4 text-slate-400" />}
                    </button>
                  </div>
                </div>
              ))}
              {!flagsLoading && (flags || []).length === 0 ? (
                <p className="py-4 text-center text-sm text-slate-500">No feature flags found.</p>
              ) : null}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
