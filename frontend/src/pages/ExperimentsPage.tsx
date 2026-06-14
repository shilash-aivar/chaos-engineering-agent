import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FlaskConical, Plus } from 'lucide-react'
import { useExperiments } from '@/hooks/useExperiments'
import { PageHeader, PageShell, EmptyState } from '@/components/layout/PageChrome'
import { StatusDot } from '@/components/shared/StatusDot'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { formatRelativeTime } from '@/lib/utils'
import type { ExperimentState } from '@/types'

const filters = ['all', 'running', 'complete', 'failed'] as const
type Filter = (typeof filters)[number]

const filterStates: Record<Filter, ExperimentState[] | null> = {
  all: null,
  running: ['running', 'aborting', 'simulating', 'awaiting_approval'],
  complete: ['complete'],
  failed: ['failed'],
}

export function ExperimentsPage() {
  const { data: experiments = [], isLoading } = useExperiments()
  const [filter, setFilter] = useState<Filter>('all')

  const filtered = useMemo(() => {
    const states = filterStates[filter]
    if (!states) return experiments
    return experiments.filter((e) => states.includes(e.state))
  }, [experiments, filter])

  return (
    <PageShell>
      <PageHeader
        title="Experiments"
        description="Fault injection runs with baseline capture, steady-state guard, and automatic rollback."
        action={
          <Button asChild>
            <Link to="/new">
              <Plus className="h-4 w-4" />
              New experiment
            </Link>
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        {filters.map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => setFilter(f)}
            className={`rounded-full px-3 py-1 text-xs font-medium capitalize transition-colors ${
              filter === f
                ? 'bg-primary/15 text-primary ring-1 ring-primary/30'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <section className="surface-card overflow-hidden rounded-lg">
        {isLoading ? (
          <div className="space-y-3 p-5">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={FlaskConical}
              title="No experiments match this filter"
              description="Create a scenario to test how checkout, payments, or dependencies behave under controlled failure."
              action={
                <Button asChild>
                  <Link to="/new">Compose experiment</Link>
                </Button>
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Source</th>
                  <th>Namespace</th>
                  <th>Status</th>
                  <th>Scores</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((exp) => (
                  <tr key={exp.id}>
                    <td>
                      <Link
                        to={`/experiments/${exp.id}`}
                        className="font-medium hover:text-primary"
                      >
                        {exp.name}
                      </Link>
                      <p className="mt-0.5 line-clamp-1 max-w-md text-xs text-muted-foreground">
                        {exp.hypothesis}
                      </p>
                    </td>
                    <td>
                      <Badge variant="outline" className="font-mono text-[10px]">
                        {exp.source}
                      </Badge>
                    </td>
                    <td className="font-mono text-xs text-muted-foreground">{exp.namespace}</td>
                    <td>
                      <StatusDot state={exp.state} />
                    </td>
                    <td className="text-xs">
                      {exp.red_score != null && (
                        <span className="mr-2 text-red-team">R {exp.red_score}</span>
                      )}
                      {exp.blue_score != null && (
                        <span className="text-blue-team">B {exp.blue_score}</span>
                      )}
                      {exp.red_score == null && exp.blue_score == null && (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="whitespace-nowrap text-xs text-muted-foreground">
                      {formatRelativeTime(exp.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </PageShell>
  )
}
