import { demoMetrics, demoObservabilityLinks } from '@/demo/mockData'
import { DemoLiveMetrics } from '@/components/demo/DemoLiveMetrics'
import { PreviewBanner, PhaseBadge } from '@/components/shared/PreviewBanner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function ObservabilityPage() {
  return (
    <div className="space-y-6">
      <PreviewBanner
        phase={1}
        liveHint="Prometheus guard runs server-side — this page will show live charts during experiments."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <DemoLiveMetrics />
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Steady-state guard</CardTitle>
            <p className="text-xs text-muted-foreground">
              Baseline capture → periodic check → auto-abort on breach
            </p>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="rounded-md border border-border p-3">
              <p className="text-xs text-muted-foreground">Abort thresholds</p>
              <p className="mt-1">Error rate &gt; 2× baseline</p>
              <p>Latency &gt; 3× baseline</p>
            </div>
            <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3">
              <p className="text-xs text-destructive">Last breach</p>
              <p className="font-medium">checkout error_rate 0.08% → 4.6%</p>
              <p className="text-xs text-muted-foreground">Rollback triggered at 14:04:02</p>
            </div>
            <PhaseBadge status="preview" phase={1} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Watch metrics</CardTitle>
          <p className="text-xs text-muted-foreground">Configured per experiment plan — polled during run</p>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2">
            {demoMetrics.map((m) => (
              <div key={m.label} className="rounded-md border border-border p-3">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">{m.label}</span>
                  <Badge variant={m.current > m.threshold ? 'destructive' : 'success'}>
                    {m.current}{m.unit}
                  </Badge>
                </div>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  baseline {m.baseline}{m.unit} · threshold {m.threshold}{m.unit}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Deep links</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {demoObservabilityLinks.map((link) => (
            <div key={link.label} className="flex items-center justify-between rounded-md border border-border px-3 py-2">
              <div>
                <p className="text-sm">{link.label}</p>
                <p className="font-mono text-[10px] text-muted-foreground">{link.url}</p>
              </div>
              <Button variant="ghost" size="sm" disabled>
                Open
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
