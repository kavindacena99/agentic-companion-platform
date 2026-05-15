export function LoadingScreen({ label = 'Loading' }) {
  return (
    <div className="grid min-h-screen place-items-center bg-slate-950 px-6 text-white">
      <div className="text-center">
        <div className="mx-auto mb-5 h-12 w-12 animate-spin rounded-full border-2 border-white/20 border-t-cyan-300" />
        <p className="text-sm font-medium text-slate-200">{label}</p>
      </div>
    </div>
  )
}
