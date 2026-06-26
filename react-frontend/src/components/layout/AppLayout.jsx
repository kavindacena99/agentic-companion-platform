import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  FiBarChart2,
  FiCreditCard,
  FiHome,
  FiLifeBuoy,
  FiLogOut,
  FiMessageCircle,
  FiMonitor,
  FiMoon,
  FiSettings,
  FiShield,
  FiSliders,
  FiSmile,
  FiSun,
  FiUser,
} from 'react-icons/fi'
import { Button } from '../ui/Button'
import { useAuth } from '../../context/AuthContext'
import { useProduct } from '../../context/ProductContext'
import { useTheme } from '../../context/ThemeContext'

const links = [
  { to: '/dashboard', label: 'Home', icon: FiHome },
  { to: '/agents', label: 'Agents', icon: FiSmile },
  { to: '/chat', label: 'Chat', icon: FiMessageCircle },
  { to: '/usage', label: 'Usage', icon: FiBarChart2 },
  { to: '/subscriptions', label: 'Plans', icon: FiCreditCard },
  { to: '/memory-privacy', label: 'Privacy', icon: FiShield },
  { to: '/safety-reports', label: 'Safety', icon: FiLifeBuoy },
  { to: '/testing-lab', label: 'Testing Lab', icon: FiSliders },
  { to: '/settings', label: 'Settings', icon: FiSettings },
]

function NavItem({ to, label, icon: Icon }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition ${
          isActive
            ? 'bg-slate-950 text-white dark:bg-slate-700'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'
        }`
      }
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </NavLink>
  )
}

export function AppLayout() {
  const { user, logout } = useAuth()
  const { usage, selectedAgent } = useProduct()
  const { isDark, toggle } = useTheme()
  const navigate = useNavigate()
  const isAdmin = user?.role === 'admin' || user?.is_staff

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950 dark:bg-slate-950 dark:text-white">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-slate-200 bg-white px-4 py-5 lg:block dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-7 px-2">
          <p className="text-xl font-black tracking-tight">Companio</p>
          <p className="mt-1 text-xs font-medium text-slate-500 dark:text-slate-400">The AI person who understands you.</p>
        </div>
        <nav className="space-y-1">
          {links.map((link) => (
            <NavItem key={link.to} {...link} />
          ))}
        </nav>
        <div className="absolute bottom-5 left-4 right-4 rounded-2xl bg-slate-950 p-4 text-white dark:bg-slate-800">
          <p className="text-xs text-slate-300">Signed in as</p>
          <p className="mt-1 truncate text-sm font-semibold">{user?.email}</p>
          <Button className="mt-4 w-full" variant="accent" onClick={handleLogout}>
            <FiLogOut /> Logout
          </Button>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur lg:px-8 dark:border-slate-800 dark:bg-slate-950/90">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-950 dark:text-white">Companio</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {selectedAgent?.agent?.display_name
                  ? `Selected: ${selectedAgent.agent.display_name}`
                  : 'Choose an AI companion to begin'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {usage ? (
                <div className="hidden rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 sm:block dark:bg-slate-800 dark:text-slate-300">
                  {usage.remaining_messages}/{usage.message_limit} messages left
                </div>
              ) : null}
              <button
                onClick={toggle}
                className="grid h-10 w-10 place-items-center rounded-full text-slate-600 transition hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {isDark ? <FiSun className="h-4 w-4" /> : <FiMoon className="h-4 w-4" />}
              </button>
              <NavLink
                to="/profile"
                className="grid h-10 w-10 place-items-center rounded-full bg-slate-950 text-white dark:bg-slate-700"
                title="Profile"
              >
                <FiUser />
              </NavLink>
              {isAdmin ? (
                <NavLink
                  to="/admin"
                  className="hidden min-h-10 items-center gap-2 rounded-xl bg-cyan-400 px-3 py-2 text-sm font-semibold text-slate-950 sm:inline-flex"
                >
                  <FiMonitor /> Admin
                </NavLink>
              ) : null}
            </div>
          </div>
          <nav className="mt-3 flex gap-2 overflow-x-auto pb-1 lg:hidden">
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `inline-flex shrink-0 items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold ${
                    isActive
                      ? 'bg-slate-950 text-white dark:bg-slate-700'
                      : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
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
