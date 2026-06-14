import { Link } from 'react-router-dom'
import { useExperiments } from '@/hooks/useExperiments'
import { useObservabilityCatalog, useObservabilityStatus } from '@/hooks/useObservability'
import { BackendStatusGrid } from '@/components/observability/BackendStatusGrid'
import { PageHeader, PageShell } from '@/components/layout/PageChrome'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

export function ObservabilityPage() {
  const { data: status, isLoading: statusLoading } = useObservabilityStatus()
  const { data: catalog } = useObservabilityCatalog()
  const { data: experiments } = useExperiments()

  const catalogServices = catalog ? Object.keys(catalog.services) : []
  const recentComplete = (experiments ?? []).filter((e) => e.state === 'complete').slice(0, 5)

  return (
    <PageShell>
      <PageHeader
        title="Observability"
        description="Prometheus guard, Loki log correlation, and Tempo trace search — summarized into fault-window evidence per run."
      />

      {statusLoading ? (
        <div className="grid gap-4 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
      ) : (
        <BackendStatusGrid status={status} />
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="surface-card rounded-lg p-5">
          <h2 className="text-sm font-semibold">Steady-state guard</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Baseline window → 15s evaluation → auto-abort on breach
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border border-border bg-card/40 px-3 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Error rate
              </p>
              <p className="mt-1 text-sm">Abort if &gt; 2× baseline</p>
            </div>
            <div className="rounded-md border border-border bg-card/40 px-3 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Latency p99
              </p>
              <p className="mt-1 text-sm">Abort if &gt; 3× baseline</p>
            </div>
          </div>
        </section>

        <section className="surface-card rounded-lg p-5">
          <h2 className="text-sm font-semibold">Service catalog</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Default metrics and log selectors per service
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {catalogServices.map((svc) => (
              <Badge key={svc} variant="outline" className="font-mono text-[10px]">
                {svc}
              </Badge>
            ))}
          </div>
        </section>
      </div>

      <section className="surface-card mt-6 rounded-lg">
        <div className="border-b border-border px-5 py-4">
          <h2 className="text-sm font-semibold">Runs with evidence</h2>
        </div>
        <div className="divide-y divide-border">
          {recentComplete.length === 0 ? (
            <p className="px-5 py-8 text-sm text-muted-foreground">No completed experiments yet.</p>
          ) : (
            recentComplete.map((exp) => (
              <Link
                key={exp.id}
                to={`/experiments/${exp.id}`}
                className="flex items-center justify-between px-5 py-3.5 transition-colors hover:bg-accent/50"
              >
                <div>
                  <p className="text-sm font-medium">{exp.name}</p>
                  <p className="text-xs text-muted-foreground">{exp.namespace}</p>
                </div>
                <Badge variant="outline">Evidence</Badge>
              </Link>
            ))
          )}
        </div>
      </section>
    </PageShell>
  )
}
