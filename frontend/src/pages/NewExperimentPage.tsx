import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Sparkles } from 'lucide-react'
import { composeScenario, createExperiment } from '@/api/client'
import type { ExperimentPlan } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'

const examples = [
  'Test checkout if inventory API has 500ms latency during peak load',
  'Pod kill on payments-api while DB connection pool is at 80%',
  'Replay cache miss storm on checkout service',
]

export function NewExperimentPage() {
  const navigate = useNavigate()
  const [scenario, setScenario] = useState('')
  const [plan, setPlan] = useState<ExperimentPlan | null>(null)
  const [summary, setSummary] = useState('')
  const [composing, setComposing] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const handleCompose = async () => {
    if (!scenario.trim()) return
    setComposing(true)
    try {
      const res = await composeScenario(scenario.trim())
      setPlan(res.plan)
      setSummary(res.summary)
    } finally {
      setComposing(false)
    }
  }

  const handleRun = async () => {
    if (!plan) return
    setSubmitting(true)
    try {
      const exp = await createExperiment(plan)
      navigate(`/experiments/${exp.id}`)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto grid max-w-5xl gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            Describe scenario
          </CardTitle>
          <CardDescription>
            Human intent + LLM grounding on K8s and AWS infrastructure
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="What failure do you want to test?"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
          />
          <div className="flex flex-wrap gap-2">
            {examples.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setScenario(ex)}
                className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-foreground"
              >
                {ex}
              </button>
            ))}
          </div>
          <Button onClick={handleCompose} disabled={composing || !scenario.trim()} className="w-full">
            {composing ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Generate plan
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Experiment plan</CardTitle>
          <CardDescription>Review before fault injection — safety validated</CardDescription>
        </CardHeader>
        <CardContent>
          {!plan ? (
            <p className="text-sm text-muted-foreground">
              Plan appears here after generation. Blast radius capped at 30% replicas, staging-only by default.
            </p>
          ) : (
            <div className="space-y-4">
              {summary && <p className="text-sm text-muted-foreground">{summary}</p>}
              <div>
                <p className="text-sm font-medium">{plan.name}</p>
                <p className="mt-1 text-sm text-muted-foreground">{plan.hypothesis}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">{plan.source}</Badge>
                <Badge variant="secondary">{plan.blast_radius.environment}</Badge>
                <Badge variant="warning">max {plan.blast_radius.max_replicas_pct}% replicas</Badge>
              </div>
              <div>
                <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Faults</p>
                <ul className="space-y-1 text-sm">
                  {plan.faults.map((f, i) => (
                    <li key={i} className="rounded border border-border px-2 py-1">
                      {f.executor} · {f.type} → {f.target}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Infra evidence</p>
                <ul className="space-y-1 text-xs text-muted-foreground">
                  {plan.infra_evidence.map((e, i) => (
                    <li key={i}>• {e}</li>
                  ))}
                </ul>
              </div>
              <Button onClick={handleRun} disabled={submitting} className="w-full">
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Approve & run in staging
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
