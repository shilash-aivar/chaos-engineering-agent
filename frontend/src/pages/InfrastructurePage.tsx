import { PageHeader, PageShell, StatCard } from '@/components/layout/PageChrome'
import { TopologyGraph } from '@/components/infrastructure/TopologyGraph'
import { useInfrastructure, useTwinAnalysis } from '@/hooks/usePlatform'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Layers } from 'lucide-react'

const ringLabels = {
  k8s: 'Kubernetes',
  aws: 'AWS',
  app: 'Application',
  deps: 'Dependencies',
  observability: 'Observability',
} as const

export function InfrastructurePage() {
  const { data: infra, isLoading } = useInfrastructure()
  const { data: twin } = useTwinAnalysis()

  if (isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-24 rounded-lg" />
        <Skeleton className="mt-6 h-96 rounded-lg" />
      </PageShell>
    )
  }

  const rings = infra?.rings ?? {}
  const topology = twin?.topology

  return (
    <PageShell>
      <PageHeader
        title="Infrastructure"
        description="Five-ring snapshot from live collectors — K8s, AWS, application, dependencies, observability."
        badge={
          <Badge variant="outline" className="font-mono text-[10px]">
            {infra?.namespace ?? 'staging'}
          </Badge>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <StatCard
          icon={Layers}
          label="Paths analyzed"
          value={twin?.paths_analyzed ?? '—'}
          accent="amber"
        />
        <StatCard
          icon={Layers}
          label="Failure probability"
          value={twin ? `${twin.failure_probability_pct}%` : '—'}
          accent="rose"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {topology ? (
          <TopologyGraph
            nodes={topology.nodes}
            edges={topology.edges}
            blastPath={topology.blast_path}
          />
        ) : (
          <Skeleton className="h-80 rounded-lg" />
        )}
        <section className="surface-card rounded-lg p-5">
          <h2 className="text-sm font-semibold">Digital twin simulation</h2>
          <p className="mt-1 text-xs text-muted-foreground">Graph path analysis before fault fires</p>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            {twin?.predicted_cascade ?? 'Run a compose experiment to refresh twin analysis.'}
          </p>
        </section>
      </div>

      <Tabs defaultValue="k8s" className="mt-6">
        <TabsList className="flex h-auto flex-wrap gap-1">
          {(Object.keys(ringLabels) as (keyof typeof ringLabels)[]).map((key) => (
            <TabsTrigger key={key} value={key}>
              {ringLabels[key]}
            </TabsTrigger>
          ))}
        </TabsList>

        {(Object.keys(ringLabels) as (keyof typeof ringLabels)[]).map((ring) => (
          <TabsContent key={ring} value={ring}>
            <section className="surface-card overflow-hidden rounded-lg">
              <table className="data-table w-full">
                <thead>
                  <tr>
                    <th>Resource</th>
                    <th>Details</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(rings[ring] ?? []).map((item) => (
                    <tr key={item.name}>
                      <td className="font-medium">{item.name}</td>
                      <td className="text-xs text-muted-foreground">{item.detail}</td>
                      <td>
                        <Badge variant={item.status === 'ok' ? 'success' : 'warning'}>{item.status}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </TabsContent>
        ))}
      </Tabs>
    </PageShell>
  )
}
