import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { abortExperiment, getExperiment } from '@/api/client'
import type { ExperimentDetail } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { StateBadge } from '@/components/experiments/StateBadge'

export function ExperimentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [exp, setExp] = useState<ExperimentDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    const load = () => {
      void getExperiment(id)
        .then(setExp)
        .catch(() => navigate('/experiments'))
        .finally(() => setLoading(false))
    }
    load()
    const interval = setInterval(() => {
      if (!id) return
      void getExperiment(id).then(setExp).catch(() => undefined)
    }, 3000)
    return () => clearInterval(interval)
  }, [id, navigate])

  const handleAbort = async () => {
    if (!id) return
    await abortExperiment(id)
    const updated = await getExperiment(id)
    setExp(updated)
  }

  if (loading) return <p className="text-sm text-muted-foreground">Loading…</p>
  if (!exp) return null

  const canAbort = exp.state === 'running' || exp.state === 'awaiting_approval'

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">{exp.name}</h2>
          <p className="text-sm text-muted-foreground">{exp.hypothesis}</p>
        </div>
        <div className="flex items-center gap-2">
          <StateBadge state={exp.state} />
          {canAbort && (
            <Button variant="destructive" size="sm" onClick={handleAbort}>
              Abort & rollback
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Findings</p>
            <p className="text-2xl font-semibold">{exp.findings_count}</p>
          </CardContent>
        </Card>
        {exp.red_score != null && (
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-red-team">Red score</p>
              <p className="text-2xl font-semibold text-red-team">{exp.red_score}</p>
            </CardContent>
          </Card>
        )}
        {exp.blue_score != null && (
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-blue-team">Blue score</p>
              <p className="text-2xl font-semibold text-blue-team">{exp.blue_score}</p>
            </CardContent>
          </Card>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Timeline</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {exp.timeline.map((t, i) => (
            <div key={i} className="flex gap-3 text-sm">
              <span className="w-20 shrink-0 text-xs text-muted-foreground">
                {new Date(t.at).toLocaleTimeString()}
              </span>
              <div>
                <p className="font-medium">{t.event}</p>
                {t.detail && <p className="text-muted-foreground">{t.detail}</p>}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Plan</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">{exp.plan.source}</Badge>
            {exp.plan.faults.map((f, i) => (
              <Badge key={i} variant="secondary">
                {f.type}
              </Badge>
            ))}
          </div>
          <pre className="overflow-auto rounded-md border border-border bg-muted p-4 text-xs">
            {JSON.stringify(exp.plan, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}
