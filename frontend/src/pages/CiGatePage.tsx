import { demoPrComment, demoRegressionSuites } from '@/demo/mockData'
import { DemoCiGatePreview } from '@/components/demo/DemoCiGatePreview'
import { PreviewBanner, PhaseBadge } from '@/components/shared/PreviewBanner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function CiGatePage() {
  return (
    <div className="space-y-6">
      <PreviewBanner phase={3} liveHint="Red agent will run PR-scoped faults; GitHub bot posts resilience comment on each push." />

      <div className="grid gap-4 lg:grid-cols-2">
        <DemoCiGatePreview />
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">How CI gate works</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <ol className="list-decimal space-y-2 pl-4">
              <li>Diff analysis identifies blast-sensitive services in the PR</li>
              <li>Red agent composes 1–3 targeted faults on changed paths</li>
              <li>Experiments run in ephemeral staging namespace</li>
              <li>Referee compares against regression suite baseline</li>
              <li>GitHub status check + markdown comment on the PR</li>
            </ol>
            <PhaseBadge status="preview" phase={3} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm">Regression suites</CardTitle>
            <p className="text-xs text-muted-foreground">
              Equilibrium Red/Blue rounds and passed experiments become permanent suites
            </p>
          </div>
          <Button variant="outline" size="sm" disabled>
            Export suite
          </Button>
        </CardHeader>
        <CardContent className="space-y-2">
          {demoRegressionSuites.map((suite) => (
            <div
              key={suite.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border p-3"
            >
              <div>
                <p className="text-sm font-medium">{suite.name}</p>
                <p className="text-xs text-muted-foreground">
                  {suite.source.replace('_', ' ')} · last run {suite.last_run}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={suite.passing === suite.tests ? 'success' : 'warning'}>
                  {suite.passing}/{suite.tests} passing
                </Badge>
                <Button variant="ghost" size="sm" disabled>
                  Run in CI
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Raw PR comment preview</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="overflow-auto rounded-md border border-border bg-muted p-4 text-xs whitespace-pre-wrap">
            {demoPrComment}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}
