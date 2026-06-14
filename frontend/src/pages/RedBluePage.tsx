import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, Play, Shield, Swords } from 'lucide-react'
import { toast } from 'sonner'
import { Scoreboard } from '@/components/red-blue/Scoreboard'
import { PageHeader, PageShell, EmptyState } from '@/components/layout/PageChrome'
import { SecurityDisclaimer } from '@/components/shared/SecurityDisclaimer'
import {
  useAttackFrameworks,
  useCampaign,
  useCampaigns,
  useGenerateAttackPlan,
  useRemediateRound,
  useRunCampaignRound,
  useStartCampaign,
  useVerifyRound,
} from '@/hooks/useRedBlue'
import { useAppStore } from '@/store/appStore'
import { formatRelativeTime } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import type { GeneratedAttackPlan } from '@/types'

const categoryVariant = {
  resilience: 'secondary',
  security: 'destructive',
  hybrid: 'warning',
} as const

export function RedBluePage() {
  const context = useAppStore((s) => s.context)
  const { data: campaigns = [], isLoading } = useCampaigns()
  const { data: frameworks = [] } = useAttackFrameworks()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { data: detail } = useCampaign(selectedId)

  const [name, setName] = useState('staging-game-day')
  const [includeSecurity, setIncludeSecurity] = useState(false)
  const [securityMix] = useState(50)
  const [selectedFramework, setSelectedFramework] = useState('owasp-top10-2021')
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [attackPlan, setAttackPlan] = useState<GeneratedAttackPlan | null>(null)
  const [showSetup, setShowSetup] = useState(false)

  const startMutation = useStartCampaign()
  const roundMutation = useRunCampaignRound()
  const generateMutation = useGenerateAttackPlan()
  const remediateMutation = useRemediateRound()
  const verifyMutation = useVerifyRound()

  useEffect(() => {
    if (!selectedId && campaigns.length > 0) setSelectedId(campaigns[0].id)
  }, [campaigns, selectedId])

  useEffect(() => {
    setSelectedCategories([])
    setAttackPlan(null)
  }, [selectedFramework])

  const activeFramework = frameworks.find((f) => f.id === selectedFramework)
  const active = detail ?? campaigns.find((c) => c.id === selectedId) ?? null
  const lastRound = detail?.rounds[detail.rounds.length - 1]

  const handleGeneratePlan = () => {
    generateMutation.mutate(
      {
        framework_id: selectedFramework,
        namespace: context.namespace,
        category_ids: selectedCategories.length > 0 ? selectedCategories : undefined,
      },
      {
        onSuccess: (plan) => {
          setAttackPlan(plan)
          setIncludeSecurity(true)
          toast.success(`Generated ${plan.attacks.length} attacks`)
        },
        onError: () => toast.error('Failed to generate attack plan'),
      },
    )
  }

  const handleStart = () => {
    startMutation.mutate(
      {
        name,
        options: {
          namespace: context.namespace,
          include_security: includeSecurity || !!attackPlan || selectedFramework !== 'resilience-chaos',
          security_mix_pct: securityMix,
          attack_framework_id: attackPlan
            ? undefined
            : selectedFramework !== 'resilience-chaos'
              ? selectedFramework
              : undefined,
          attack_category_ids: selectedCategories.length > 0 ? selectedCategories : undefined,
          attack_plan_id: attackPlan?.plan_id,
        },
      },
      {
        onSuccess: (c) => {
          setSelectedId(c.id)
          setShowSetup(false)
          toast.success('Campaign started')
        },
        onError: () => toast.error('Failed to start campaign'),
      },
    )
  }

  const handleRunRound = () => {
    if (!selectedId) return
    roundMutation.mutate(selectedId, {
      onSuccess: () => toast.success('Round complete'),
      onError: () => toast.error('Round failed'),
    })
  }

  if (isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-32 rounded-lg" />
        <Skeleton className="mt-4 h-96 rounded-lg" />
      </PageShell>
    )
  }

  return (
    <PageShell>
      <SecurityDisclaimer compact />

      <PageHeader
        title="Red vs Blue"
        description="Adversarial resilience campaigns — Red breaks, Blue defends, Referee scores each round."
        action={
          <Button variant="outline" onClick={() => setShowSetup((s) => !s)}>
            {showSetup ? 'Hide setup' : 'New campaign'}
          </Button>
        }
      />

      {showSetup && (
        <section className="surface-card mb-6 space-y-4 rounded-lg p-5">
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-[200px] flex-1">
              <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Campaign name
              </label>
              <Input value={name} onChange={(e) => setName(e.target.value)} className="mt-1" />
            </div>
            <Button variant="red" onClick={handleStart} disabled={startMutation.isPending}>
              {startMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Swords className="h-4 w-4" />}
              Start campaign
            </Button>
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={includeSecurity}
              onChange={(e) => setIncludeSecurity(e.target.checked)}
              className="rounded border-border"
            />
            Include security probes (OWASP / MITRE / CWE)
          </label>

          <div className="flex flex-wrap gap-2">
            {frameworks.map((fw) => (
              <Button
                key={fw.id}
                variant={selectedFramework === fw.id ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedFramework(fw.id)}
              >
                {fw.name}
              </Button>
            ))}
          </div>

          {activeFramework && (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {activeFramework.categories.slice(0, 6).map((cat) => {
                const selected = selectedCategories.includes(cat.id)
                return (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() =>
                      setSelectedCategories((prev) =>
                        prev.includes(cat.id) ? prev.filter((c) => c !== cat.id) : [...prev, cat.id],
                      )
                    }
                    className={`rounded-md border p-3 text-left text-xs transition-colors ${
                      selected ? 'border-primary bg-primary/10' : 'border-border hover:bg-accent/50'
                    }`}
                  >
                    <p className="font-medium">{cat.id}</p>
                    <p className="mt-0.5 line-clamp-1 text-muted-foreground">{cat.name}</p>
                  </button>
                )
              })}
            </div>
          )}

          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleGeneratePlan} disabled={generateMutation.isPending}>
              {generateMutation.isPending ? 'Generating…' : 'Generate attack plan'}
            </Button>
            {attackPlan && (
              <Badge variant="outline">{attackPlan.attacks.length} probes ready</Badge>
            )}
          </div>
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-12">
        <aside className="surface-card rounded-lg lg:col-span-4">
          <div className="border-b border-border px-4 py-3">
            <h2 className="text-sm font-semibold">Campaigns</h2>
          </div>
          {campaigns.length === 0 ? (
            <div className="p-4">
              <EmptyState
                icon={Swords}
                title="No campaigns"
                description="Start a Red vs Blue game day to score detection and recovery."
                action={
                  <Button size="sm" onClick={() => setShowSetup(true)}>
                    New campaign
                  </Button>
                }
              />
            </div>
          ) : (
            <div className="divide-y divide-border">
              {campaigns.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setSelectedId(c.id)}
                  className={`w-full px-4 py-3 text-left transition-colors hover:bg-accent/40 ${
                    selectedId === c.id ? 'bg-primary/5 ring-1 ring-inset ring-primary/20' : ''
                  }`}
                >
                  <p className="text-sm font-medium">{c.name}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    R {c.red_score} · B {c.blue_score} · {formatRelativeTime(c.last_round_at)}
                  </p>
                  <div className="mt-1 flex gap-1">
                    <Badge variant={c.state === 'active' ? 'warning' : 'success'} className="text-[10px]">
                      {c.state}
                    </Badge>
                    {c.include_security && (
                      <Badge variant="outline" className="text-[10px]">
                        security
                      </Badge>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </aside>

        <main className="lg:col-span-8">
          {!active ? (
            <EmptyState
              icon={Shield}
              title="Select a campaign"
              description="Pick a campaign from the list or create a new game day."
            />
          ) : (
            <div className="space-y-6">
              <section className="surface-card rounded-lg p-5">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-lg font-bold">{active.name}</h2>
                  {active.state === 'active' && active.round < active.max_rounds && (
                    <Button variant="red" size="sm" onClick={handleRunRound} disabled={roundMutation.isPending}>
                      {roundMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                      Run round {active.round + 1}
                    </Button>
                  )}
                </div>
                <Scoreboard
                  redScore={active.red_score}
                  blueScore={active.blue_score}
                  leader={active.leader}
                  round={active.round}
                  maxRounds={active.max_rounds}
                />
              </section>

              {detail && detail.rounds.length > 0 && (
                <section className="surface-card rounded-lg">
                  <div className="border-b border-border px-5 py-4">
                    <h3 className="text-sm font-semibold">Round history</h3>
                  </div>
                  <div className="divide-y divide-border">
                    {detail.rounds.map((r) => (
                      <div key={r.round} className="px-5 py-4 text-sm">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-medium">
                            Round {r.round}
                            <Badge variant={categoryVariant[r.attack.category]} className="ml-2 text-[10px]">
                              {r.attack.category}
                            </Badge>
                          </span>
                          <span className="text-xs">
                            <span className="text-red-team">+{r.red_points}</span>
                            {' / '}
                            <span className="text-blue-team">+{r.blue_points}</span>
                          </span>
                        </div>
                        <p className="mt-2 text-xs text-red-team/90">{r.attack.title}</p>
                        <p className="text-xs text-blue-team/90">{r.defense.title}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{r.referee_note}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {lastRound && selectedId && (
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="blue"
                    size="sm"
                    disabled={remediateMutation.isPending}
                    onClick={() =>
                      remediateMutation.mutate(
                        { campaignId: selectedId, round: lastRound.round },
                        {
                          onSuccess: (r) =>
                            toast.success(r.dry_run ? 'PR draft (dry-run)' : 'GitHub PR opened'),
                          onError: () => toast.error('Remediation failed'),
                        },
                      )
                    }
                  >
                    Blue: open PR
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={verifyMutation.isPending}
                    onClick={() =>
                      verifyMutation.mutate(
                        { campaignId: selectedId, round: lastRound.round },
                        {
                          onSuccess: (r) =>
                            toast.info(r.verified ? 'Probe verified' : r.message),
                        },
                      )
                    }
                  >
                    Verify probe
                  </Button>
                </div>
              )}

              {lastRound && (
                <div className="grid gap-4 lg:grid-cols-2">
                  <section className="rounded-lg border border-red-team/20 bg-red-team/5 p-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-red-team">Red transcript</h4>
                    <div className="mt-3 space-y-2">
                      {lastRound.red_transcript.map((t, i) => (
                        <p key={i} className="text-xs leading-relaxed text-foreground/90">
                          {t}
                        </p>
                      ))}
                    </div>
                  </section>
                  <section className="rounded-lg border border-blue-team/20 bg-blue-team/5 p-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-blue-team">Blue transcript</h4>
                    <div className="mt-3 space-y-2">
                      {lastRound.blue_transcript.map((t, i) => (
                        <p key={i} className="text-xs leading-relaxed text-foreground/90">
                          {t}
                        </p>
                      ))}
                    </div>
                  </section>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      <p className="mt-6 text-center text-xs text-muted-foreground">
        Equilibrium rounds feed the{' '}
        <Link to="/ci-gate" className="text-primary hover:underline">
          CI gate
        </Link>{' '}
        · Context gaps from{' '}
        <Link to="/context" className="text-primary hover:underline">
          ingestion
        </Link>
      </p>
    </PageShell>
  )
}
