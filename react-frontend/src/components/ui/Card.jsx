export function Card({ children, className = '', style }) {
  return (
    <section
      style={style}
      className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900 ${className}`}
    >
      {children}
    </section>
  )
}
