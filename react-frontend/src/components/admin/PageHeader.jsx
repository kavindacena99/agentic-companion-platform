export function PageHeader({ title, eyebrow = 'Admin', children, action }) {
  return (
    <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
      <div>
        <p className="text-xs font-bold uppercase tracking-wide text-cyan-700">{eyebrow}</p>
        <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950">{title}</h1>
        {children ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{children}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  )
}
