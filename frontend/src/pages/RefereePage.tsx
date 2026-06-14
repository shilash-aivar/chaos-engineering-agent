import { PageHeader, PageShell } from '@/components/layout/PageChrome'
import { useFreezeCalendar, useRefereeScoring } from '@/hooks/usePlatform'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

export function RefereePage() {
  const scoring = useRefereeScoring()
  const freeze = useFreezeCalendar()

  if (scoring.isLoading || freeze.isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-96 rounded-lg" />
      </PageShell>
    )
  }

  return (
    <PageShell>
      <PageHeader
        title="Referee"
        description="Deterministic scoring and freeze calendar — objective gate, not LLM."
        badge={
          freeze.data?.blocked ? (
            <Badge variant="warning">freeze active</Badge>
          ) : (
            <Badge variant="success">experiments allowed</Badge>
          )
        }
      />

      {freeze.data?.active_reason && (
        <div className="mb-6 rounded-lg border border-warning/40 bg-warning/10 px-4 py-3 text-sm">
          <span className="font-medium text-warning">Freeze active:</span>{' '}
          <span className="text-muted-foreground">{freeze.data.active_reason}</span>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="surface-card rounded-lg">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-sm font-semibold">Red vs Blue scoring weights</h2>
          </div>
          <div className="divide-y divide-border">
            {(scoring.data ?? []).map((row) => (
              <div key={row.metric} className="px-5 py-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">{row.metric}</p>
                  <Badge variant="outline">{row.weight}%</Badge>
                </div>
                <div className="mt-2 grid gap-1 text-[10px] text-muted-foreground sm:grid-cols-2">
                  <p><span className="text-red-team">Red:</span> {row.red}</p>
                  <p><span className="text-blue-team">Blue:</span> {row.blue}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="surface-card rounded-lg">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-sm font-semibold">Freeze calendar</h2>
          </div>
          <div className="divide-y divide-border">
            {(freeze.data?.windows ?? []).map((window) => (
              <div key={window.label} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
                <div>
                  <p className="text-sm font-medium">{window.label}</p>
                  <p className="text-xs text-muted-foreground">{window.schedule}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-muted-foreground">{window.next}</span>
                  <Badge variant={window.enforced ? 'warning' : 'secondary'}>
                    {window.enforced ? 'enforced' : 'advisory'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="surface-card mt-6 rounded-lg p-5">
        <h2 className="text-sm font-semibold">Round orchestration</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-4 text-sm text-muted-foreground">
          <li>Red agent proposes attack from posture + framework</li>
          <li>Fault injected via experiment orchestrator (when enabled)</li>
          <li>Steady-state guard monitors SLO breach</li>
          <li>Blue agent drafts defense → GitHub PR</li>
          <li>Referee scores round → equilibrium exports to regression suite</li>
        </ol>
      </section>
    </PageShell>
  )
}
