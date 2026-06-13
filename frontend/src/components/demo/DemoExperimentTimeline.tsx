import { AlertTriangle, CheckCircle2, Circle, Loader2 } from 'lucide-react'
import { demoTimeline } from '@/demo/mockData'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const statusIcon = {
  done: CheckCircle2,
  alert: AlertTriangle,
  active: Loader2,
  pending: Circle,
}

const statusColor = {
  done: 'text-success',
  alert: 'text-destructive',
  active: 'text-primary animate-spin',
  pending: 'text-muted-foreground',
}

export function DemoExperimentTimeline() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Experiment timeline</CardTitle>
        <p className="text-xs text-muted-foreground">Full lifecycle with audit trail</p>
      </CardHeader>
      <CardContent>
        <div className="relative space-y-0">
          {demoTimeline.map((step, i) => {
            const Icon = statusIcon[step.status as keyof typeof statusIcon] ?? Circle
            const isLast = i === demoTimeline.length - 1
            return (
              <div key={i} className="relative flex gap-3 pb-4">
                {!isLast && (
                  <div className="absolute left-[11px] top-6 h-full w-px bg-border" />
                )}
                <Icon
                  className={`relative z-10 h-6 w-6 shrink-0 rounded-full bg-card p-0.5 ${
                    statusColor[step.status as keyof typeof statusColor]
                  }`}
                />
                <div className="min-w-0 flex-1 pt-0.5">
                  <div className="flex items-baseline gap-2">
                    <span className="text-[10px] text-muted-foreground">{step.at}</span>
                    <span className="text-sm font-medium">{step.event}</span>
                  </div>
                  {step.detail && (
                    <p className="text-xs text-muted-foreground">{step.detail}</p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
