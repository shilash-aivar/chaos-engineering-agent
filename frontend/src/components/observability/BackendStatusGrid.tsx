import type { ObservabilityBackendStatus } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

function BackendBadge({ status }: { status: string }) {
  return (
    <Badge variant={status === 'ok' ? 'success' : 'warning'}>
      {status === 'ok' ? 'connected' : 'gap'}
    </Badge>
  )
}

const BACKENDS = [
  { key: 'prometheus' as const, title: 'Prometheus', hint: 'Range queries + steady-state guard' },
  { key: 'loki' as const, title: 'Loki', hint: 'LogQL per service in fault window' },
  { key: 'tempo' as const, title: 'Tempo', hint: 'TraceQL search on blast paths' },
]

export function BackendStatusGrid({ status }: { status?: ObservabilityBackendStatus | null }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {BACKENDS.map((backend) => (
        <Card key={backend.key}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">{backend.title}</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">{backend.hint}</p>
            <BackendBadge status={status?.[backend.key] ?? 'gap'} />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
