import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { LoadingScreen } from '../components/common/LoadingScreen'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <LoadingScreen label="Restoring your Companio session" />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <Outlet />
}
