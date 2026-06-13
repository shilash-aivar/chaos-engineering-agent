import { demoMetrics } from '@/demo/mockData'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function DemoLiveMetrics() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Live metrics (experiment running)</CardTitle>
        <p className="text-xs text-muted-foreground">Steady-state guard · 15s evaluation</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {demoMetrics.map((m) => {
          const pct = Math.min(100, (m.current / (m.threshold * 2)) * 100)
          const breached = m.current > m.threshold
          return (
            <div key={m.label}>
              <div className="mb-1 flex justify-between text-xs">
                <span className="font-medium">{m.label}</span>
                <span className={breached ? 'text-destructive' : 'text-muted-foreground'}>
                  {m.current}
                  {m.unit} / threshold {m.threshold}
                  {m.unit}
                </span>
              </div>
              <div className="relative h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className={`h-full rounded-full transition-all ${breached ? 'bg-destructive' : 'bg-primary'}`}
                  style={{ width: `${pct}%` }}
                />
                <div
                  className="absolute top-0 h-full w-0.5 bg-warning/80"
                  style={{ left: `${(m.threshold / (m.threshold * 2)) * 100}%` }}
                />
              </div>
              <p className="mt-0.5 text-[10px] text-muted-foreground">baseline: {m.baseline}{m.unit}</p>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
