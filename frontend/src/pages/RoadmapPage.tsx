import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { roadmapPhases } from '@/demo/mockData'
import { PreviewBanner, PhaseBadge } from '@/components/shared/PreviewBanner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export function RoadmapPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PreviewBanner liveHint="Phase 1 orchestrator and compose are live today — everything else is the build plan." />

      <p className="text-sm text-muted-foreground">
        Core loop: infra snapshot → human/LLM scenarios → safe fault injection → LLM remediation →
        Red vs Blue scoring → verify. K8s + AWS + app + deps + observability (no GCP/Azure in v1).
      </p>

      <div className="space-y-4">
        {roadmapPhases.map((phase) => (
          <Card key={String(phase.phase)}>
            <CardHeader>
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle>
                  {phase.phase === 'future' ? 'Future' : `Phase ${phase.phase}`} — {phase.title}
                </CardTitle>
                <PhaseBadge phase={phase.phase === 'future' ? undefined : phase.phase} status={phase.status} />
              </div>
              <CardDescription>{phase.summary}</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {phase.features.map((f) => (
                  <li
                    key={f.name}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border px-3 py-2 text-sm"
                  >
                    <span>{f.name}</span>
                    <div className="flex items-center gap-2">
                      <PhaseBadge status={f.status} />
                      {f.path && (
                        <Button variant="ghost" size="sm" className="h-7 px-2" asChild>
                          <Link to={f.path}>
                            Open <ArrowRight className="h-3 w-3" />
                          </Link>
                        </Button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
