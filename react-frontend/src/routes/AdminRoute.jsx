import { Navigate, Outlet } from 'react-router-dom'
import { StateBlock } from '../components/common/StateBlock'
import { Button } from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'

export function AdminRoute() {
  const { user, isAuthenticated } = useAuth()
  const isAdmin = user?.role === 'admin' || user?.is_staff

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!isAdmin) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-100 px-4">
        <div className="w-full max-w-lg">
          <StateBlock
            type="error"
            title="Admin access required"
            action={
              <a href="/dashboard">
                <Button>Back to dashboard</Button>
              </a>
            }
          >
            Your account is authenticated, but the Main Backend does not mark it as an admin user.
          </StateBlock>
        </div>
      </div>
    )
  }

  return <Outlet />
}
