import { AdminPlaceholder } from '../../components/admin/AdminPlaceholder'
import { PageHeader } from '../../components/admin/PageHeader'
import { Card } from '../../components/ui/Card'
import { useAuth } from '../../context/AuthContext'
import { pendingAdminEndpoints } from '../../services/adminService'

export function AdminUsersPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <PageHeader title="User management">
        View and manage user accounts once the Main Backend exposes admin user APIs.
      </PageHeader>
      <AdminPlaceholder title="User list endpoint pending" endpoint={pendingAdminEndpoints.users}>
        The current API exposes only the authenticated user via `/api/auth/me/`. Listing all users, viewing user
        profiles, and activating/deactivating users needs a protected admin endpoint.
      </AdminPlaceholder>
      <Card>
        <h2 className="font-bold">Current admin user</h2>
        <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
          <Info label="Email" value={user?.email} />
          <Info label="Username" value={user?.username} />
          <Info label="Role" value={user?.role} />
          <Info label="Active" value={user?.is_active ? 'Yes' : 'No'} />
        </div>
      </Card>
    </div>
  )
}

function Info({ label, value }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 font-bold text-slate-950">{value || 'Not available'}</p>
    </div>
  )
}
