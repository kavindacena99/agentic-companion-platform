import { useState } from 'react'
import { FiActivity, FiRefreshCw } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { useAuth } from '../../context/AuthContext'
import { API_BASE_URL, getApiErrorMessage } from '../../services/apiClient'
import { agentService } from '../../services/agentService'
import { appConfigService } from '../../services/appConfigService'
import { chatService } from '../../services/chatService'
import { profileService } from '../../services/profileService'
import { subscriptionService } from '../../services/subscriptionService'
import { usageService } from '../../services/usageService'

const checks = [
  ['Health', appConfigService.health],
  ['Public app config', appConfigService.getPublicConfig],
  ['Profile', profileService.getProfile],
  ['Agents', agentService.listAgents],
  ['Selected agent', agentService.getSelectedAgent],
  ['Chat sessions', chatService.listSessions],
  ['Usage', usageService.getUsage],
  ['Plans', subscriptionService.listPlans],
  ['Subscription', subscriptionService.getCurrentSubscription],
]

export function TestingLabPage() {
  const { user } = useAuth()
  const [results, setResults] = useState([])
  const [running, setRunning] = useState(false)

  async function runChecks() {
    setRunning(true)
    const nextResults = []
    for (const [name, loader] of checks) {
      const startedAt = performance.now()
      try {
        const data = await loader()
        nextResults.push({
          name,
          ok: true,
          duration: Math.round(performance.now() - startedAt),
          preview: Array.isArray(data) ? `${data.length} records` : JSON.stringify(data).slice(0, 160),
        })
      } catch (error) {
        nextResults.push({
          name,
          ok: false,
          duration: Math.round(performance.now() - startedAt),
          preview: getApiErrorMessage(error),
        })
      }
      setResults([...nextResults])
    }
    setRunning(false)
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-slate-950 p-6 text-white">
        <Badge tone="blue">Backend-only QA</Badge>
        <h1 className="mt-4 text-3xl font-black tracking-tight">Testing Lab</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300">
          This area validates Main Backend API behavior for the product frontend. It does not call OpenAI,
          provider APIs, LangChain, LangGraph, vector DB, or the Agent Platform directly.
        </p>
      </section>

      <Card className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <p className="text-sm text-slate-500">API base URL</p>
          <p className="font-mono text-sm font-semibold text-slate-950">{API_BASE_URL}</p>
          <p className="mt-1 text-xs text-slate-500">Authenticated as {user?.email}</p>
        </div>
        <Button onClick={runChecks} disabled={running}>
          <FiRefreshCw /> {running ? 'Running checks...' : 'Run API checks'}
        </Button>
      </Card>

      <div className="grid gap-4">
        {results.length === 0 ? (
          <Card>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <FiActivity className="h-5 w-5 text-cyan-600" />
              Run checks to validate the current backend state.
            </div>
          </Card>
        ) : null}
        {results.map((result) => (
          <Card key={result.name}>
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
              <div>
                <h2 className="font-bold">{result.name}</h2>
                <p className="mt-1 break-words font-mono text-xs text-slate-500">{result.preview}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone={result.ok ? 'green' : 'rose'}>{result.ok ? 'OK' : 'Failed'}</Badge>
                <Badge>{result.duration}ms</Badge>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
