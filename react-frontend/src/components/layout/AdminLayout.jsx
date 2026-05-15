import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  FiActivity,
  FiBarChart2,
  FiCreditCard,
  FiFlag,
  FiHome,
  FiLogOut,
  FiMessageCircle,
  FiServer,
  FiSettings,
  FiShield,
  FiSliders,
  FiSmile,
  FiUsers,
} from 'react-icons/fi'
import { Button } from '../ui/Button'
import { useAuth } from '../../context/AuthContext'

const adminLinks = [
  { to: '/admin', label: 'Overview', icon: FiHome, end: true },
  { to: '/admin/users', label: 'Users', icon: FiUsers },
  { to: '/admin/agents', label: 'Agents', icon: FiSmile },
  { to: '/admin/plans', label: 'Plans', icon: FiCreditCard },
  { to: '/admin/subscriptions', label: 'Subscriptions', icon: FiFlag },
  { to: '/admin/usage', label: 'Usage', icon: FiBarChart2 },
  { to: '/admin/safety-reports', label: 'Safety Reports', icon: FiShield },
  { to: '/admin/app-config', label: 'App Config', icon: FiSettings },
  { to: '/admin/llm-providers', label: 'LLM Providers', icon: FiServer },
  { to: '/admin/testing-lab', label: 'Testing Lab', icon: FiSliders },
]

function AdminNavItem({ to, label, icon: Icon, end }) {
  return (
    <NavLink
      end={end}
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold transition ${
          isActive ? 'bg-cyan-400 text-slate-950' : 'text-slate-300 hover:bg-white/10 hover:text-white'
        }`
      }
    >
      <Icon className="h-4 w-4" />
      {label}
    </NavLink>
  )
}

export function AdminLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <aside className="fixed inset-y-0 left-0 hidden w-76 border-r border-slate-800 bg-slate-950 px-4 py-5 xl:block">
        <div className="mb-7 px-2 text-white">
          <p className="text-xl font-black tracking-tight">Companio Admin</p>
          <p className="mt-1 text-xs font-medium text-slate-400">Product control panel</p>
        </div>
        <nav className="space-y-1">
          {adminLinks.map((link) => (
            <AdminNavItem key={link.to} {...link} />
          ))}
        </nav>
        <div className="absolute bottom-5 left-4 right-4 rounded-2xl bg-white/10 p-4 text-white">
          <p className="text-xs text-slate-400">Admin session</p>
          <p className="mt-1 truncate text-sm font-semibold">{user?.email}</p>
          <div className="mt-4 grid grid-cols-2 gap-2">
            <NavLink
              className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl bg-white px-3 py-2 text-sm font-semibold text-slate-950"
              to="/dashboard"
            >
              <FiMessageCircle /> User app
            </NavLink>
            <Button variant="accent" onClick={handleLogout}>
              <FiLogOut /> Logout
            </Button>
          </div>
        </div>
      </aside>

      <div className="xl:pl-76">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur lg:px-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-black text-slate-950">Companio Admin</p>
              <p className="text-xs text-slate-500">Main Backend only</p>
            </div>
            <NavLink
              className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-slate-950 px-3 py-2 text-sm font-semibold text-white"
              to="/dashboard"
            >
              <FiActivity /> User app
            </NavLink>
          </div>
          <nav className="mt-3 flex gap-2 overflow-x-auto pb-1 xl:hidden">
            {adminLinks.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                end={end}
                key={to}
                to={to}
                className={({ isActive }) =>
                  `inline-flex shrink-0 items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold ${
                    isActive ? 'bg-slate-950 text-white' : 'bg-slate-100 text-slate-700'
                  }`
                }
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </NavLink>
            ))}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-7xl px-4 py-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
