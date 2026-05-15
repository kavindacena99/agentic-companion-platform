const tones = {
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  blue: 'bg-cyan-50 text-cyan-700 ring-cyan-200',
  amber: 'bg-amber-50 text-amber-800 ring-amber-200',
  rose: 'bg-rose-50 text-rose-700 ring-rose-200',
  slate: 'bg-slate-100 text-slate-700 ring-slate-200',
}

export function Badge({ children, tone = 'slate' }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tones[tone]}`}>
      {children}
    </span>
  )
}
