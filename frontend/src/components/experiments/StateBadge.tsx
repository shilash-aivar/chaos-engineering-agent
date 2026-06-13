import type { ExperimentState } from '@/types'
import { Badge } from '@/components/ui/badge'

const stateVariant: Record<
  ExperimentState,
  'default' | 'success' | 'warning' | 'destructive' | 'secondary'
> = {
  pending: 'secondary',
  simulating: 'default',
  awaiting_approval: 'warning',
  running: 'default',
  aborting: 'warning',
  complete: 'success',
  failed: 'destructive',
}

export function StateBadge({ state }: { state: ExperimentState }) {
  return (
    <Badge variant={stateVariant[state]} className="capitalize">
      {state.replace('_', ' ')}
    </Badge>
  )
}
