interface ScanStatusProps {
  status: 'pending' | 'running' | 'completed' | 'failed'
  error?: string
}

export function ScanStatus({ status, error }: ScanStatusProps) {
  const statusConfig = {
    pending: { label: 'Pending', color: 'text-slate-400', icon: '○' },
    running: { label: 'Running', color: 'text-cyan-400', icon: '◐', animate: true },
    completed: { label: 'Completed', color: 'text-emerald-400', icon: '✓' },
    failed: { label: 'Failed', color: 'text-red-400', icon: '✕' },
  }

  const config = statusConfig[status]

  return (
    <div className="flex items-center gap-3">
      <span className={`text-lg ${config.color} ${(config as { animate?: boolean }).animate ? 'animate-spin' : ''}`}>
        {(config as { icon?: string }).icon}
      </span>
      <span className={config.color}>{(config as { label?: string }).label}</span>
      {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
    </div>
  )
}
