import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Play, ShieldCheck, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { composeFullScenario } from '@/api/client'
import { useCreateExperiment } from '@/hooks/useExperiments'
import { PageHeader, PageShell } from '@/components/layout/PageChrome'
import type { ExperimentPlan } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'

const examples = [
  'Pod kill on payments-api during checkout peak — verify circuit breaker',
  '500ms latency on inventory-api — measure checkout p99 and error budget',
  'DB connection blackhole on payments-db — confirm rollback under 3 minutes',
]

export function NewExperimentPage() {
  const navigate = useNavigate()
  const createMutation = useCreateExperiment()
  const [scenario, setScenario] = useState('')
  const [plan, setPlan] = useState<ExperimentPlan | null>(null)
  const [summary, setSummary] = useState('')
  const [preMortem, setPreMortem] = useState<Record<string, unknown> | null>(null)
  const [referee, setReferee] = useState<{ passed: boolean; errors: string[] } | null>(null)
  const [composerMode, setComposerMode] = useState<'llm' | 'rules' | null>(null)
  const [composing, setComposing] = useState(false)

  const handleCompose = async () => {
    if (!scenario.trim()) return
    setComposing(true)
    try {
      const res = await composeFullScenario(scenario.trim())
      setPlan(res.plan)
      setSummary(res.summary)
      setPreMortem(res.pre_mortem)
      setReferee(res.referee)
      setComposerMode(res.composer ?? (res.plan.source === 'llm' ? 'llm' : 'rules'))
    } catch {
      toast.error('Could not generate plan — is the API running?')
    } finally {
      setComposing(false)
    }
  }

  const handleRun = () => {
    if (!plan) return
    createMutation.mutate(plan, {
      onSuccess: (exp) => {
        toast.success('Experiment queued')
        navigate(`/experiments/${exp.id}`)
      },
      onError: () => toast.error('Failed to start experiment'),
    })
  }

  return (
    <PageShell>
      <PageHeader
        title="Compose experiment"
        description="Describe the failure in plain language. The composer grounds the plan on your infra snapshot and safety policies."
      />

      <div className="grid gap-6 lg:grid-cols-5">
        <section className="surface-card rounded-lg lg:col-span-2">
          <div className="border-b border-border px-5 py-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold">Scenario</h2>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              What should break, and what should stay within SLO?
            </p>
          </div>
          <div className="space-y-4 p-5">
            <Textarea
              placeholder="e.g. Kill 30% of checkout pods while inventory latency is elevated…"
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="min-h-[140px] resize-none bg-input/50 font-sans text-sm"
            />
            <div className="flex flex-col gap-2">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Templates
              </p>
              {examples.map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => setScenario(ex)}
                  className="rounded-md border border-border bg-card/40 px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground"
                >
                  {ex}
                </button>
              ))}
            </div>
            <Button
              onClick={handleCompose}
              disabled={composing || !scenario.trim()}
              className="w-full"
            >
              {composing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Generate plan
            </Button>
          </div>
        </section>

        <section className="surface-card rounded-lg lg:col-span-3">
          <div className="border-b border-border px-5 py-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-success" />
              <h2 className="text-sm font-semibold">Review & approve</h2>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Blast radius capped · staging default · auto-rollback on breach
            </p>
          </div>
          <div className="p-5">
            {!plan ? (
              <div className="flex min-h-[280px] flex-col items-center justify-center text-center">
                <p className="text-sm text-muted-foreground">
                  Plan preview appears after generation.
                </p>
                <p className="mt-1 max-w-sm text-xs text-muted-foreground/80">
                  Includes faults, watch metrics, infra evidence, and rollback spec.
                </p>
              </div>
            ) : (
              <div className="space-y-5">
                {summary && (
                  <p className="rounded-md border border-border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
                    {summary}
                  </p>
                )}
                {preMortem && (
                  <div className="rounded-md border border-border bg-muted/20 px-3 py-2 text-xs text-muted-foreground">
                    <p className="font-semibold text-foreground">Pre-mortem</p>
                    <p className="mt-1">
                      {typeof preMortem.summary === 'string'
                        ? preMortem.summary
                        : 'Twin + risk analysis complete'}
                    </p>
                  </div>
                )}
                {referee && (
                  <Badge variant={referee.passed ? 'default' : 'destructive'}>
                    Referee: {referee.passed ? 'passed' : referee.errors.join('; ')}
                  </Badge>
                )}
                <div>
                  <p className="text-base font-semibold">{plan.name}</p>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{plan.hypothesis}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{plan.source}</Badge>
                  {composerMode && (
                    <Badge variant={composerMode === 'llm' ? 'default' : 'secondary'}>
                      Composer: {composerMode}
                    </Badge>
                  )}
                  <Badge variant="secondary">{plan.blast_radius.environment}</Badge>
                  <Badge variant="warning">≤ {plan.blast_radius.max_replicas_pct}% replicas</Badge>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Faults
                    </p>
                    <ul className="space-y-1.5">
                      {plan.faults.map((f, i) => (
                        <li
                          key={i}
                          className="rounded-md border border-border bg-card/50 px-3 py-2 font-mono text-xs"
                        >
                          {f.executor}/{f.type} → {f.target}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Watch metrics
                    </p>
                    <ul className="space-y-1.5">
                      {plan.watch_metrics.map((m) => (
                        <li
                          key={m}
                          className="rounded-md border border-border bg-card/50 px-3 py-2 font-mono text-xs text-muted-foreground"
                        >
                          {m}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
                <Button
                  onClick={handleRun}
                  disabled={createMutation.isPending}
                  className="w-full"
                  size="lg"
                >
                  {createMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  Approve & run in staging
                </Button>
              </div>
            )}
          </div>
        </section>
      </div>
    </PageShell>
  )
}
