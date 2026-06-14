import { useState } from 'react'
import { Link } from 'react-router-dom'
import { PageHeader, PageShell } from '@/components/layout/PageChrome'
import { useLoadTests } from '@/hooks/usePlatform'
import { LoadScenarioCard } from '@/components/load/LoadScenarioCard'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import type { LoadTestType } from '@/types'

export function LoadTestingPage() {
  const { data, isLoading } = useLoadTests()
  const [filter, setFilter] = useState<LoadTestType | 'all'>('all')
  const [scriptType, setScriptType] = useState<LoadTestType>('load')

  if (isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-96 rounded-lg" />
      </PageShell>
    )
  }

  const scenarios = (data?.scenarios ?? []) as Array<{
    id: string
    name: string
    type: LoadTestType
    vus: number
    duration: string
    target: string
    status: string
    hypothesis: string
  }>
  const filtered = filter === 'all' ? scenarios : scenarios.filter((s) => s.type === filter)

  return (
    <PageShell>
      <PageHeader
        title="Performance testing"
        description="k6 load, stress, performance, and soak profiles paired with chaos faults."
      />

      <Tabs defaultValue="types">
        <TabsList className="flex h-auto flex-wrap gap-1">
          <TabsTrigger value="types">Test types</TabsTrigger>
          <TabsTrigger value="scenarios">Scenario library</TabsTrigger>
          <TabsTrigger value="pairing">Chaos + load</TabsTrigger>
          <TabsTrigger value="scripts">k6 templates</TabsTrigger>
        </TabsList>

        <TabsContent value="types" className="grid gap-4 md:grid-cols-2">
          {(data?.types ?? []).map((info) => (
            <section key={info.type} className="surface-card rounded-lg p-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold">{info.title}</h2>
                <Badge variant="outline">{info.type}</Badge>
              </div>
              <p className="mt-1 text-xs font-medium text-primary">{info.question}</p>
              <p className="mt-2 text-xs text-muted-foreground">{info.description}</p>
            </section>
          ))}
        </TabsContent>

        <TabsContent value="scenarios" className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {(['all', 'load', 'stress', 'performance', 'soak'] as const).map((t) => (
              <Button key={t} variant={filter === t ? 'default' : 'outline'} size="sm" onClick={() => setFilter(t)}>
                {t}
              </Button>
            ))}
            <Button size="sm" className="ml-auto" asChild>
              <Link to="/new">Use in experiment</Link>
            </Button>
          </div>
          <div className="space-y-3">
            {filtered.map((scenario) => (
              <LoadScenarioCard key={scenario.id} scenario={scenario} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="pairing">
          <section className="surface-card rounded-lg">
            <div className="divide-y divide-border">
              {(data?.pairings ?? []).map((pair) => (
                <div key={String(pair.id)} className="px-5 py-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium">{String(pair.name)}</p>
                    <Badge variant="outline">{String(pair.load_type)}</Badge>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">{String(pair.hypothesis)}</p>
                  <p className="mt-2 text-xs text-red-team">{String(pair.fault)}</p>
                  <Button variant="outline" size="sm" className="mt-3" asChild>
                    <Link to="/new">Compose experiment</Link>
                  </Button>
                </div>
              ))}
            </div>
          </section>
        </TabsContent>

        <TabsContent value="scripts">
          <div className="mb-4 flex flex-wrap gap-2">
            {(['load', 'stress', 'performance', 'soak'] as LoadTestType[]).map((t) => (
              <Button key={t} variant={scriptType === t ? 'default' : 'outline'} size="sm" onClick={() => setScriptType(t)}>
                {t}
              </Button>
            ))}
          </div>
          <pre className="surface-card overflow-auto rounded-lg p-5 font-mono text-xs">
            {data?.templates?.[scriptType] ?? ''}
          </pre>
        </TabsContent>
      </Tabs>
    </PageShell>
  )
}
