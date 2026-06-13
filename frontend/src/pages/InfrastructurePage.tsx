import { demoInfraRings } from '@/demo/mockData'
import { DemoTopologyGraph } from '@/components/demo/DemoTopologyGraph'
import { PreviewBanner, PhaseBadge } from '@/components/shared/PreviewBanner'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const ringLabels = {
  k8s: 'Kubernetes',
  aws: 'AWS',
  app: 'Application',
  deps: 'Dependencies',
  observability: 'Observability',
} as const

export function InfrastructurePage() {
  return (
    <div className="space-y-6">
      <PreviewBanner phase={2} liveHint="GET /snapshot returns seed data today — collectors will populate these rings." />

      <div className="grid gap-4 lg:grid-cols-2">
        <DemoTopologyGraph />
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Digital twin simulation</CardTitle>
            <p className="text-xs text-muted-foreground">
              Monte Carlo path analysis before any fault fires
            </p>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-md border border-border p-3">
                <p className="text-xs text-muted-foreground">Paths analyzed</p>
                <p className="text-xl font-bold">847</p>
              </div>
              <div className="rounded-md border border-border p-3">
                <p className="text-xs text-muted-foreground">Failure probability</p>
                <p className="text-xl font-bold text-red-team">12%</p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Predicted cascade: checkout → payments-api → payments-db. SQS backlog likely within 90s under load.
            </p>
            <PhaseBadge status="preview" phase={2} />
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="k8s">
        <TabsList className="flex h-auto flex-wrap gap-1">
          {(Object.keys(ringLabels) as (keyof typeof ringLabels)[]).map((key) => (
            <TabsTrigger key={key} value={key}>
              {ringLabels[key]}
            </TabsTrigger>
          ))}
        </TabsList>

        {(['k8s', 'aws', 'app', 'deps', 'observability'] as const).map((ring) => (
          <TabsContent key={ring} value={ring} className="space-y-3">
            <Card>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="p-3">Resource</th>
                      <th className="p-3">Details</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {demoInfraRings[ring].items.map((item) => (
                      <tr key={item.name} className="border-b border-border/50">
                        <td className="p-3 font-medium">{item.name}</td>
                        <td className="p-3 text-xs text-muted-foreground">{item.detail}</td>
                        <td className="p-3">
                          <Badge variant={item.status === 'ok' ? 'success' : 'warning'}>{item.status}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
