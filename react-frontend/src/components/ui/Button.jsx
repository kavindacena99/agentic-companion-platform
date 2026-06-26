const variants = {
  primary:
    'bg-slate-950 text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-white focus-visible:outline-slate-950',
  secondary:
    'bg-white text-slate-950 ring-1 ring-slate-200 hover:bg-slate-50 dark:bg-slate-800 dark:text-white dark:ring-slate-700 dark:hover:bg-slate-700 focus-visible:outline-slate-950',
  accent: 'bg-cyan-500 text-slate-950 hover:bg-cyan-400 focus-visible:outline-cyan-500',
  ghost:
    'text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 focus-visible:outline-slate-950',
  danger: 'bg-rose-600 text-white hover:bg-rose-500 focus-visible:outline-rose-600',
}

export function Button({
  children,
  className = '',
  variant = 'primary',
  type = 'button',
  disabled = false,
  ...props
}) {
  return (
    <button
      className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
      type={type}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}
