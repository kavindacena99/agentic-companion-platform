import { useState } from 'react'
import { FiRefreshCw } from 'react-icons/fi'
import { PageHeader } from '../../components/admin/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { getApiErrorMessage } from '../../services/apiClient'
import { adminService } from '../../services/adminService'

const statusTone = {
  pending: 'amber',
  under_review: 'blue',
  resolved: 'green',
  dismissed: 'slate',
}

const nextStatusOptions = {
  pending: ['under_review', 'resolved', 'dismissed'],
  under_review: ['resolved', 'dismissed'],
  resolved: [],
  dismissed: [],
}

export function AdminSafetyReportsPage() {
  const [actionError, setActionError] = useState('')
  const { data: reports, loading, error, run, setData } = useAsync(adminService.listAllSafetyReports, [])

  async function updateStatus(report, newStatus) {
    setActionError('')
    try {
      const updated = await adminService.reviewSafetyReport(report.id, { status: newStatus })
      setData((current) => current.map((r) => (r.id === report.id ? { ...r, ...updated } : r)))
    } catch (e) {
      setActionError(getApiErrorMessage(e, 'Could not update report status.'))
    }
  }

  const pendingCount = (reports || []).filter((r) => r.status === 'pending').length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Safety reports"
        action={
          <Button variant="secondary" onClick={run} disabled={loading}>
            <FiRefreshCw /> Refresh
          </Button>
        }
      >
        Global review queue for all user safety reports. Resolve or dismiss to clear the queue.
      </PageHeader>

      {pendingCount > 0 ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-900">
          {pendingCount} report{pendingCount !== 1 ? 's' : ''} pending review
        </div>
      ) : null}

      {actionError ? <p className="rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{actionError}</p> : null}
      {error ? <StateBlock type="error" title="Could not load safety reports">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading reports...</p> : null}
      {!loading && reports?.length === 0 ? (
        <StateBlock title="No safety reports">No reports have been submitted yet.</StateBlock>
      ) : null}

      <div className="grid gap-4">
        {(reports || []).map((report) => (
          <Card key={report.id}>
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="font-bold capitalize">{report.category.replaceAll('_', ' ')}</h2>
                  <Badge tone={statusTone[report.status] || 'slate'}>{report.status}</Badge>
                </div>
                <p className="mt-1 text-sm text-slate-500">
                  Reported by {report.reported_by_email} · Session #{report.session_id} · Message #{report.message_id}
                </p>
                {report.description ? (
                  <p className="mt-3 text-sm leading-6 text-slate-700">{report.description}</p>
                ) : null}
                {report.reviewed_by_email ? (
                  <p className="mt-2 text-xs text-slate-500">
                    Reviewed by {report.reviewed_by_email}
                    {report.reviewed_at ? ` on ${new Date(report.reviewed_at).toLocaleDateString()}` : ''}
                  </p>
                ) : null}
              </div>
              {nextStatusOptions[report.status]?.length > 0 ? (
                <div className="flex shrink-0 flex-wrap gap-2">
                  {nextStatusOptions[report.status].map((s) => (
                    <Button key={s} variant="secondary" onClick={() => updateStatus(report, s)}>
                      Mark {s.replace('_', ' ')}
                    </Button>
                  ))}
                </div>
              ) : null}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
