import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FeaturePhase, FeatureStatus } from '@/types'

export function PreviewBanner({
  className,
  phase,
  liveHint,
}: {
  className?: string
  phase?: FeaturePhase
  liveHint?: string
}) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg border border-primary/30 bg-primary/10 px-4 py-3',
        className,
      )}
    >
      <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
      <div>
        <p className="text-sm font-medium text-primary">
          UI preview{phase ? ` · Phase ${phase}` : ''} — backend coming later
        </p>
        <p className="text-xs text-muted-foreground">
          Static sample data shows the intended experience.{' '}
          {liveHint ?? 'Wire to API when the backend feature lands.'}
        </p>
      </div>
    </div>
  )
}

const statusStyles: Record<FeatureStatus, string> = {
  live: 'border-success/40 bg-success/15 text-success',
  preview: 'border-primary/40 bg-primary/15 text-primary',
  planned: 'border-muted-foreground/30 bg-muted text-muted-foreground',
}

export function PhaseBadge({
  phase,
  status,
  className,
}: {
  phase?: FeaturePhase
  status: FeatureStatus
  className?: string
}) {
  const label = status === 'live' ? 'Live' : status === 'preview' ? 'Preview' : 'Planned'
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide',
        statusStyles[status],
        className,
      )}
    >
      {phase != null && phase !== 'future' ? `P${phase} · ` : ''}
      {label}
    </span>
  )
}
