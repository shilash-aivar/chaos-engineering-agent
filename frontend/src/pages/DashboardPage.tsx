import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  FlaskConical,
  Map,
  Presentation,
  ShieldAlert,
  Swords,
  TrendingUp,
} from 'lucide-react'
import { productFeatures } from '@/demo/mockData'
import { getDashboardStats, listCampaigns, listExperiments, scanPosture } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { formatRelativeTime } from '@/lib/utils'
import { PhaseBadge } from '@/components/shared/PreviewBanner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { StateBadge } from '@/components/experiments/StateBadge'

export function DashboardPage() {
  const { stats, setStats, setExperiments, setPostureGaps, setCampaigns } = useAppStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    void Promise.all([getDashboardStats(), listExperiments(), scanPosture(), listCampaigns()])
      .then(([s, exps, posture, campaigns]) => {
        setStats(s)
        setExperiments(exps)
        setPostureGaps(posture.gaps)
        setCampaigns(campaigns)
      })
      .finally(() => setLoading(false))
  }, [setStats, setExperiments, setPostureGaps, setCampaigns])

  const recent = useAppStore((s) => s.experiments.slice(0, 4))
  const topGaps = useAppStore((s) => s.postureGaps.slice(0, 3))
  const activeCampaign = useAppStore((s) => s.campaigns.find((c) => c.state === 'active'))

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading dashboard…</p>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3">
        <Link
          to="/demo"
          className="flex flex-1 min-w-[200px] items-center justify-between rounded-lg border border-primary/25 bg-primary/5 px-4 py-3 transition-colors hover:bg-primary/10"
        >
          <div className="flex items-center gap-2">
            <Presentation className="h-4 w-4 text-primary" />
            <span className="text-sm">
              <span className="font-medium text-primary">UI walkthrough</span>
              <span className="text-muted-foreground"> — end-to-end flow preview</span>
            </span>
          </div>
          <ArrowRight className="h-4 w-4 text-primary" />
        </Link>
        <Link
          to="/roadmap"
          className="flex flex-1 min-w-[200px] items-center justify-between rounded-lg border border-border px-4 py-3 transition-colors hover:bg-accent"
        >
          <div className="flex items-center gap-2">
            <Map className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Product roadmap — all phases</span>
          </div>
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: 'Experiments', value: stats?.experiments_total ?? 0, icon: FlaskConical },
          { label: 'Running', value: stats?.experiments_running ?? 0, icon: TrendingUp },
          { label: 'Resilience score', value: stats?.avg_resilience_score ?? 0, icon: ShieldAlert },
          { label: 'Posture gaps', value: stats?.posture_gaps ?? 0, icon: Swords },
        ].map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="mt-1 text-2xl font-semibold">{value}</p>
              </div>
              <Icon className="h-5 w-5 text-muted-foreground" />
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle>Recent experiments</CardTitle>
              <CardDescription>
                {stats?.last_experiment_at
                  ? `Last run ${formatRelativeTime(stats.last_experiment_at)}`
                  : 'No runs yet'}
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link to="/experiments">View all</Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {recent.map((exp) => (
              <Link
                key={exp.id}
                to={`/experiments/${exp.id}`}
                className="flex items-center justify-between rounded-md border border-border p-3 transition-colors hover:bg-accent"
              >
                <div>
                  <p className="text-sm font-medium">{exp.name}</p>
                  <p className="text-xs text-muted-foreground">{exp.namespace}</p>
                </div>
                <StateBadge state={exp.state} />
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Red vs Blue</CardTitle>
            <CardDescription>Adversarial resilience campaigns in staging</CardDescription>
          </CardHeader>
          <CardContent>
            {activeCampaign ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="font-medium">{activeCampaign.name}</p>
                  <Badge variant="warning">
                    Round {activeCampaign.round}/{activeCampaign.max_rounds}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-md border border-red-team/30 bg-red-team/10 p-3 text-center">
                    <p className="text-xs text-red-team">Red</p>
                    <p className="text-2xl font-bold text-red-team">{activeCampaign.red_score}</p>
                  </div>
                  <div className="rounded-md border border-blue-team/30 bg-blue-team/10 p-3 text-center">
                    <p className="text-xs text-blue-team">Blue</p>
                    <p className="text-2xl font-bold text-blue-team">{activeCampaign.blue_score}</p>
                  </div>
                </div>
                <Button variant="blue" className="w-full" asChild>
                  <Link to="/red-blue">
                    Open campaign <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              </div>
            ) : (
              <Button variant="red" asChild>
                <Link to="/red-blue">Start campaign</Link>
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Top posture gaps</CardTitle>
            <CardDescription>K8s + AWS rules failing in current context</CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link to="/posture">Full scan</Link>
          </Button>
        </CardHeader>
        <CardContent className="space-y-2">
          {topGaps.map((gap) => (
            <div key={gap.id} className="flex items-start justify-between gap-4 rounded-md border border-border p-3">
              <div>
                <p className="text-sm font-medium">{gap.service}</p>
                <p className="text-xs text-muted-foreground">{gap.message}</p>
              </div>
              <Badge variant={gap.severity === 'critical' ? 'destructive' : 'warning'}>
                {gap.scope}
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Platform features</CardTitle>
            <CardDescription>Live today vs UI previews — backend wiring comes over time</CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link to="/roadmap">Full roadmap</Link>
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {productFeatures.map((f) => (
              <Link
                key={f.id}
                to={f.path}
                className="flex items-start justify-between gap-2 rounded-md border border-border p-3 transition-colors hover:bg-accent"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium">{f.name}</p>
                  <p className="text-xs text-muted-foreground line-clamp-2">{f.description}</p>
                </div>
                <PhaseBadge status={f.status} phase={f.phase} className="shrink-0" />
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
