import { demoScoreHistory } from '@/demo/mockData'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function DemoResilienceTrend() {
  const max = Math.max(...demoScoreHistory.map((d) => d.score))

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Resilience score trend</CardTitle>
        <p className="text-xs text-muted-foreground">90-day scorecard per service</p>
      </CardHeader>
      <CardContent>
        <div className="flex h-32 items-end justify-between gap-2">
          {demoScoreHistory.map((d) => (
            <div key={d.week} className="flex flex-1 flex-col items-center gap-1">
              <span className="text-[10px] font-medium text-primary">{d.score}</span>
              <div
                className="w-full rounded-t bg-primary/70 transition-all hover:bg-primary"
                style={{ height: `${(d.score / max) * 100}%`, minHeight: 8 }}
              />
              <span className="text-[10px] text-muted-foreground">{d.week}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
