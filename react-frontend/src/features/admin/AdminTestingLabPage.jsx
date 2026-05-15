import { TestingLabPage } from '../testing/TestingLabPage'
import { AdminPlaceholder } from '../../components/admin/AdminPlaceholder'
import { PageHeader } from '../../components/admin/PageHeader'

export function AdminTestingLabPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Admin Testing Lab">
        Uses the same Main Backend APIs as the user app. It does not bypass business rules.
      </PageHeader>
      <AdminPlaceholder title="Admin-only diagnostics pending" endpoint="/api/admin/testing-lab/">
        Future backend support can add global diagnostics, runtime snapshots, and safe request traces. Current checks
        reuse existing endpoints only.
      </AdminPlaceholder>
      <TestingLabPage />
    </div>
  )
}
