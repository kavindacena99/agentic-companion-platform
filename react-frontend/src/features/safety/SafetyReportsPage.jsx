import { FiRefreshCw } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { safetyService } from '../../services/safetyService'

export function SafetyReportsPage() {
  const { data: reports, loading, error, run } = useAsync(safetyService.listMyReports, [])

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Safety reports</h1>
          <p className="mt-2 text-sm text-slate-600">Reports submitted for your own agent messages.</p>
        </div>
        <Button variant="secondary" onClick={run}>
          <FiRefreshCw /> Refresh
        </Button>
      </div>

      {error ? <StateBlock type="error" title="Could not load reports">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading reports...</p> : null}
      {!loading && reports?.length === 0 ? (
        <StateBlock title="No safety reports">Report buttons appear under agent messages in chat.</StateBlock>
      ) : null}

      <div className="grid gap-4">
        {(reports || []).map((report) => (
          <Card key={report.id}>
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
              <div>
                <h2 className="font-bold capitalize">{report.category.replaceAll('_', ' ')}</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Session #{report.session_id} · Message #{report.message_id}
                </p>
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
