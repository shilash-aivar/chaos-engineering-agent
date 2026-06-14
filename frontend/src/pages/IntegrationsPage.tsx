import { PageHeader, PageShell } from '@/components/layout/PageChrome'
import { useIntegrations } from '@/hooks/usePlatform'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

export function IntegrationsPage() {
  const { data: integrations = [], isLoading } = useIntegrations()

  if (isLoading) {
    return (
      <PageShell>
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-lg" />
          ))}
        </div>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <PageHeader
        title="Integrations"
        description="Observability, GitHub, PagerDuty, and Slack connectivity — probed live from the API."
      />

      <div className="grid gap-4 md:grid-cols-2">
        {integrations.map((integration) => (
          <section key={integration.id} className="surface-card rounded-lg p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">{integration.name}</h2>
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
            <p className="mt-1 text-xs text-muted-foreground">{integration.detail}</p>
            <div className="mt-3 flex flex-wrap gap-1">
              {integration.events.map((e) => (
                <Badge key={e} variant="outline" className="text-[10px]">
                  {e}
                </Badge>
              ))}
            </div>
            <Button variant="outline" size="sm" className="mt-3" disabled={integration.status === 'planned'}>
              {integration.status === 'connected' ? 'Configure' : 'Connect'}
            </Button>
          </section>
        ))}
      </div>
    </PageShell>
  )
}
