import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { AdminLayout } from './components/layout/AdminLayout'
import { AdminRoute } from './routes/AdminRoute'
import { ProtectedRoute } from './routes/ProtectedRoute'
import { AgentsPage } from './features/agents/AgentsPage'
import { AdminAgentsPage } from './features/admin/AdminAgentsPage'
import { AdminAppConfigPage } from './features/admin/AdminAppConfigPage'
import { AdminLlmProvidersPage } from './features/admin/AdminLlmProvidersPage'
import { AdminOverviewPage } from './features/admin/AdminOverviewPage'
import { AdminPlansPage } from './features/admin/AdminPlansPage'
import { AdminSafetyReportsPage } from './features/admin/AdminSafetyReportsPage'
import { AdminSubscriptionsPage } from './features/admin/AdminSubscriptionsPage'
import { AdminTestingLabPage } from './features/admin/AdminTestingLabPage'
import { AdminUsagePage } from './features/admin/AdminUsagePage'
import { AdminUsersPage } from './features/admin/AdminUsersPage'
import { LoginPage } from './features/auth/LoginPage'
import { RegisterPage } from './features/auth/RegisterPage'
import { ChatPage } from './features/chat/ChatPage'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { LandingPage } from './features/landing/LandingPage'
import { ProfilePage } from './features/profile/ProfilePage'
import { SafetyReportsPage } from './features/safety/SafetyReportsPage'
import { SettingsPage } from './features/settings/SettingsPage'
import { SubscriptionsPage } from './features/subscriptions/SubscriptionsPage'
import { TestingLabPage } from './features/testing/TestingLabPage'
import { UsagePage } from './features/usage/UsagePage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/onboarding/profile" element={<ProfilePage onboarding />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:sessionId" element={<ChatPage />} />
          <Route path="/usage" element={<UsagePage />} />
          <Route path="/subscriptions" element={<SubscriptionsPage />} />
          <Route path="/memory-privacy" element={<SettingsPage initialSection="privacy" />} />
          <Route path="/safety-reports" element={<SafetyReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/testing-lab" element={<TestingLabPage />} />
        </Route>
      </Route>
      <Route element={<AdminRoute />}>
        <Route element={<AdminLayout />}>
          <Route path="/admin" element={<AdminOverviewPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/agents" element={<AdminAgentsPage />} />
          <Route path="/admin/plans" element={<AdminPlansPage />} />
          <Route path="/admin/subscriptions" element={<AdminSubscriptionsPage />} />
          <Route path="/admin/usage" element={<AdminUsagePage />} />
          <Route path="/admin/safety-reports" element={<AdminSafetyReportsPage />} />
          <Route path="/admin/app-config" element={<AdminAppConfigPage />} />
          <Route path="/admin/llm-providers" element={<AdminLlmProvidersPage />} />
          <Route path="/admin/testing-lab" element={<AdminTestingLabPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
