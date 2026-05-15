/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { FiAlertTriangle, FiMessageCircle, FiPlus, FiSend } from 'react-icons/fi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { FormField, inputClass } from '../../components/ui/FormField'
import { StateBlock } from '../../components/common/StateBlock'
import { useProduct } from '../../context/ProductContext'
import { getApiErrorMessage } from '../../services/apiClient'
import { chatService } from '../../services/chatService'
import { safetyService } from '../../services/safetyService'

const reportCategories = [
  ['unsafe_response', 'Unsafe response'],
  ['harmful_advice', 'Harmful advice'],
  ['emotional_manipulation', 'Emotional manipulation'],
  ['dependency_concern', 'Dependency concern'],
  ['sexual_content', 'Sexual content'],
  ['harassment', 'Harassment'],
  ['privacy_concern', 'Privacy concern'],
  ['other', 'Other'],
]

export function ChatPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const { selectedAgent, usage, setUsage, refreshSelectedAgent, refreshUsage } = useProduct()
  const [sessions, setSessions] = useState([])
  const [messages, setMessages] = useState([])
  const [session, setSession] = useState(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [reportMessage, setReportMessage] = useState(null)
  const listEndRef = useRef(null)

  const activeSessionId = sessionId ? Number(sessionId) : null

  useEffect(() => {
    loadBase()
  }, [])

  useEffect(() => {
    if (activeSessionId) {
      loadSession(activeSessionId)
    } else {
      setSession(null)
      setMessages([])
    }
  }, [activeSessionId])

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, sending])

  async function loadBase() {
    setLoading(true)
    setError('')
    try {
      const [sessionList] = await Promise.all([chatService.listSessions(), refreshSelectedAgent(), refreshUsage()])
      setSessions(sessionList)
    } catch (caughtError) {
      setError(getApiErrorMessage(caughtError, 'Could not load chat.'))
    } finally {
      setLoading(false)
    }
  }

  async function loadSession(id) {
    setError('')
    try {
      const [sessionData, messageList] = await Promise.all([chatService.getSession(id), chatService.listMessages(id)])
      setSession(sessionData)
      setMessages(messageList)
    } catch (caughtError) {
      setError(getApiErrorMessage(caughtError, 'Could not load this chat session.'))
    }
  }

  async function createSession() {
    setError('')
    try {
      const payload = selectedAgent?.agent?.agent_key ? { agent_key: selectedAgent.agent.agent_key } : {}
      const newSession = await chatService.createSession(payload)
      setSessions((current) => [newSession, ...current])
      navigate(`/chat/${newSession.id}`)
    } catch (caughtError) {
      setError(getApiErrorMessage(caughtError, 'Select an available agent before starting a chat.'))
    }
  }

  async function sendMessage(event) {
    event.preventDefault()
    if (!message.trim() || !activeSessionId) return

    const outgoing = message.trim()
    setMessage('')
    setSending(true)
    setError('')

    try {
      const response = await chatService.sendMessage(activeSessionId, outgoing)
      setMessages((current) => [...current, response.user_message, response.agent_message])
      setUsage(response.usage)
      const sessionList = await chatService.listSessions()
      setSessions(sessionList)
    } catch (caughtError) {
      const apiMessage = getApiErrorMessage(caughtError, 'Agent response failed. Please try again.')
      setError(apiMessage)
      if (caughtError.response?.status === 429 && caughtError.response.data?.usage) {
        setUsage(caughtError.response.data.usage)
      }
      setMessage(outgoing)
    } finally {
      setSending(false)
    }
  }

  const canSend = useMemo(() => Boolean(activeSessionId && usage?.can_send_message !== false), [activeSessionId, usage])

  return (
    <div className="grid min-h-[calc(100vh-150px)] gap-5 lg:grid-cols-[320px_1fr]">
      <Card className="flex flex-col">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold">Chats</h1>
            <p className="text-sm text-slate-500">Backend chat sessions</p>
          </div>
          <Button variant="accent" onClick={createSession}>
            <FiPlus /> New
          </Button>
        </div>

        {selectedAgent?.agent ? (
          <div className="mt-4 rounded-2xl bg-cyan-50 p-3">
            <p className="text-sm font-semibold">{selectedAgent.agent.display_name}</p>
            <p className="text-xs text-slate-600">{selectedAgent.agent.availability_status}</p>
          </div>
        ) : (
          <StateBlock
            title="No agent selected"
            action={
              <Link to="/agents">
                <Button variant="secondary">Choose agent</Button>
              </Link>
            }
          >
            Select Best Friend, Girlfriend, or Boyfriend before creating a chat.
          </StateBlock>
        )}

        <div className="mt-4 flex-1 space-y-2 overflow-y-auto">
          {loading ? <p className="text-sm text-slate-500">Loading sessions...</p> : null}
          {!loading && sessions.length === 0 ? (
            <p className="rounded-xl bg-slate-50 p-3 text-sm text-slate-500">No sessions yet.</p>
          ) : null}
          {sessions.map((item) => (
            <Link
              className={`block rounded-2xl border p-3 transition ${
                Number(sessionId) === item.id ? 'border-cyan-300 bg-cyan-50' : 'border-slate-200 hover:bg-slate-50'
              }`}
              key={item.id}
              to={`/chat/${item.id}`}
            >
              <p className="truncate text-sm font-semibold text-slate-950">{item.title}</p>
              <p className="text-xs text-slate-500">{item.agent_display_name}</p>
            </Link>
          ))}
        </div>
      </Card>

      <Card className="flex min-h-[620px] flex-col p-0">
        <div className="border-b border-slate-200 p-4">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h2 className="text-lg font-bold">{session?.title || 'Select or start a chat'}</h2>
              <p className="text-sm text-slate-500">
                AI companion responses are generated through the Main Backend only.
              </p>
            </div>
            {usage ? (
              <Badge tone={usage.can_send_message ? 'green' : 'rose'}>
                {usage.remaining_messages}/{usage.message_limit} left
              </Badge>
            ) : null}
          </div>
        </div>

        {error ? <p className="m-4 rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{error}</p> : null}

        <div className="flex-1 space-y-4 overflow-y-auto bg-slate-50 p-4">
          {!activeSessionId ? (
            <StateBlock
              title="Ready when you are"
              action={
                <Button onClick={createSession}>
                  <FiMessageCircle /> Start new chat
                </Button>
              }
            >
              Choose an agent and create a backend chat session to begin.
            </StateBlock>
          ) : null}

          {activeSessionId && messages.length === 0 && !loading ? (
            <StateBlock title="No messages yet">Send the first message to test the agent response flow.</StateBlock>
          ) : null}

          {messages.map((item) => (
            <MessageBubble key={item.id} message={item} onReport={() => setReportMessage(item)} />
          ))}
          {sending ? (
            <div className="max-w-[78%] rounded-2xl bg-white p-4 text-sm text-slate-500 shadow-sm">
              Waiting for agent response...
            </div>
          ) : null}
          <div ref={listEndRef} />
        </div>

        <form className="border-t border-slate-200 p-4" onSubmit={sendMessage}>
          {!canSend && activeSessionId ? (
            <p className="mb-3 rounded-xl bg-amber-50 p-3 text-sm font-medium text-amber-800">
              Usage limit reached for today. Check Usage or Plans for the current backend state.
            </p>
          ) : null}
          <div className="flex gap-2">
            <input
              className={inputClass}
              disabled={!activeSessionId || sending || !canSend}
              maxLength={4000}
              placeholder="Message your Companio agent..."
              value={message}
              onChange={(event) => setMessage(event.target.value)}
            />
            <Button type="submit" disabled={!message.trim() || !activeSessionId || sending || !canSend}>
              <FiSend /> Send
            </Button>
          </div>
        </form>
      </Card>

      {reportMessage ? <SafetyReportModal message={reportMessage} onClose={() => setReportMessage(null)} /> : null}
    </div>
  )
}

function MessageBubble({ message, onReport }) {
  const isUser = message.sender === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <article
        className={`max-w-[84%] rounded-2xl p-4 shadow-sm ${
          isUser ? 'bg-slate-950 text-white' : 'bg-white text-slate-950'
        }`}
      >
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{isUser ? 'You' : 'Companio agent'}</p>
          <p className="text-xs opacity-60">{new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
        </div>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{message.content}</p>
        {!isUser ? (
          <div className="mt-3 flex items-center justify-between gap-3">
            <Badge tone={message.safety_status === 'safe' ? 'green' : 'amber'}>{message.safety_status}</Badge>
            <button className="inline-flex items-center gap-1 text-xs font-semibold text-rose-600" onClick={onReport} type="button">
              <FiAlertTriangle /> Report
            </button>
          </div>
        ) : null}
      </article>
    </div>
  )
}

function SafetyReportModal({ message, onClose }) {
  const [category, setCategory] = useState('unsafe_response')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function submitReport(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setStatus('')
    try {
      await safetyService.createReport({ message_id: message.id, category, description })
      setStatus('Report submitted for review.')
      setTimeout(onClose, 800)
    } catch (caughtError) {
      setError(getApiErrorMessage(caughtError, 'Could not submit safety report.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/60 px-4">
      <Card className="w-full max-w-lg">
        <h2 className="text-xl font-bold">Report unsafe response</h2>
        <p className="mt-2 text-sm text-slate-600">This submits a SafetyReport through `/api/safety-reports/`.</p>
        <form className="mt-5 space-y-4" onSubmit={submitReport}>
          <FormField label="Category">
            <select className={inputClass} value={category} onChange={(event) => setCategory(event.target.value)}>
              {reportCategories.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Notes">
            <textarea
              className={`${inputClass} min-h-28`}
              maxLength={1000}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </FormField>
          {error ? <p className="rounded-xl bg-rose-50 p-3 text-sm font-medium text-rose-700">{error}</p> : null}
          {status ? <p className="rounded-xl bg-emerald-50 p-3 text-sm font-medium text-emerald-700">{status}</p> : null}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={submitting}>{submitting ? 'Submitting...' : 'Submit report'}</Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
