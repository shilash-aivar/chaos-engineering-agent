import { useState } from 'react'
import { PageHeader, PageShell } from '@/components/layout/PageChrome'
import { ConnectorConfigForm } from '@/components/integrations/ConnectorConfigForm'
import { useIntegrations, useTestIntegration } from '@/hooks/usePlatform'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

export function IntegrationsPage() {
  const { data: integrations = [], isLoading } = useIntegrations()
  const testMutation = useTestIntegration()
  const [lastResult, setLastResult] = useState<Record<string, string>>({})
  const [configuring, setConfiguring] = useState<string | null>(null)

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
        description="Connect Prometheus, Grafana, Loki, Tempo, GitHub, PagerDuty, Slack, and Anthropic from the console. Settings are saved to config/connectors.yaml and apply without restart."
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
            {lastResult[integration.id] && (
              <p className="mt-2 text-xs text-muted-foreground">{lastResult[integration.id]}</p>
            )}
            <div className="mt-3 flex flex-wrap gap-2">
              {integration.configurable !== false && (
                <Button
                  variant={configuring === integration.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() =>
                    setConfiguring((current) =>
                      current === integration.id ? null : integration.id,
                    )
                  }
                >
                  {configuring === integration.id ? 'Close' : 'Configure'}
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                disabled={integration.status === 'planned' || testMutation.isPending}
                onClick={async () => {
                  const result = await testMutation.mutateAsync(integration.id)
                  setLastResult((prev) => ({
                    ...prev,
                    [integration.id]: `${result.ok ? 'OK' : 'Failed'} (${result.latency_ms}ms): ${result.message}`,
                  }))
                }}
              >
                {integration.status === 'connected' ? 'Test connection' : 'Probe'}
              </Button>
            </div>
            {configuring === integration.id && (
              <ConnectorConfigForm integrationId={integration.id} />
            )}
          </section>
        ))}
      </div>
    </PageShell>
  )
}
