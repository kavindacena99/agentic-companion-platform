import { useEffect, useState } from 'react'
import { FiBell, FiSave, FiShield, FiUser } from 'react-icons/fi'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { FormField, inputClass } from '../../components/ui/FormField'
import { useAuth } from '../../context/AuthContext'
import { useProduct } from '../../context/ProductContext'
import { useAsync } from '../../hooks/useAsync'
import { getApiErrorMessage } from '../../services/apiClient'
import { profileService } from '../../services/profileService'
import { settingsService } from '../../services/settingsService'

export function SettingsPage({ initialSection = 'account' }) {
  const [section, setSection] = useState(initialSection)
  const { user, logout } = useAuth()

  return (
    <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
      <Card className="h-fit">
        <nav className="space-y-2">
          <TabButton active={section === 'account'} icon={FiUser} label="Account" onClick={() => setSection('account')} />
          <TabButton active={section === 'privacy'} icon={FiShield} label="Memory and privacy" onClick={() => setSection('privacy')} />
          <TabButton active={section === 'notifications'} icon={FiBell} label="Notifications" onClick={() => setSection('notifications')} />
        </nav>
      </Card>
      <div className="space-y-6">
        {section === 'account' ? <AccountSection user={user} logout={logout} /> : null}
        {section === 'privacy' ? <PrivacySection /> : null}
        {section === 'notifications' ? <NotificationSection /> : null}
      </div>
    </div>
  )
}

function TabButton({ active, icon: Icon, label, onClick }) {
  return (
    <button
      className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm font-semibold ${
        active ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-slate-100'
      }`}
      onClick={onClick}
      type="button"
    >
      <Icon /> {label}
    </button>
  )
}

function AccountSection({ user, logout }) {
  return (
    <Card>
      <h1 className="text-2xl font-black">Account settings</h1>
      <div className="mt-5 grid gap-3 text-sm md:grid-cols-2">
        <Info label="Email" value={user?.email} />
        <Info label="Username" value={user?.username} />
        <Info label="Full name" value={user?.full_name || 'Not set'} />
        <Info label="Role" value={user?.role} />
      </div>
      <div className="mt-5 rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
        Delete or deactivate account is not exposed by the current Main Backend API.
      </div>
      <Button className="mt-5" variant="danger" onClick={logout}>Logout</Button>
    </Card>
  )
}

function PrivacySection() {
  const { profile, setProfile, refreshProfile } = useProduct()
  const [memoryEnabled, setMemoryEnabled] = useState(true)
  const [personalizationEnabled, setPersonalizationEnabled] = useState(true)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useAsync(refreshProfile, [refreshProfile])

  useEffect(() => {
    if (profile) {
      setMemoryEnabled(Boolean(profile.memory_enabled))
      setPersonalizationEnabled(Boolean(profile.personalization_enabled))
    }
  }, [profile])

  async function savePrivacy() {
    setSubmitting(true)
    setStatus('')
    setError('')
    try {
      const updated = await profileService.updateProfile({
        memory_enabled: memoryEnabled,
        personalization_enabled: personalizationEnabled,
      })
      setProfile(updated)
      setStatus('Privacy preferences saved.')
    } catch (caughtError) {
      setError(getApiErrorMessage(caughtError, 'Could not save privacy preferences.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card>
      <h1 className="text-2xl font-black">Memory and privacy</h1>
      <p className="mt-2 text-sm text-slate-600">Current backend support is profile-level memory and personalization toggles.</p>
      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <Toggle checked={memoryEnabled} label="Memory enabled" onChange={setMemoryEnabled} />
        <Toggle checked={personalizationEnabled} label="Personalization enabled" onChange={setPersonalizationEnabled} />
      </div>
      <div className="mt-5 rounded-2xl bg-amber-50 p-4 text-sm text-amber-900">
        Planned / waiting for backend endpoint: delete memory request, export data request, memory item review.
      </div>
      {error ? <p className="mt-4 rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{error}</p> : null}
      {status ? <p className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm font-medium text-emerald-700">{status}</p> : null}
      <Button className="mt-5" onClick={savePrivacy} disabled={submitting}>
        <FiSave /> {submitting ? 'Saving...' : 'Save privacy preferences'}
      </Button>
    </Card>
  )
}

function NotificationSection() {
  const [prefs, setPrefs] = useState(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { loading } = useAsync(async () => {
    const data = await settingsService.getNotificationPreferences()
    setPrefs(data)
    return data
  }, [])

  async function savePrefs() {
    setSubmitting(true)
    setError('')
    setStatus('')
    try {
      const updated = await settingsService.updateNotificationPreferences(prefs)
      setPrefs(updated)
      setStatus('Notification preferences saved.')
    } catch (caughtError) {
      setError(getApiErrorMessage(caughtError, 'Could not save notification preferences.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card>
      <h1 className="text-2xl font-black">Notifications</h1>
      <p className="mt-2 text-sm text-slate-600">Preferences are connected to `/api/notifications/preferences/`.</p>
      {loading || !prefs ? <p className="mt-5 text-sm text-slate-500">Loading preferences...</p> : null}
      {prefs ? (
        <div className="mt-5 space-y-3">
          {['push_enabled', 'chat_reminders_enabled', 'product_updates_enabled', 'safety_notifications_enabled', 'quiet_hours_enabled'].map((key) => (
            <Toggle
              key={key}
              checked={Boolean(prefs[key])}
              label={key.replaceAll('_', ' ')}
              onChange={(checked) => setPrefs({ ...prefs, [key]: checked })}
            />
          ))}
          <div className="grid gap-3 md:grid-cols-2">
            <FormField label="Quiet hours start">
              <input className={inputClass} type="time" value={prefs.quiet_hours_start || ''} onChange={(event) => setPrefs({ ...prefs, quiet_hours_start: event.target.value || null })} />
            </FormField>
            <FormField label="Quiet hours end">
              <input className={inputClass} type="time" value={prefs.quiet_hours_end || ''} onChange={(event) => setPrefs({ ...prefs, quiet_hours_end: event.target.value || null })} />
            </FormField>
          </div>
        </div>
      ) : null}
      {error ? <p className="mt-4 rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{error}</p> : null}
      {status ? <p className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm font-medium text-emerald-700">{status}</p> : null}
      <Button className="mt-5" onClick={savePrefs} disabled={!prefs || submitting}>
        <FiSave /> {submitting ? 'Saving...' : 'Save notification preferences'}
      </Button>
    </Card>
  )
}

function Toggle({ checked, label, onChange }) {
  return (
    <label className="flex items-center justify-between gap-3 rounded-2xl bg-slate-50 p-4">
      <span className="text-sm font-semibold capitalize text-slate-800">{label}</span>
      <input className="h-5 w-5 accent-cyan-500" type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
    </label>
  )
}

function Info({ label, value }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 font-bold text-slate-950">{value}</p>
    </div>
  )
}
