import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listExperiments } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { formatRelativeTime } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { StateBadge } from '@/components/experiments/StateBadge'

export function ExperimentsPage() {
  const experiments = useAppStore((s) => s.experiments)
  const setExperiments = useAppStore((s) => s.setExperiments)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    void listExperiments()
      .then(setExperiments)
      .finally(() => setLoading(false))
  }, [setExperiments])

  if (loading) return <p className="text-sm text-muted-foreground">Loading experiments…</p>

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button asChild>
          <Link to="/new">New experiment</Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All experiments</CardTitle>
        </CardHeader>
        <CardContent className="divide-y divide-border p-0">
          {experiments.map((exp) => (
            <Link
              key={exp.id}
              to={`/experiments/${exp.id}`}
              className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 transition-colors hover:bg-accent"
            >
              <div className="min-w-0">
                <p className="font-medium">{exp.name}</p>
                <p className="text-sm text-muted-foreground">{exp.hypothesis}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {exp.namespace} · {formatRelativeTime(exp.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">{exp.source}</Badge>
                <StateBadge state={exp.state} />
                {exp.red_score != null && (
                  <Badge variant="red">R {exp.red_score}</Badge>
                )}
                {exp.blue_score != null && (
                  <Badge variant="blue">B {exp.blue_score}</Badge>
                )}
              </div>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
