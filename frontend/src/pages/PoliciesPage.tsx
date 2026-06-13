import { demoPolicies } from '@/demo/mockData'
import { PreviewBanner, PhaseBadge } from '@/components/shared/PreviewBanner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function PoliciesPage() {
  return (
    <div className="space-y-6">
      <PreviewBanner
        phase={1}
        liveHint="Safety validator enforces these server-side today — UI editor comes later."
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Active safety policies</CardTitle>
          <p className="text-xs text-muted-foreground">
            Hard limits enforced by referee — not LLM. Prod requires explicit override + Slack approval.
          </p>
        </CardHeader>
        <CardContent className="space-y-2">
          {demoPolicies.map((policy) => (
            <div
              key={policy.id}
              className="flex flex-wrap items-start justify-between gap-3 rounded-md border border-border p-3"
            >
              <div>
                <p className="text-sm font-medium">{policy.name}</p>
                <p className="text-xs text-muted-foreground">{policy.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">{policy.value}</Badge>
                <Badge variant={policy.enforced ? 'success' : 'secondary'}>
                  {policy.enforced ? 'enforced' : 'optional'}
                </Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Approval workflow</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="rounded-md border border-border p-3">
              <p className="font-medium">Staging</p>
              <p className="text-xs text-muted-foreground">Auto-run after safety validation</p>
            </div>
            <div className="rounded-md border border-warning/30 bg-warning/10 p-3">
              <p className="font-medium">Production</p>
              <p className="text-xs text-muted-foreground">
                awaiting_approval → Slack #chaos-agent-approvals → human ack
              </p>
            </div>
            <div className="rounded-md border border-border p-3">
              <p className="font-medium">Cross-namespace</p>
              <p className="text-xs text-muted-foreground">Requires platform team approval</p>
            </div>
            <PhaseBadge status="preview" phase={2} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Executor allowlist</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {[
              { name: 'chaos_mesh', status: 'enabled', detail: 'pod_kill, network_latency, io_stress' },
              { name: 'toxiproxy', status: 'enabled', detail: 'dependency_blackhole, timeout, latency' },
              { name: 'k6', status: 'enabled', detail: 'load scenarios paired with faults' },
              { name: 'aws_fis', status: 'disabled', detail: 'AZ impairment, RDS failover — Phase 3' },
            ].map((ex) => (
              <div key={ex.name} className="flex justify-between rounded-md border border-border px-3 py-2 text-sm">
                <div>
                  <p className="font-medium">{ex.name}</p>
                  <p className="text-xs text-muted-foreground">{ex.detail}</p>
                </div>
                <Badge variant={ex.status === 'enabled' ? 'success' : 'secondary'}>{ex.status}</Badge>
              </div>
            ))}
            <Button variant="outline" size="sm" className="mt-2" disabled>
              Edit allowlist
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
