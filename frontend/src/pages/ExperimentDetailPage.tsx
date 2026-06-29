import { useEffect, useRef } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { MessageSquare, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { TopologyGraph } from '@/components/infrastructure/TopologyGraph'
import { EvidencePanel } from '@/components/observability/EvidencePanel'
import { MetricChart } from '@/components/observability/MetricChart'
import {
  useAbortExperiment,
  useCaptureEvidence,
  useExperiment,
  useExperimentEvidence,
} from '@/hooks/useExperiments'
import { useExperimentWebSocket } from '@/hooks/useExperimentWebSocket'
import { useApproveExperiment, useExperimentRemediation, useRunRemediation } from '@/hooks/useRemediation'
import { useTwinAnalysis } from '@/hooks/usePlatform'
import { useAppStore } from '@/store/appStore'
import { PageShell } from '@/components/layout/PageChrome'
import { StatusDot } from '@/components/shared/StatusDot'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { MetricWindowSample } from '@/types'

const ACTIVE_STATES = new Set(['running', 'simulating', 'aborting'])
const SHOW_LIVE_PREVIEW = new Set(['running', 'simulating', 'complete', 'failed'])
const EVIDENCE_STATES = new Set(['complete', 'failed'])

export function ExperimentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const context = useAppStore((s) => s.context)
  const { data: exp, isLoading, isError } = useExperiment(id)
  const abortMutation = useAbortExperiment()
  const approveMutation = useApproveExperiment()
  const captureMutation = useCaptureEvidence()
  const autoCaptureAttempted = useRef(false)

  useExperimentWebSocket(id, Boolean(id))

  const evidenceReady = Boolean(id && exp && EVIDENCE_STATES.has(exp.state))
  const hasInlineEvidence = Boolean(exp?.evidence)
  const evidenceQuery = useExperimentEvidence(id, evidenceReady && !hasInlineEvidence)
  const remediationQuery = useExperimentRemediation(id, evidenceReady)
  const runRemediation = useRunRemediation()
  const faultTarget = exp?.plan?.faults?.[0]?.target ?? exp?.plan?.targets?.[0]?.service ?? 'checkout'
  const { data: twin } = useTwinAnalysis(faultTarget, Boolean(exp))

  useEffect(() => {
    if (!id || !evidenceReady || hasInlineEvidence || autoCaptureAttempted.current) return
    if (evidenceQuery.isError) {
      autoCaptureAttempted.current = true
      captureMutation.mutate(id)
    }
  }, [id, evidenceReady, hasInlineEvidence, evidenceQuery.isError, captureMutation])

  useEffect(() => {
    if (isError) navigate('/experiments')
  }, [isError, navigate])

  if (isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-28 rounded-lg" />
        <Skeleton className="mt-4 h-10 w-80" />
        <Skeleton className="mt-6 h-96 rounded-lg" />
      </PageShell>
    )
  }
  if (!exp || !id) return null

  const canAbort = exp.state === 'running' || exp.state === 'awaiting_approval'
  const isAwaitingApproval = exp.state === 'awaiting_approval'
  const showLivePreview = SHOW_LIVE_PREVIEW.has(exp.state)
  const showFindings = exp.findings_count > 0 || exp.state === 'complete'

  const resolvedEvidence =
    exp.evidence ?? evidenceQuery.data ?? captureMutation.data ?? null

  const liveMetrics: MetricWindowSample[] =
    resolvedEvidence?.metrics ??
    (exp.baseline
      ? Object.entries(exp.baseline).map(([name, baseline]) => ({
          name,
          baseline,
          during_peak: baseline,
          after: baseline,
          unit: name.includes('p99') ? 'seconds' : 'ratio',
        }))
      : [])

  const handleAbort = async () => {
    try {
      await abortMutation.mutateAsync(id)
      toast.success('Abort requested — rollback started')
    } catch {
      toast.error('Failed to request abort')
    }
  }

  const handleApprove = () => {
    if (!id) return
    approveMutation.mutate(id, {
      onSuccess: () => toast.success('Experiment approved — starting inject'),
      onError: () => toast.error('Approval failed — check referee gate'),
    })
  }

  const handleCapture = () => {
    captureMutation.mutate(id, {
      onSuccess: () => toast.success('Fault-window evidence captured'),
      onError: () => toast.error('Evidence capture failed — restart API and retry'),
    })
  }

  return (
    <PageShell>
      <section className="surface-card rounded-lg p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 space-y-2">
            <div className="flex flex-wrap items-center gap-3">
              <StatusDot state={exp.state} />
              <span className="font-mono text-[11px] text-muted-foreground">{exp.id}</span>
            </div>
            <h1 className="text-xl font-bold tracking-tight">{exp.name}</h1>
            <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">{exp.hypothesis}</p>
            <p className="text-xs text-muted-foreground">
              {context.cluster} · {exp.namespace} · {exp.environment}
            </p>
          </div>
          {canAbort && (
            <Button
              variant="destructive"
              size="sm"
              disabled={abortMutation.isPending}
              onClick={handleAbort}
            >
              Abort & rollback
            </Button>
          )}
          {EVIDENCE_STATES.has(exp.state) && (
            <Button variant="outline" size="sm" asChild>
              <Link to={`/new?prior=${id}`}>
                <Sparkles className="mr-2 h-4 w-4" />
                Iterate from results
              </Link>
            </Button>
          )}
        </div>
      </section>

      <Tabs defaultValue="overview" className="mt-6">
        <TabsList className="bg-muted/50">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="plan">Plan</TabsTrigger>
          <TabsTrigger value="metrics" disabled={!showLivePreview}>
            Metrics
          </TabsTrigger>
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
          <TabsTrigger value="findings" disabled={!showFindings}>
            Findings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {isAwaitingApproval && (
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-warning/30 bg-warning/5 px-4 py-3 text-sm text-warning">
              <span>
                <MessageSquare className="mr-2 inline h-4 w-4" />
                Awaiting human approval before inject
              </span>
              <Button size="sm" onClick={handleApprove} disabled={approveMutation.isPending}>
                Approve & run
              </Button>
            </div>
          )}

          {exp.baseline && ACTIVE_STATES.has(exp.state) && (
            <div className="surface-card flex items-center justify-between rounded-lg p-4">
              <div>
                <p className="text-xs text-muted-foreground">Baseline captured</p>
                <p className="font-mono text-sm">
                  {Object.entries(exp.baseline)
                    .map(([k, v]) => `${k}=${v.toFixed(4)}`)
                    .join(', ')}
                </p>
              </div>
              <Badge variant="success">steady-state armed</Badge>
            </div>
          )}

          <div className="surface-card rounded-lg">
            <div className="border-b border-border px-5 py-4">
              <h3 className="text-sm font-semibold">Run timeline</h3>
            </div>
            <div className="space-y-0 divide-y divide-border px-5">
              {exp.timeline.map((t, i) => (
                <div key={i} className="flex gap-4 py-3 text-sm">
                  <span className="w-16 shrink-0 font-mono text-[11px] text-muted-foreground">
                    {new Date(t.at).toLocaleTimeString()}
                  </span>
                  <div>
                    <p className="font-medium">{t.event}</p>
                    {t.detail && <p className="text-muted-foreground">{t.detail}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="plan" className="space-y-4">
          {exp.plan ? (
            <div className="surface-card rounded-lg p-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Faults
                  </p>
                  <ul className="space-y-1.5">
                    {exp.plan.faults.map((f, i) => (
                      <li
                        key={i}
                        className="rounded-md border border-border bg-card/50 px-3 py-2 font-mono text-xs"
                      >
                        {f.executor}/{f.type} → {f.target}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Watch metrics
                  </p>
                  <ul className="space-y-1.5">
                    {exp.plan.watch_metrics.map((m) => (
                      <li
                        key={m}
                        className="rounded-md border border-border bg-card/50 px-3 py-2 font-mono text-xs text-muted-foreground"
                      >
                        {m}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              <p className="mt-4 text-xs text-muted-foreground">
                Rollback: {exp.plan.rollback.type}
                {exp.plan.rollback.ttl_seconds
                  ? ` · TTL ${exp.plan.rollback.ttl_seconds}s`
                  : ''}
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Plan not available for this experiment.</p>
          )}
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          {showLivePreview ? (
            <>
              <MetricChart
                metrics={liveMetrics}
                title={resolvedEvidence ? 'Fault-window metrics' : 'Baseline metrics (live)'}
              />
              {twin?.topology && (
                <TopologyGraph
                  nodes={twin.topology.nodes}
                  edges={twin.topology.edges}
                  blastPath={twin.topology.blast_path}
                />
              )}
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Metrics available once experiment is running.</p>
          )}
        </TabsContent>

        <TabsContent value="evidence">
          <EvidencePanel
            evidence={resolvedEvidence}
            sloBreached={exp.slo_breached}
            loading={
              evidenceReady &&
              !resolvedEvidence &&
              (evidenceQuery.isLoading || captureMutation.isPending)
            }
            error={
              evidenceReady && !resolvedEvidence && captureMutation.isError
                ? 'Evidence capture failed.'
                : null
            }
            onCapture={evidenceReady ? handleCapture : undefined}
            capturing={captureMutation.isPending}
          />
        </TabsContent>

        <TabsContent value="findings" className="space-y-3">
          {showFindings ? (
            <>
              {(remediationQuery.data?.findings ?? []).length > 0 ? (
                (remediationQuery.data?.findings ?? []).map((f) => (
                  <div key={f.id} className="surface-card rounded-lg p-4">
                    <Badge variant="outline">{f.severity}</Badge>
                    <span className="ml-2 text-sm font-medium">{f.title}</span>
                    <p className="mt-2 text-xs text-muted-foreground">{f.prescription}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No findings yet — run the remediator agent.</p>
              )}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={runRemediation.isPending}
                  onClick={() =>
                    runRemediation.mutate(id, {
                      onSuccess: (r) => toast.success(`${r.findings_count} findings (${r.mode})`),
                    })
                  }
                >
                  Run remediation
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <Link to="/remediation">Open pipeline</Link>
                </Button>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Findings appear after experiment completes.</p>
          )}
        </TabsContent>
      </Tabs>
    </PageShell>
  )
}
