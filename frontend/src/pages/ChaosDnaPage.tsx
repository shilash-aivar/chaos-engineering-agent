import { TrendingDown, TrendingUp, Minus } from 'lucide-react'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { PageHeader, PageShell, StatCard } from '@/components/layout/PageChrome'
import { useChaosDna } from '@/hooks/usePlatform'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dna } from 'lucide-react'

const trendIcon = {
  up: TrendingUp,
  down: TrendingDown,
  flat: Minus,
}

export function ChaosDnaPage() {
  const { data, isLoading } = useChaosDna()

  if (isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-96 rounded-lg" />
      </PageShell>
    )
  }

  return (
    <PageShell>
      <PageHeader
        title="Chaos DNA"
        description="Per-service resilience profiles aggregated from experiments and Red/Blue campaigns."
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-4">
        <StatCard icon={Dna} label="Org score" value={data?.org_score ?? 0} accent="amber" />
        <StatCard icon={Dna} label="Faults survived (avg)" value={data?.faults_survived_avg ?? 0} accent="teal" />
        <StatCard icon={Dna} label="MTTR" value={data?.mttr_seconds != null ? `${data.mttr_seconds}s` : '—'} accent="sky" />
        <StatCard icon={Dna} label="Regression suites" value={data?.regression_suites_passing ?? 0} accent="neutral" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="surface-card rounded-lg p-5">
          <h2 className="text-sm font-semibold">Score trend</h2>
          <div className="mt-4 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.history ?? []}>
                <XAxis dataKey="week" tick={{ fontSize: 10 }} />
                <YAxis domain={[50, 100]} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Line type="monotone" dataKey="score" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="surface-card rounded-lg p-5">
          <h2 className="text-sm font-semibold">Org resilience</h2>
          <p className="mt-2 text-4xl font-bold">{data?.org_score}</p>
          <p className="text-xs text-muted-foreground">{data?.org_delta}</p>
        </section>
      </div>

      <section className="surface-card mt-6 rounded-lg">
        <div className="border-b border-border px-5 py-4">
          <h2 className="text-sm font-semibold">Service profiles</h2>
        </div>
        <div className="divide-y divide-border">
          {data?.empty_state ? (
            <p className="px-5 py-6 text-sm text-muted-foreground">
              No experiments in this namespace yet. Run a chaos experiment or Red/Blue campaign to build profiles.
            </p>
          ) : (
            (data?.profiles ?? []).map((profile) => {
            const Icon = trendIcon[profile.trend]
            return (
              <div key={profile.service} className="px-5 py-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{profile.service}</span>
                    <Badge variant="outline">{profile.tier}</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold">{profile.resilience_score}</span>
                    <Icon
                      className={`h-4 w-4 ${profile.trend === 'up' ? 'text-success' : profile.trend === 'down' ? 'text-destructive' : 'text-muted-foreground'}`}
                    />
                  </div>
                </div>
                <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                  <div>
                    <p className="text-muted-foreground">Survived</p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {profile.faults_survived.map((f) => (
                        <Badge key={f} variant="success">
                          {f}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Weak points</p>
                    <p className="mt-1">{profile.weak_points.join(' · ')}</p>
                  </div>
                </div>
                <p className="mt-2 text-[10px] text-muted-foreground">Last tested {profile.last_tested}</p>
              </div>
            )
          })
          )}
        </div>
      </section>
    </PageShell>
  )
}
