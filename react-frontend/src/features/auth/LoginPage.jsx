import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { FiLogIn } from 'react-icons/fi'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { FormField, inputClass } from '../../components/ui/FormField'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/apiClient'

export function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await login(form)
      navigate(location.state?.from?.pathname || '/dashboard', { replace: true })
    } catch (caughtError) {
      setError(getApiErrorMessage(caughtError, 'Login failed. Check your email and password.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthFrame title="Welcome back" subtitle="Continue testing the Companio customer experience.">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <FormField label="Email">
          <input
            className={inputClass}
            type="email"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            required
          />
        </FormField>
        <FormField label="Password">
          <input
            className={inputClass}
            type="password"
            value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
            required
          />
        </FormField>
        {error ? <p className="rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{error}</p> : null}
        <Button className="w-full" type="submit" disabled={submitting}>
          <FiLogIn /> {submitting ? 'Logging in...' : 'Login'}
        </Button>
      </form>
      <p className="mt-5 text-center text-sm text-slate-600">
        New to Companio?{' '}
        <Link className="font-semibold text-slate-950 underline" to="/register">
          Create an account
        </Link>
      </p>
    </AuthFrame>
  )
}

export function AuthFrame({ title, subtitle, children }) {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-100 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <Link className="text-2xl font-black text-slate-950" to="/">
            Companio
          </Link>
          <p className="mt-1 text-sm text-slate-500">The AI person who understands you.</p>
        </div>
        <Card>
          <h1 className="text-2xl font-bold text-slate-950">{title}</h1>
          <p className="mt-2 text-sm text-slate-600">{subtitle}</p>
          <div className="mt-6">{children}</div>
        </Card>
      </div>
    </main>
  )
}
