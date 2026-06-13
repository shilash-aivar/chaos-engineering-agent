import { demoTopology } from '@/demo/mockData'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const tierColors: Record<string, string> = {
  critical: 'border-red-team/50 bg-red-team/15 text-red-team',
  standard: 'border-border bg-muted text-foreground',
  infra: 'border-primary/40 bg-primary/10 text-primary',
  deps: 'border-warning/40 bg-warning/10 text-warning',
}

export function DemoTopologyGraph() {
  const { nodes, edges, blastPath } = demoTopology
  const isBlast = (id: string) => blastPath.includes(id)

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Blast radius preview</CardTitle>
        <p className="text-xs text-muted-foreground">
          Predicted cascade before fault fires — twin simulation output
        </p>
      </CardHeader>
      <CardContent>
        <div className="relative mx-auto h-64 max-w-md rounded-lg border border-border bg-background/50">
          <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 90">
            {edges.map((e) => {
              const from = nodes.find((n) => n.id === e.from)!
              const to = nodes.find((n) => n.id === e.to)!
              const hot = isBlast(e.from) && isBlast(e.to)
              return (
                <line
                  key={`${e.from}-${e.to}`}
                  x1={from.x}
                  y1={from.y + 4}
                  x2={to.x}
                  y2={to.y - 4}
                  stroke={hot ? '#f43f5e' : '#334155'}
                  strokeWidth={hot ? 1.2 : 0.6}
                  strokeDasharray={hot ? undefined : '2 2'}
                />
              )
            })}
          </svg>
          {nodes.map((node) => (
            <div
              key={node.id}
              className="absolute -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${node.x}%`, top: `${node.y}%` }}
            >
              <div
                className={`rounded-md border px-2 py-1 text-center text-[10px] font-medium shadow-sm ${
                  isBlast(node.id) ? 'border-red-team bg-red-team/25 text-red-team ring-2 ring-red-team/30' : tierColors[node.tier]
                }`}
              >
                {node.label}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Badge variant="red">Predicted blast path</Badge>
          <Badge variant="outline">checkout → payments → RDS</Badge>
        </div>
      </CardContent>
    </Card>
  )
}
