import { cn } from '@/lib/utils'
import type { ExperimentState } from '@/types'

const stateConfig: Record<
  ExperimentState,
  { dot: string; label: string; pulse?: boolean }
> = {
  pending: { dot: 'bg-muted-foreground', label: 'Pending' },
  simulating: { dot: 'bg-blue-team', label: 'Simulating', pulse: true },
  awaiting_approval: { dot: 'bg-warning', label: 'Awaiting approval', pulse: true },
  running: { dot: 'bg-primary', label: 'Running', pulse: true },
  aborting: { dot: 'bg-warning', label: 'Aborting', pulse: true },
  complete: { dot: 'bg-success', label: 'Complete' },
  failed: { dot: 'bg-destructive', label: 'Failed' },
}

export function StatusDot({
  state,
  showLabel = true,
  className,
}: {
  state: ExperimentState
  showLabel?: boolean
  className?: string
}) {
  const cfg = stateConfig[state]
  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      <span
        className={cn(
          'status-dot',
          cfg.dot,
          cfg.pulse && 'status-dot--pulse',
        )}
        style={{ color: 'currentColor' }}
      />
      {showLabel && (
        <span className="text-xs font-medium text-foreground">{cfg.label}</span>
      )}
    </span>
  )
}
