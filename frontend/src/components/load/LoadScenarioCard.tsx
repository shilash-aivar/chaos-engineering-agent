import type { LoadTestScenario, LoadTestType } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'

const typeVariant: Record<LoadTestType, 'default' | 'warning' | 'success' | 'secondary'> = {
  load: 'default',
  stress: 'warning',
  performance: 'success',
  soak: 'secondary',
}

type ScenarioInput = Partial<LoadTestScenario> & {
  id: string
  name: string
  type: LoadTestType
  hypothesis?: string
  goal?: string
  status?: string
}

export function LoadScenarioCard({ scenario }: { scenario: ScenarioInput }) {
  const r = scenario.last_result
  const goal = scenario.goal ?? scenario.hypothesis ?? ''

  return (
    <div className="surface-card rounded-lg p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-medium">{scenario.name}</p>
            <Badge variant={typeVariant[scenario.type]}>{scenario.type}</Badge>
            {scenario.status && <Badge variant="outline">{scenario.status}</Badge>}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {scenario.target ?? 'checkout'} · {scenario.vus ?? 0} VUs · {scenario.duration ?? '5m'}
          </p>
          {goal && <p className="mt-1 text-xs text-foreground/80">{goal}</p>}
        </div>
        <Badge variant="outline">k6</Badge>
      </div>

      {scenario.paired_fault && (
        <p className="mt-2 rounded border border-primary/20 bg-primary/5 px-2 py-1 text-[10px] text-primary">
          + fault: {scenario.paired_fault}
        </p>
      )}

      {scenario.stages && scenario.stages.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {scenario.stages.map((s, i) => (
            <span
              key={i}
              className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
            >
              {s.duration}→{s.target}VU
            </span>
          ))}
        </div>
      )}

      {r ? (
        <div className="mt-3 grid grid-cols-2 gap-2 text-center text-xs sm:grid-cols-5">
          <div className="rounded border border-border p-2">
            <p className="text-muted-foreground">RPS</p>
            <p className="font-bold">{r.rps}</p>
          </div>
          <div className="rounded border border-border p-2">
            <p className="text-muted-foreground">p99</p>
            <p className="font-bold">{r.p99_ms}ms</p>
          </div>
        </div>
      ) : (
        <p className="mt-2 text-xs text-muted-foreground">Not run yet — pair with compose experiment</p>
      )}

      <div className="mt-3 flex gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link to="/new">Use in experiment</Link>
        </Button>
      </div>
    </div>
  )
}
