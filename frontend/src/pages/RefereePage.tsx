import { useState } from 'react'
import { PageHeader, PageShell } from '@/components/layout/PageChrome'
import { useFreezeCalendar, useRefereeScoring, useRegressionSuites } from '@/hooks/usePlatform'
import { validateRefereePlan } from '@/api/client'
import type { ExperimentPlan } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'

export function RefereePage() {
  const scoring = useRefereeScoring()
  const freeze = useFreezeCalendar()
  const regression = useRegressionSuites()
  const [planJson, setPlanJson] = useState('')
  const [validation, setValidation] = useState<{
    passed: boolean
    errors: string[]
    freeze_active: boolean
  } | null>(null)
  const [validating, setValidating] = useState(false)

  if (scoring.isLoading || freeze.isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-96 rounded-lg" />
      </PageShell>
    )
  }

  const handleValidate = async () => {
    setValidating(true)
    try {
      const plan = JSON.parse(planJson) as ExperimentPlan
      const result = await validateRefereePlan(plan)
      setValidation(result)
      if (result.passed) toast.success('Plan passes referee gate')
      else toast.error(result.errors.join('; '))
    } catch {
      toast.error('Invalid JSON plan')
    } finally {
      setValidating(false)
    }
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
        <h2 className="text-sm font-semibold">Validate experiment plan</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Paste an ExperimentPlan JSON to run the referee gate (blast radius, freeze calendar, production rules).
        </p>
        <Textarea
          className="mt-3 min-h-[200px] font-mono text-xs"
          placeholder='{"name": "...", "hypothesis": "...", ...}'
          value={planJson}
          onChange={(e) => setPlanJson(e.target.value)}
        />
        <Button className="mt-3" size="sm" disabled={validating || !planJson.trim()} onClick={() => void handleValidate()}>
          {validating ? 'Validating…' : 'Validate plan'}
        </Button>
        {validation && (
          <div className="mt-3 rounded border border-border p-3 text-sm">
            <Badge variant={validation.passed ? 'success' : 'destructive'}>
              {validation.passed ? 'passed' : 'rejected'}
            </Badge>
            {validation.freeze_active && (
              <p className="mt-2 text-xs text-warning">Freeze calendar is active</p>
            )}
            {validation.errors.length > 0 && (
              <ul className="mt-2 list-disc pl-4 text-xs text-muted-foreground">
                {validation.errors.map((err) => (
                  <li key={err}>{err}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>

      <section className="surface-card mt-6 rounded-lg">
        <div className="border-b border-border px-5 py-4">
          <h2 className="text-sm font-semibold">Regression suites</h2>
          <p className="text-xs text-muted-foreground">Exported from equilibrium Red/Blue rounds and passing experiments</p>
        </div>
        <div className="divide-y divide-border">
          {(regression.data ?? []).length === 0 ? (
            <p className="px-5 py-4 text-sm text-muted-foreground">No regression suites yet — equilibrium draws auto-export.</p>
          ) : (
            (regression.data ?? []).map((suite) => (
              <div key={suite.id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3">
                <div>
                  <p className="text-sm font-medium">{suite.name}</p>
                  <p className="text-xs text-muted-foreground">{suite.source} · {suite.tests} tests</p>
                </div>
                <Badge variant={suite.passing >= suite.tests ? 'success' : 'warning'}>
                  {suite.passing}/{suite.tests} passing
                </Badge>
              </div>
            ))
          )}
        </div>
      </section>

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
