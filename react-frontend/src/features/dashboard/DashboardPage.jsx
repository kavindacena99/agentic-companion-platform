import { Link } from 'react-router-dom'
import { FiArrowRight, FiMessageCircle, FiShield, FiSmile } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useAuth } from '../../context/AuthContext'
import { useProduct } from '../../context/ProductContext'
import { useAsync } from '../../hooks/useAsync'
import { chatService } from '../../services/chatService'

export function DashboardPage() {
  const { user } = useAuth()
  const product = useProduct()
  const { data: sessions, loading } = useAsync(async () => {
    await product.refreshProductState()
    return chatService.listSessions()
  }, [product.refreshProductState])

  const recentSessions = sessions?.slice(0, 3) || []
  const displayName = product.profile?.display_name || user?.full_name || user?.username || 'there'

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-slate-950 p-6 text-white shadow-sm md:p-8">
        <div className="grid gap-6 lg:grid-cols-[1fr_320px] lg:items-end">
          <div>
            <Badge tone="blue">Product testing frontend</Badge>
            <h1 className="mt-5 text-3xl font-black tracking-tight md:text-5xl">Hi {displayName}, welcome to Companio.</h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-300">
              Validate onboarding, agent selection, chat responses, usage limits, subscriptions, and safety
              reports through the Main Backend before the Flutter app is built.
            </p>
          </div>
          <div className="rounded-2xl bg-white/10 p-4">
            <p className="text-sm font-semibold">AI transparency</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Companio agents are AI companions. They are not humans, medical providers, or emergency services.
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Selected agent" value={product.selectedAgent?.agent?.display_name || 'Not selected'} icon={FiSmile} to="/agents" />
        <MetricCard
          label="Messages left today"
          value={product.usage ? `${product.usage.remaining_messages}/${product.usage.message_limit}` : 'Loading'}
          icon={FiMessageCircle}
          to="/usage"
        />
        <MetricCard label="Current plan" value={product.subscription?.plan_name || 'Free'} icon={FiShield} to="/subscriptions" />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <Card>
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold">Recent chats</h2>
              <p className="text-sm text-slate-500">Continue a session or start a new conversation.</p>
            </div>
            <Link to="/chat">
              <Button variant="secondary">Open chat</Button>
            </Link>
          </div>
          <div className="mt-5 space-y-3">
            {loading ? <p className="text-sm text-slate-500">Loading sessions...</p> : null}
            {!loading && recentSessions.length === 0 ? (
              <StateBlock title="No chat sessions yet">Choose an agent and start your first Companio conversation.</StateBlock>
            ) : null}
            {recentSessions.map((session) => (
              <Link
                className="flex items-center justify-between rounded-2xl border border-slate-200 p-4 transition hover:border-cyan-300 hover:bg-cyan-50/40"
                key={session.id}
                to={`/chat/${session.id}`}
              >
                <div>
                  <p className="font-semibold text-slate-950">{session.title}</p>
                  <p className="text-sm text-slate-500">{session.agent_display_name}</p>
                </div>
                <FiArrowRight className="text-slate-400" />
              </Link>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="text-lg font-bold">Readiness checklist</h2>
          <div className="mt-4 space-y-3">
            <ChecklistItem done={Boolean(product.profile?.profile_completed)} label="Profile completed" to="/profile" />
            <ChecklistItem done={Boolean(product.selectedAgent?.agent)} label="Agent selected" to="/agents" />
            <ChecklistItem done={Boolean(sessions?.length)} label="Chat flow tested" to="/chat" />
            <ChecklistItem done={Boolean(product.subscription)} label="Subscription status loaded" to="/subscriptions" />
          </div>
        </Card>
      </div>
    </div>
  )
}

function MetricCard({ label, value, icon: Icon, to }) {
  return (
    <Link to={to}>
      <Card className="h-full transition hover:border-cyan-300 hover:shadow-md">
        <Icon className="mb-4 h-6 w-6 text-cyan-600" />
        <p className="text-sm text-slate-500">{label}</p>
        <p className="mt-1 text-xl font-bold text-slate-950">{value}</p>
      </Card>
    </Link>
  )
}

function ChecklistItem({ done, label, to }) {
  return (
    <Link className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2" to={to}>
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <Badge tone={done ? 'green' : 'amber'}>{done ? 'Done' : 'Needs test'}</Badge>
    </Link>
  )
}
