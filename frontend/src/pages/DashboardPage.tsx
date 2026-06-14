import { Link } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  FlaskConical,
  Plus,
  Shield,
  Swords,
  Zap,
} from 'lucide-react'
import { useDashboard } from '@/hooks/useDashboard'
import { PageHeader, PageShell, StatCard, EmptyState } from '@/components/layout/PageChrome'
import { StatusDot } from '@/components/shared/StatusDot'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { formatRelativeTime } from '@/lib/utils'
import { useAppStore } from '@/store/appStore'

export function DashboardPage() {
  const context = useAppStore((s) => s.context)
  const { stats, experiments, postureGaps, activeCampaign, isLoading } = useDashboard()

  const running = experiments.filter((e) => e.state === 'running' || e.state === 'aborting')
  const recent = experiments.slice(0, 6)
  const criticalGaps = postureGaps.filter((g) => g.severity === 'critical' || g.severity === 'high').slice(0, 4)

  if (isLoading) {
    return (
      <PageShell>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
        <Skeleton className="mt-6 h-80 rounded-lg" />
      </PageShell>
    )
  }

  return (
    <PageShell>
      <PageHeader
        title="Control overview"
        description={`${context.cluster} · ${context.namespace} — steady-state guard armed, staging-only injects by default.`}
        badge={
          <Badge variant="outline" className="font-mono text-[10px]">
            {context.environment}
          </Badge>
        }
        action={
          <Button asChild>
            <Link to="/new">
              <Plus className="h-4 w-4" />
              Compose experiment
            </Link>
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={FlaskConical}
          label="Total experiments"
          value={stats?.experiments_total ?? 0}
          hint={stats?.last_experiment_at ? `Last ${formatRelativeTime(stats.last_experiment_at)}` : undefined}
          accent="amber"
        />
        <StatCard
          icon={Activity}
          label="Active runs"
          value={stats?.experiments_running ?? running.length}
          hint={running.length > 0 ? `${running.length} need attention` : 'All clear'}
          accent={running.length > 0 ? 'amber' : 'teal'}
        />
        <StatCard
          icon={Shield}
          label="Resilience score"
          value={stats?.avg_resilience_score ?? '—'}
          hint="Rolling 30-day average"
          accent="teal"
        />
        <StatCard
          icon={AlertTriangle}
          label="Posture gaps"
          value={stats?.posture_gaps ?? postureGaps.length}
          hint={`${criticalGaps.length} high/critical`}
          accent={criticalGaps.length > 0 ? 'rose' : 'neutral'}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <section className="surface-card lg:col-span-2 rounded-lg">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <div>
              <h2 className="text-sm font-semibold">Recent experiments</h2>
              <p className="text-xs text-muted-foreground">Live runs and completed fault injections</p>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/experiments">
                View all <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>

          {recent.length === 0 ? (
            <div className="p-6">
              <EmptyState
                icon={Zap}
                title="No experiments yet"
                description="Compose your first fault scenario against staging. The orchestrator captures baseline, injects safely, and rolls back on breach."
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
                    <th>Experiment</th>
                    <th>Namespace</th>
                    <th>Status</th>
                    <th>Started</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((exp) => (
                    <tr key={exp.id}>
                      <td>
                        <Link
                          to={`/experiments/${exp.id}`}
                          className="font-medium text-foreground hover:text-primary"
                        >
                          {exp.name}
                        </Link>
                        <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{exp.hypothesis}</p>
                      </td>
                      <td className="font-mono text-xs text-muted-foreground">{exp.namespace}</td>
                      <td>
                        <StatusDot state={exp.state} />
                      </td>
                      <td className="text-xs text-muted-foreground whitespace-nowrap">
                        {formatRelativeTime(exp.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <div className="flex flex-col gap-6">
          <section className="surface-card rounded-lg p-5">
            <div className="mb-4 flex items-center gap-2">
              <Swords className="h-4 w-4 text-red-team" />
              <h2 className="text-sm font-semibold">Red vs Blue</h2>
            </div>
            {activeCampaign ? (
              <div className="space-y-4">
                <p className="font-medium">{activeCampaign.name}</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg border border-red-team/20 bg-red-team/5 px-3 py-3 text-center">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-red-team">Red</p>
                    <p className="text-2xl font-bold text-red-team">{activeCampaign.red_score}</p>
                  </div>
                  <div className="rounded-lg border border-blue-team/20 bg-blue-team/5 px-3 py-3 text-center">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-blue-team">Blue</p>
                    <p className="text-2xl font-bold text-blue-team">{activeCampaign.blue_score}</p>
                  </div>
                </div>
                <Button variant="outline" className="w-full" asChild>
                  <Link to="/red-blue">Open campaign</Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  No active campaign. Run adversarial rounds to score detection and recovery.
                </p>
                <Button variant="red" className="w-full" asChild>
                  <Link to="/red-blue">Start campaign</Link>
                </Button>
              </div>
            )}
          </section>

          <section className="surface-card rounded-lg p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Posture alerts</h2>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/posture">Scan</Link>
              </Button>
            </div>
            <div className="space-y-2">
              {criticalGaps.length === 0 ? (
                <p className="text-sm text-muted-foreground">No critical gaps in latest scan.</p>
              ) : (
                criticalGaps.map((gap) => (
                  <div
                    key={gap.id}
                    className="rounded-md border border-border bg-card/40 px-3 py-2.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium">{gap.service}</p>
                      <Badge variant={gap.severity === 'critical' ? 'destructive' : 'warning'}>
                        {gap.severity}
                      </Badge>
                    </div>
                    <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{gap.message}</p>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>
      </div>
    </PageShell>
  )
}
