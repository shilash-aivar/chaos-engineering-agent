import { demoIntegrations } from '@/demo/mockData'
import { PreviewBanner, PhaseBadge } from '@/components/shared/PreviewBanner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <PreviewBanner phase={2} liveHint="GitHub and PagerDuty stubs exist in backend — full OAuth and webhooks later." />

      <div className="grid gap-4 md:grid-cols-2">
        {demoIntegrations.map((integration) => (
          <Card key={integration.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">{integration.name}</CardTitle>
                <Badge
                  variant={
                    integration.status === 'connected'
                      ? 'success'
                      : integration.status === 'planned'
                        ? 'secondary'
                        : 'warning'
                  }
                >
                  {integration.status}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">{integration.detail}</p>
            </CardHeader>
            <CardContent>
              <p className="mb-2 text-[10px] uppercase tracking-wide text-muted-foreground">Events</p>
              <div className="flex flex-wrap gap-1">
                {integration.events.map((e) => (
                  <Badge key={e} variant="outline">
                    {e}
                  </Badge>
                ))}
              </div>
              <Button variant="outline" size="sm" className="mt-3" disabled>
                {integration.status === 'connected' ? 'Configure' : 'Connect'}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Slack approval flow (planned)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>Interactive message when experiment hits awaiting_approval:</p>
          <div className="rounded-md border border-border bg-muted p-3 font-mono text-xs">
            :warning: <strong>checkout-payments-db-blackhole</strong> requests prod inject<br />
            Blast: 30% replicas · namespace: production<br />
            [Approve] [Reject] [View plan]
          </div>
          <PhaseBadge status="planned" phase={2} />
        </CardContent>
      </Card>
    </div>
  )
}
