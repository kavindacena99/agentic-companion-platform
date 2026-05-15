import { FiAlertCircle, FiInbox } from 'react-icons/fi'

export function StateBlock({ type = 'empty', title, children, action }) {
  const Icon = type === 'error' ? FiAlertCircle : FiInbox

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
      <Icon className="mx-auto mb-3 h-8 w-8 text-slate-400" />
      <h3 className="text-base font-semibold text-slate-950">{title}</h3>
      {children ? <div className="mt-2 text-sm text-slate-600">{children}</div> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}
