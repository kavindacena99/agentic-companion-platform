import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { FiUserPlus } from 'react-icons/fi'
import { Button } from '../../components/ui/Button'
import { FormField, inputClass } from '../../components/ui/FormField'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/apiClient'
import { AuthFrame } from './LoginPage'

export function RegisterPage() {
  const { register, isAuthenticated } = useAuth()
  const [form, setForm] = useState({ email: '', username: '', full_name: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await register(form)
      navigate('/onboarding/profile', { replace: true })
    } catch (caughtError) {
      setError(getApiErrorMessage(caughtError, 'Registration failed. Please check the form.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthFrame title="Create your Companio profile" subtitle="Start with the backend-supported account fields.">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <FormField label="Email">
          <input className={inputClass} type="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
        </FormField>
        <FormField label="Username">
          <input className={inputClass} required value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />
        </FormField>
        <FormField label="Full name">
          <input className={inputClass} value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
        </FormField>
        <FormField label="Password" hint="Minimum 8 characters.">
          <input className={inputClass} type="password" minLength={8} required value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
        </FormField>
        {error ? (
          <p className="rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700 dark:bg-rose-950 dark:text-rose-400">
            {error}
          </p>
        ) : null}
        <Button className="w-full" type="submit" disabled={submitting}>
          <FiUserPlus /> {submitting ? 'Creating account...' : 'Create account'}
        </Button>
      </form>
      <p className="mt-5 text-center text-sm text-slate-600 dark:text-slate-400">
        Already have an account?{' '}
        <Link className="font-semibold text-slate-950 underline dark:text-white" to="/login">
          Login
        </Link>
      </p>
    </AuthFrame>
  )
}
