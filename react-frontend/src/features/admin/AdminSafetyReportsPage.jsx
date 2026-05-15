import { AdminPlaceholder } from '../../components/admin/AdminPlaceholder'
import { PageHeader } from '../../components/admin/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { safetyService } from '../../services/safetyService'
import { pendingAdminEndpoints } from '../../services/adminService'

export function AdminSafetyReportsPage() {
  const { data: reports, loading, error } = useAsync(safetyService.listMyReports, [])

  return (
    <div className="space-y-6">
      <PageHeader title="Safety reports admin">
        Global review queue and status updates require admin APIs. Current data is the logged-in user's reports.
      </PageHeader>
      <AdminPlaceholder title="Global safety report endpoint pending" endpoint={pendingAdminEndpoints.safetyReports}>
        Needed for filtering by category/status, opening report details, assigning reviewers, and resolving reports.
      </AdminPlaceholder>
      {error ? <StateBlock type="error" title="Could not load safety reports">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading reports...</p> : null}
      {!loading && reports?.length === 0 ? <StateBlock title="No reports for current user">Global report queue is pending backend support.</StateBlock> : null}
      <div className="grid gap-4">
        {(reports || []).map((report) => (
          <Card key={report.id}>
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
              <div>
                <h2 className="font-bold capitalize">{report.category.replaceAll('_', ' ')}</h2>
                <p className="mt-1 text-sm text-slate-500">Session #{report.session_id} · Message #{report.message_id}</p>
              </div>
              <Badge tone={report.status === 'resolved' ? 'green' : 'amber'}>{report.status}</Badge>
            </div>
            {report.description ? <p className="mt-4 text-sm leading-6 text-slate-700">{report.description}</p> : null}
          </Card>
        ))}
      </div>
    </div>
  )
}
