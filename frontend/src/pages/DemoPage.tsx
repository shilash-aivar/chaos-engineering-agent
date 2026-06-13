import { Link } from 'react-router-dom'
import {
  FlaskConical,
  GitPullRequest,
  Layers,
  Shield,
  Swords,
  TrendingUp,
  Users,
  Zap,
} from 'lucide-react'
import { demoStats } from '@/demo/mockData'
import { DemoBanner } from '@/components/demo/DemoBanner'
import { DemoSection } from '@/components/demo/DemoSection'
import { DemoScenarioComposer } from '@/components/demo/DemoScenarioComposer'
import { DemoTopologyGraph } from '@/components/demo/DemoTopologyGraph'
import { DemoLiveMetrics } from '@/components/demo/DemoLiveMetrics'
import { DemoExperimentTimeline } from '@/components/demo/DemoExperimentTimeline'
import { DemoRedBlueArena } from '@/components/demo/DemoRedBlueArena'
import { DemoRemediationPanel } from '@/components/demo/DemoRemediationPanel'
import { DemoResilienceTrend } from '@/components/demo/DemoResilienceTrend'
import { DemoCiGatePreview } from '@/components/demo/DemoCiGatePreview'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function DemoPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-8 pb-12">
      <DemoBanner />

      {/* Vision stats */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: 'Experiments run', value: demoStats.experiments_total, icon: FlaskConical },
          { label: 'Resilience score', value: demoStats.avg_resilience_score, icon: TrendingUp },
          { label: 'Teams enabled', value: demoStats.teams_active, icon: Users },
          { label: 'Regression suites', value: demoStats.regressions_passing, icon: Shield },
        ].map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="flex items-center justify-between p-4">
              <div>
                <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
                <p className="text-2xl font-bold">{value}</p>
              </div>
              <Icon className="h-5 w-5 text-muted-foreground/60" />
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="flow" className="w-full">
        <TabsList className="flex h-auto flex-wrap gap-1 bg-muted p-1">
          <TabsTrigger value="flow" className="gap-1.5">
            <Zap className="h-3.5 w-3.5" />
            Full flow
          </TabsTrigger>
          <TabsTrigger value="experiment" className="gap-1.5">
            <FlaskConical className="h-3.5 w-3.5" />
            Live experiment
          </TabsTrigger>
          <TabsTrigger value="redblue" className="gap-1.5">
            <Swords className="h-3.5 w-3.5" />
            Red vs Blue
          </TabsTrigger>
          <TabsTrigger value="platform" className="gap-1.5">
            <Layers className="h-3.5 w-3.5" />
            Platform
          </TabsTrigger>
        </TabsList>

        {/* Tab: end-to-end flow */}
        <TabsContent value="flow" className="space-y-8">
          <DemoSection
            title="1 · Describe scenario"
            description="Human intent + LLM grounds the plan on K8s and AWS infrastructure"
          >
            <DemoScenarioComposer />
          </DemoSection>

          <DemoSection
            title="2 · Predict blast radius"
            description="Digital twin maps dependencies before any fault fires"
          >
            <div className="grid gap-4 lg:grid-cols-2">
              <DemoTopologyGraph />
              <DemoExperimentTimeline />
            </div>
          </DemoSection>

          <DemoSection
            title="3 · Remediate automatically"
            description="LLM diagnoses, prescribes, and opens tickets — verify with re-run"
          >
            <DemoRemediationPanel />
          </DemoSection>
        </TabsContent>

        {/* Tab: running experiment */}
        <TabsContent value="experiment" className="space-y-6">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="default">running</Badge>
            <span className="text-sm text-muted-foreground">checkout-payments-db-blackhole · staging</span>
            <Button variant="destructive" size="sm" disabled>
              Abort & rollback
            </Button>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <DemoLiveMetrics />
            <DemoExperimentTimeline />
          </div>
          <DemoTopologyGraph />
        </TabsContent>

        {/* Tab: Red vs Blue */}
        <TabsContent value="redblue" className="space-y-6">
          <p className="text-sm text-muted-foreground">
            Two agents compete in staging — Red maximizes break score, Blue maximizes defense score.
            Equilibrium rounds become regression suites.
          </p>
          <div className="grid gap-4 lg:grid-cols-2">
            <DemoRedBlueArena />
            <DemoResilienceTrend />
          </div>
        </TabsContent>

        {/* Tab: platform extras */}
        <TabsContent value="platform" className="space-y-6">
          <div className="grid gap-4 lg:grid-cols-2">
            <DemoCiGatePreview />
            <Card>
              <CardContent className="space-y-3 p-5">
                <div className="flex items-center gap-2">
                  <GitPullRequest className="h-4 w-4 text-primary" />
                  <p className="text-sm font-medium">Posture enforcement</p>
                </div>
                <ul className="space-y-2 text-xs text-muted-foreground">
                  <li className="flex justify-between rounded border border-border px-2 py-1.5">
                    <span>PriorityClass on critical pods</span>
                    <Badge variant="destructive">missing</Badge>
                  </li>
                  <li className="flex justify-between rounded border border-border px-2 py-1.5">
                    <span>RDS Multi-AZ (payments-db)</span>
                    <Badge variant="destructive">missing</Badge>
                  </li>
                  <li className="flex justify-between rounded border border-border px-2 py-1.5">
                    <span>SQS DLQ (order-events)</span>
                    <Badge variant="warning">missing</Badge>
                  </li>
                  <li className="flex justify-between rounded border border-border px-2 py-1.5">
                    <span>Istio retry on checkout→payments</span>
                    <Badge variant="warning">missing</Badge>
                  </li>
                </ul>
                <p className="text-[10px] text-muted-foreground">
                  Agent can create PriorityClass, open Terraform PRs, and bootstrap Istio (with approval).
                </p>
              </CardContent>
            </Card>
          </div>
          <DemoResilienceTrend />
        </TabsContent>
      </Tabs>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-card p-4">
        <p className="text-sm text-muted-foreground">
          Explore all features in the sidebar, or see the{' '}
          <Link to="/roadmap" className="text-primary hover:underline">
            product roadmap
          </Link>
          .
        </p>
        <Button asChild>
          <Link to="/new">Start experiment</Link>
        </Button>
      </div>
    </div>
  )
}
