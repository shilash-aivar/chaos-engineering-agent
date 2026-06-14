import { Link } from 'react-router-dom'
import { AlertTriangle, Cloud, Database, GitBranch, Loader2, RefreshCw, Server } from 'lucide-react'
import { demoBootstrapActions } from '@/demo/mockData'
import { usePostureScan } from '@/hooks/usePosture'
import { PageHeader, PageShell, StatCard } from '@/components/layout/PageChrome'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import type { PostureGap } from '@/types'

const severityVariant = {
  critical: 'destructive',
  high: 'warning',
  medium: 'default',
  low: 'secondary',
} as const

const scopeConfig: {
  key: PostureGap['scope']
  title: string
  description: string
  icon: typeof Server
  accent: 'amber' | 'teal' | 'rose' | 'sky' | 'neutral'
}[] = [
  { key: 'k8s', title: 'Kubernetes', description: 'Pods, probes, PriorityClass, mesh', icon: Server, accent: 'sky' },
  { key: 'aws', title: 'AWS', description: 'RDS, ALB, SQS, ElastiCache', icon: Cloud, accent: 'amber' },
  { key: 'app', title: 'Application', description: 'Retries, circuit breakers, feature flags', icon: GitBranch, accent: 'teal' },
  { key: 'deps', title: 'Dependencies', description: 'Postgres, Redis, Kafka, Stripe, Auth0', icon: Database, accent: 'rose' },
  { key: 'observability', title: 'Observability', description: 'Prometheus, Grafana, Tempo, PagerDuty', icon: AlertTriangle, accent: 'neutral' },
]

export function PosturePage() {
  const { posture, snapshot, refetchAll, isLoading, isRefetching } = usePostureScan()
  const gaps = posture.data?.gaps ?? []
  const summary = posture.data?.summary
  const snap = snapshot.data

  if (isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-24 rounded-lg" />
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
        <Skeleton className="mt-6 h-96 rounded-lg" />
      </PageShell>
    )
  }

  return (
    <PageShell>
      <PageHeader
        title="Resilience posture"
        description="Cross-scope gap scan across Kubernetes, AWS, application code, dependencies, and observability."
        action={
          <Button variant="outline" onClick={() => void refetchAll()} disabled={isRefetching}>
            {isRefetching ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Re-scan
          </Button>
        }
        badge={
          <>
            {posture.data?.live_data === false && (
              <Badge variant="warning" className="mr-2">
                seed data
              </Badge>
            )}
            {posture.data?.live_data && (
              <Badge variant="success" className="mr-2">
                live cluster
              </Badge>
            )}
            {posture.data?.scanned_at ? (
              <Badge variant="outline" className="font-mono text-[10px]">
                {new Date(posture.data.scanned_at).toLocaleString()}
              </Badge>
            ) : undefined}
          </>
        }
      />

      {snap && (
        <section className="surface-card mb-6 rounded-lg p-5">
          <h2 className="text-sm font-semibold">Infrastructure snapshot</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            {snap.applications.length} apps · {snap.dependencies.length} deps · {snap.observability.length}{' '}
            observability targets
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {snap.graph_edges.map((e, i) => (
              <Badge key={i} variant="outline" className="font-mono text-[10px]">
                {e.from} → {e.to}
                <span className="ml-1 text-muted-foreground">({e.type})</span>
              </Badge>
            ))}
          </div>
        </section>
      )}

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {scopeConfig.map(({ key, title, icon, accent }) => (
          <StatCard
            key={key}
            icon={icon}
            label={title}
            value={summary?.[key] ?? gaps.filter((g) => g.scope === key).length}
            hint="gaps"
            accent={accent}
          />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {scopeConfig.map(({ key, title, description }) => {
          const items = gaps.filter((g) => g.scope === key)
          return (
            <section key={key} className="surface-card rounded-lg">
              <div className="border-b border-border px-5 py-4">
                <h3 className="text-sm font-semibold">{title}</h3>
                <p className="text-xs text-muted-foreground">{description}</p>
              </div>
              <div className="divide-y divide-border">
                {items.length === 0 ? (
                  <p className="px-5 py-6 text-sm text-muted-foreground">No gaps detected</p>
                ) : (
                  items.map((gap) => (
                    <div key={gap.id} className="px-5 py-4">
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-medium">{gap.service}</p>
                        <Badge variant={severityVariant[gap.severity]}>{gap.severity}</Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">{gap.rule}</p>
                      <p className="mt-2 text-sm">{gap.message}</p>
                      <p className="mt-2 text-xs text-primary">{gap.remediation}</p>
                    </div>
                  ))
                )}
              </div>
            </section>
          )
        })}
      </div>

      <section className="surface-card mt-6 rounded-lg">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
          <div>
            <h3 className="text-sm font-semibold">Bootstrap actions</h3>
            <p className="text-xs text-muted-foreground">
              Agent can install Istio, create PriorityClass, open Terraform PRs — with approval
            </p>
          </div>
          <Badge variant="outline" className="text-[10px]">
            Phase 2 preview
          </Badge>
        </div>
        <div className="divide-y divide-border">
          {demoBootstrapActions.map((action) => (
            <div
              key={action.action}
              className="flex flex-wrap items-center justify-between gap-2 px-5 py-3"
            >
              <div>
                <p className="text-sm font-medium">{action.action}</p>
                <p className="text-xs text-muted-foreground">{action.detail}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">{action.scope}</Badge>
                <Badge
                  variant={
                    action.status === 'done'
                      ? 'success'
                      : action.status === 'requires_approval'
                        ? 'warning'
                        : 'default'
                  }
                >
                  {action.status.replace('_', ' ')}
                </Badge>
                <Button variant="outline" size="sm" disabled>
                  {action.status === 'done' ? 'Done' : 'Apply'}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <p className="mt-6 text-center text-xs text-muted-foreground">
        Full infrastructure rings:{' '}
        <Link to="/infrastructure" className="text-primary hover:underline">
          Infrastructure page
        </Link>
      </p>
    </PageShell>
  )
}
