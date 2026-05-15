import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiSave } from 'react-icons/fi'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { FormField, inputClass } from '../../components/ui/FormField'
import { useProduct } from '../../context/ProductContext'
import { useAsync } from '../../hooks/useAsync'
import { getApiErrorMessage } from '../../services/apiClient'
import { profileService } from '../../services/profileService'

const blankProfile = {
  display_name: '',
  birth_date: '',
  gender: '',
  country: '',
  preferred_language: 'en',
  timezone: 'Asia/Colombo',
  memory_enabled: true,
  personalization_enabled: true,
}

export function ProfilePage({ onboarding = false }) {
  const { setProfile, refreshProfile } = useProduct()
  const [form, setForm] = useState(blankProfile)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const { data, loading } = useAsync(refreshProfile, [refreshProfile])

  useEffect(() => {
    if (data) {
      setForm({
        display_name: data.display_name || '',
        birth_date: data.birth_date || '',
        gender: data.gender || '',
        country: data.country || '',
        preferred_language: data.preferred_language || 'en',
        timezone: data.timezone || 'Asia/Colombo',
        memory_enabled: Boolean(data.memory_enabled),
        personalization_enabled: Boolean(data.personalization_enabled),
      })
    }
  }, [data])

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setStatus('')
    try {
      const updated = await profileService.updateProfile(form)
      setProfile(updated)
      setStatus('Profile saved.')
      if (onboarding) navigate('/agents')
    } catch (caughtError) {
      setError(getApiErrorMessage(caughtError, 'Profile update failed.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-black tracking-tight">{onboarding ? 'Set up your profile' : 'Profile'}</h1>
        <p className="mt-2 text-sm text-slate-600">
          These fields match the Main Backend profile serializer. Profile completion requires display name,
          preferred language, and timezone.
        </p>
      </div>

      <Card>
        {loading ? <p className="text-sm text-slate-500">Loading profile...</p> : null}
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
          <FormField label="Display name">
            <input className={inputClass} value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} />
          </FormField>
          <FormField label="Birth date">
            <input className={inputClass} type="date" value={form.birth_date || ''} onChange={(event) => setForm({ ...form, birth_date: event.target.value })} />
          </FormField>
          <FormField label="Gender">
            <select className={inputClass} value={form.gender} onChange={(event) => setForm({ ...form, gender: event.target.value })}>
              <option value="">Prefer not set</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </select>
          </FormField>
          <FormField label="Country">
            <input className={inputClass} value={form.country} onChange={(event) => setForm({ ...form, country: event.target.value })} />
          </FormField>
          <FormField label="Preferred language">
            <input className={inputClass} value={form.preferred_language} onChange={(event) => setForm({ ...form, preferred_language: event.target.value })} />
          </FormField>
          <FormField label="Timezone">
            <input className={inputClass} value={form.timezone} onChange={(event) => setForm({ ...form, timezone: event.target.value })} />
          </FormField>

          <div className="md:col-span-2 grid gap-3 rounded-2xl bg-slate-50 p-4 md:grid-cols-2">
            <Toggle
              checked={form.memory_enabled}
              label="Memory enabled"
              onChange={(checked) => setForm({ ...form, memory_enabled: checked })}
            />
            <Toggle
              checked={form.personalization_enabled}
              label="Personalization enabled"
              onChange={(checked) => setForm({ ...form, personalization_enabled: checked })}
            />
          </div>

          {error ? <p className="md:col-span-2 rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{error}</p> : null}
          {status ? <p className="md:col-span-2 rounded-xl bg-emerald-50 p-3 text-sm font-medium text-emerald-700">{status}</p> : null}

          <div className="md:col-span-2 flex justify-end">
            <Button type="submit" disabled={submitting}>
              <FiSave /> {submitting ? 'Saving...' : onboarding ? 'Save and choose agent' : 'Save profile'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

function Toggle({ checked, label, onChange }) {
  return (
    <label className="flex items-center justify-between gap-3 rounded-xl bg-white p-3">
      <span className="text-sm font-semibold text-slate-800">{label}</span>
      <input
        className="h-5 w-5 accent-cyan-500"
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
    </label>
  )
}
