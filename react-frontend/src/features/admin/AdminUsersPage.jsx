import { useState } from 'react'
import { FiRefreshCw, FiShield, FiUser } from 'react-icons/fi'
import { PageHeader } from '../../components/admin/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAsync } from '../../hooks/useAsync'
import { getApiErrorMessage } from '../../services/apiClient'
import { adminService } from '../../services/adminService'

export function AdminUsersPage() {
  const [actionError, setActionError] = useState('')
  const { data: users, loading, error, run, setData } = useAsync(adminService.listUsers, [])

  async function toggleActive(user) {
    setActionError('')
    try {
      const updated = await adminService.updateUser(user.id, { is_active: !user.is_active })
      setData((current) => current.map((u) => (u.id === user.id ? { ...u, ...updated } : u)))
    } catch (e) {
      setActionError(getApiErrorMessage(e, 'Could not update user.'))
    }
  }

  async function toggleRole(user) {
    setActionError('')
    const newRole = user.role === 'admin' ? 'user' : 'admin'
    try {
      const updated = await adminService.updateUser(user.id, { role: newRole })
      setData((current) => current.map((u) => (u.id === user.id ? { ...u, ...updated } : u)))
    } catch (e) {
      setActionError(getApiErrorMessage(e, 'Could not update role.'))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="User management"
        action={
          <Button variant="secondary" onClick={run} disabled={loading}>
            <FiRefreshCw /> Refresh
          </Button>
        }
      >
        All registered users. Toggle active status or admin role. Email cannot be changed here.
      </PageHeader>

      {actionError ? <p className="rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{actionError}</p> : null}
      {error ? <StateBlock type="error" title="Could not load users">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading users...</p> : null}
      {!loading && users?.length === 0 ? <StateBlock title="No users found" /> : null}

      <div className="grid gap-4">
        {(users || []).map((user) => (
          <Card key={user.id}>
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div className="flex items-center gap-4">
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-slate-950 text-white">
                  {user.role === 'admin' ? <FiShield className="h-4 w-4" /> : <FiUser className="h-4 w-4" />}
                </div>
                <div>
                  <p className="font-semibold text-slate-950">{user.email}</p>
                  <p className="text-sm text-slate-500">@{user.username}{user.full_name ? ` · ${user.full_name}` : ''}</p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={user.is_active ? 'green' : 'rose'}>{user.is_active ? 'Active' : 'Inactive'}</Badge>
                <Badge tone={user.role === 'admin' ? 'amber' : 'slate'}>{user.role}</Badge>
                <Button variant="secondary" onClick={() => toggleActive(user)}>
                  {user.is_active ? 'Deactivate' : 'Activate'}
                </Button>
                <Button variant="secondary" onClick={() => toggleRole(user)}>
                  {user.role === 'admin' ? 'Remove admin' : 'Make admin'}
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
