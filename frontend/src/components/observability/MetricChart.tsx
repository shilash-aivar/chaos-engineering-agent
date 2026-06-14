import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { MetricWindowSample } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type MetricChartProps = {
  metrics: MetricWindowSample[]
  title?: string
}

export function MetricChart({ metrics, title = 'Fault-window metrics' }: MetricChartProps) {
  const data = metrics.map((m) => ({
    name: m.name.replace(/_/g, ' '),
    baseline: m.baseline ?? 0,
    peak: m.during_peak ?? 0,
    after: m.after ?? 0,
    breached: (m.delta_ratio ?? 0) >= 2,
  }))

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No metric samples in this window.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{title}</CardTitle>
        <p className="text-xs text-muted-foreground">Baseline · peak during fault · after recovery</p>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 32 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10 }}
              interval={0}
              angle={-20}
              textAnchor="end"
              height={48}
            />
            <YAxis tick={{ fontSize: 10 }} width={48} />
            <Tooltip
              contentStyle={{
                background: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Bar dataKey="baseline" name="Baseline" fill="#8b95a8" radius={[4, 4, 0, 0]} />
            <Bar dataKey="peak" name="Peak" radius={[4, 4, 0, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={entry.breached ? '#ef4444' : '#e8952e'}
                />
              ))}
            </Bar>
            <Bar dataKey="after" name="After" fill="#34d399" radius={[4, 4, 0, 0]} />
            <ReferenceLine y={0} stroke="hsl(var(--border))" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
