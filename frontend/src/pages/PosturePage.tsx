import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { demoBootstrapActions } from '@/demo/mockData'
import { getSnapshot, scanPosture } from '@/api/client'
import type { InfraSnapshot, PostureGap } from '@/types'
import { useAppStore } from '@/store/appStore'
import { PhaseBadge } from '@/components/shared/PreviewBanner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

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
}[] = [
  { key: 'k8s', title: 'Kubernetes', description: 'Pods, probes, PriorityClass, mesh' },
  { key: 'aws', title: 'AWS', description: 'RDS, ALB, SQS, ElastiCache' },
  { key: 'app', title: 'Application', description: 'Retries, circuit breakers, feature flags' },
  { key: 'deps', title: 'Dependencies', description: 'Postgres, Redis, Kafka, Stripe, Auth0' },
  { key: 'observability', title: 'Observability', description: 'Prometheus, Grafana, Tempo, PagerDuty, GitHub' },
]

export function PosturePage() {
  const setPostureGaps = useAppStore((s) => s.setPostureGaps)
  const [gaps, setGaps] = useState<PostureGap[]>([])
  const [summary, setSummary] = useState<Record<string, number>>({})
  const [snapshot, setSnapshot] = useState<InfraSnapshot | null>(null)
  const [scannedAt, setScannedAt] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = () => {
    setLoading(true)
    void Promise.all([scanPosture(), getSnapshot()])
      .then(([posture, snap]) => {
        setGaps(posture.gaps)
        setSummary(posture.summary ?? {})
        setPostureGaps(posture.gaps)
        setScannedAt(posture.scanned_at)
        setSnapshot(snap)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    refresh()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">
            {scannedAt ? `Last scan: ${new Date(scannedAt).toLocaleString()}` : 'Not scanned'}
          </p>
          {snapshot && (
            <p className="text-xs text-muted-foreground">
              Snapshot: {snapshot.applications.length} apps · {snapshot.dependencies.length} deps ·{' '}
              {snapshot.observability.length} observability targets
            </p>
          )}
        </div>
        <Button variant="outline" onClick={refresh} disabled={loading}>
          {loading ? 'Scanning…' : 'Re-scan'}
        </Button>
      </div>

      {snapshot && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Dependency graph</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {snapshot.graph_edges.map((e, i) => (
                <Badge key={i} variant="outline" className="font-mono text-[10px]">
                  {e.from} → {e.to}
                  <span className="ml-1 text-muted-foreground">({e.type})</span>
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {scopeConfig.map(({ key, title }) => (
          <Card key={key}>
            <CardContent className="p-4">
              <p className="text-[10px] uppercase text-muted-foreground">{title}</p>
              <p className="text-2xl font-bold">{summary[key] ?? gaps.filter((g) => g.scope === key).length}</p>
              <p className="text-[10px] text-muted-foreground">gaps</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {scopeConfig.map(({ key, title, description }) => {
          const items = gaps.filter((g) => g.scope === key)
          return (
            <Card key={key}>
              <CardHeader>
                <CardTitle>{title}</CardTitle>
                <p className="text-xs text-muted-foreground">{description}</p>
              </CardHeader>
              <CardContent className="space-y-3">
                {items.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No gaps detected</p>
                ) : (
                  items.map((gap) => (
                    <div key={gap.id} className="rounded-md border border-border p-4">
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
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm">Bootstrap actions</CardTitle>
            <p className="text-xs text-muted-foreground">
              Agent can install Istio, create PriorityClass, open Terraform PRs — with approval
            </p>
          </div>
          <PhaseBadge status="preview" phase={2} />
        </CardHeader>
        <CardContent className="space-y-2">
          {demoBootstrapActions.map((action) => (
            <div
              key={action.action}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border px-3 py-2"
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
        </CardContent>
      </Card>

      <p className="text-center text-xs text-muted-foreground">
        Full infrastructure rings:{' '}
        <Link to="/infrastructure" className="text-primary hover:underline">
          Infrastructure page
        </Link>
      </p>
    </div>
  )
}
