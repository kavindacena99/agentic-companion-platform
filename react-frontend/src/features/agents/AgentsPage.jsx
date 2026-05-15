import { useState } from 'react'
import { Link } from 'react-router-dom'
import { FiCheckCircle, FiLock, FiRefreshCw } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StateBlock } from '../../components/common/StateBlock'
import { useProduct } from '../../context/ProductContext'
import { useAsync } from '../../hooks/useAsync'
import { getApiErrorMessage } from '../../services/apiClient'
import { agentService } from '../../services/agentService'

export function AgentsPage() {
  const { selectedAgent, setSelectedAgent, refreshSelectedAgent } = useProduct()
  const [actionError, setActionError] = useState('')
  const [selectingKey, setSelectingKey] = useState('')
  const { data: agents, loading, error, run } = useAsync(async () => {
    await refreshSelectedAgent()
    return agentService.listAgents()
  }, [refreshSelectedAgent])

  async function selectAgent(agentKey) {
    setSelectingKey(agentKey)
    setActionError('')
    try {
      const data = await agentService.selectAgent(agentKey)
      setSelectedAgent(data)
    } catch (caughtError) {
      setActionError(getApiErrorMessage(caughtError, 'Could not select this agent.'))
    } finally {
      setSelectingKey('')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Choose your AI companion</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Availability is resolved by the Main Backend from product settings plus Agent Platform runtime status.
          </p>
        </div>
        <Button variant="secondary" onClick={run}>
          <FiRefreshCw /> Refresh
        </Button>
      </div>

      {actionError ? <p className="rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{actionError}</p> : null}
      {error ? <StateBlock type="error" title="Could not load agents">{error}</StateBlock> : null}
      {loading ? <p className="text-sm text-slate-500">Loading agents...</p> : null}

      <div className="grid gap-4 md:grid-cols-3">
        {(agents || []).map((agent) => {
          const isSelected = selectedAgent?.agent?.agent_key === agent.agent_key
          return (
            <Card key={agent.agent_key} className={`relative overflow-hidden ${isSelected ? 'ring-2 ring-cyan-400' : ''}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold">{agent.display_name}</h2>
                  <p className="mt-1 text-sm capitalize text-slate-500">{agent.agent_type}</p>
                </div>
                {isSelected ? <FiCheckCircle className="h-6 w-6 text-cyan-600" /> : null}
              </div>
              <p className="mt-4 min-h-16 text-sm leading-6 text-slate-600">{agent.short_description}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge tone={agent.is_available ? 'green' : 'rose'}>{agent.availability_status}</Badge>
                {agent.requires_premium ? <Badge tone="amber">Premium</Badge> : <Badge tone="blue">Included</Badge>}
                {agent.version ? <Badge>Runtime {agent.version}</Badge> : null}
              </div>
              <div className="mt-5">
                <Button
                  className="w-full"
                  variant={agent.is_available ? 'primary' : 'secondary'}
                  disabled={!agent.is_available || selectingKey === agent.agent_key}
                  onClick={() => selectAgent(agent.agent_key)}
                >
                  {!agent.is_available ? <FiLock /> : null}
                  {isSelected ? 'Selected' : selectingKey === agent.agent_key ? 'Selecting...' : 'Select agent'}
                </Button>
              </div>
            </Card>
          )
        })}
      </div>

      {selectedAgent?.agent ? (
        <Card className="flex flex-col justify-between gap-4 bg-cyan-50 md:flex-row md:items-center">
          <div>
            <p className="font-semibold text-slate-950">{selectedAgent.agent.display_name} is ready.</p>
            <p className="text-sm text-slate-600">Start a chat session through the Main Backend chat API.</p>
          </div>
          <Link to="/chat">
            <Button variant="accent">Go to chat</Button>
          </Link>
        </Card>
      ) : null}
    </div>
  )
}
