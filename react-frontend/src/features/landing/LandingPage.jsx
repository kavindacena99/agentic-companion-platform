import { Link, Navigate } from 'react-router-dom'
import { FiLock, FiMessageCircle, FiShield, FiUserPlus } from 'react-icons/fi'
import { Card } from '../../components/ui/Card'
import { useAuth } from '../../context/AuthContext'
import heroImage from '../../assets/hero.png'

export function LandingPage() {
  const { isAuthenticated } = useAuth()

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-40">
          <img className="h-full w-full object-cover" src={heroImage} alt="" />
        </div>
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950/70 via-slate-950/80 to-slate-950" />
        <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-16">
          <div className="max-w-3xl">
            <p className="mb-4 inline-flex rounded-full bg-cyan-300 px-3 py-1 text-xs font-bold uppercase tracking-wide text-slate-950">
              AI companion experience
            </p>
            <h1 className="text-5xl font-black tracking-tight sm:text-7xl">Companio</h1>
            <p className="mt-4 text-2xl font-semibold text-cyan-100">The AI person who understands you.</p>
            <p className="mt-6 max-w-2xl text-base leading-7 text-slate-200">
              Create your profile, choose an AI companion, and test long-term conversations, usage limits,
              safety reporting, and subscription behavior through the Main Backend.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                to="/register"
                className="inline-flex min-h-10 min-w-36 items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
              >
                <FiUserPlus /> Create profile
              </Link>
              <Link
                to="/login"
                className="inline-flex min-h-10 items-center justify-center rounded-xl border-2 border-white/60 px-6 py-2 text-sm font-semibold text-white transition hover:border-white hover:bg-white/10"
              >
                Sign in
              </Link>
            </div>
          </div>
          <div className="mt-14 grid gap-4 md:grid-cols-3">
            {[
              ['AI transparency', 'Every experience here is clearly disclosed as AI companion interaction.', FiShield],
              ['Backend-only AI', 'Chat, usage, safety, and agent behavior go through the Django API.', FiLock],
              ['Real UX testing', 'Designed to validate the future mobile app experience before Flutter.', FiMessageCircle],
            ].map(([title, body, Icon]) => (
              <Card key={title} className="border-white/10 bg-white/10 text-white backdrop-blur">
                <Icon className="mb-4 h-6 w-6 text-cyan-200" />
                <h2 className="font-semibold">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-200">{body}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>
    </main>
  )
}
