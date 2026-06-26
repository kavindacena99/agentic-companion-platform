import { FiAlertCircle, FiInbox } from 'react-icons/fi'

export function StateBlock({ type = 'empty', title, children, action }) {
  const Icon = type === 'error' ? FiAlertCircle : FiInbox

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <Icon className="mx-auto mb-3 h-8 w-8 text-slate-400 dark:text-slate-500" />
      <h3 className="text-base font-semibold text-slate-950 dark:text-white">{title}</h3>
      {children ? <div className="mt-2 text-sm text-slate-600 dark:text-slate-400">{children}</div> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}
