import { FiLock } from 'react-icons/fi'
import { Card } from '../ui/Card'

export function AdminPlaceholder({ title, children, endpoint }) {
  return (
    <Card className="border-amber-200 bg-amber-50">
      <div className="flex gap-3">
        <FiLock className="mt-1 h-5 w-5 shrink-0 text-amber-700" />
        <div>
          <h3 className="font-bold text-amber-950">{title}</h3>
          <div className="mt-2 text-sm leading-6 text-amber-900">{children}</div>
          {endpoint ? <p className="mt-3 font-mono text-xs text-amber-800">Needed endpoint: {endpoint}</p> : null}
        </div>
      </div>
    </Card>
  )
}
