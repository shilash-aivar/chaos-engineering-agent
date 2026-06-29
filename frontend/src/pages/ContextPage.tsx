import { useMemo, useState } from 'react'
import { Database, FileCode2, GitBranch, History, Loader2, RefreshCw, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { PageHeader, PageShell, StatCard } from '@/components/layout/PageChrome'
import { SecurityDisclaimer } from '@/components/shared/SecurityDisclaimer'
import { useAppStore } from '@/store/appStore'
import {
  useContextAnalysis,
  useContextSnapshots,
  useContextUnderstanding,
  useAwsProbe,
  useDeleteContextSnapshot,
  useIngestContext,
  useLatestContextAgentRun,
  usePullGitHubContext,
  useRefreshContextAnalysis,
  useRunContextAgent,
} from '@/hooks/useContext'
import { useInfrastructure, useIntegrations } from '@/hooks/usePlatform'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import type { ContextAgentResult, ContextAnalysisResult } from '@/types'

const SAMPLE_TF = `resource "aws_db_instance" "payments_db" {
  identifier = "payments-db"
  engine     = "postgres"
  multi_az   = false
}

resource "aws_sqs_queue" "order_events" {
  name = "order-events"
}`

const SAMPLE_README = `# payments-service

Highly available payment processing with SLO: 99.9% availability.

- Multi-AZ Postgres (planned)
- Circuit breaker on Stripe calls
- Prometheus metrics on /metrics
`

const SAMPLE_CODE = `# src/payments/client.py
import httpx

client = httpx.AsyncClient()  # no timeout configured
`

const severityVariant = {
  critical: 'destructive',
  high: 'warning',
  medium: 'default',
  low: 'secondary',
} as const

const levelLabels: Record<string, string> = {
  infra: 'Infrastructure',
  db: 'Database',
  dependency: 'Dependency',
  app: 'Application',
  scaling: 'Scaling',
  security: 'Security',
  monitoring: 'Monitoring',
  ha: 'High availability',
  resiliency: 'Resiliency',
  reliability: 'Reliability',
}

function AnalysisSections({ analysis }: { analysis: ContextAnalysisResult }) {
  return (
    <div className="space-y-6">
      {analysis.sast_findings && analysis.sast_findings.length > 0 && (
        <section className="surface-card rounded-lg">
          <div className="border-b border-border px-5 py-4">
            <h3 className="text-sm font-semibold">SAST findings</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              tfsec / semgrep when installed; builtin heuristics otherwise
              {analysis.sast_simulated && ' (simulated scanner)'}
            </p>
          </div>
          <div className="divide-y divide-border">
            {analysis.sast_findings.map((f, i) => (
              <div key={i} className="px-5 py-4 text-xs">
                <div className="flex flex-wrap gap-2">
                  <Badge variant={f.severity === 'critical' ? 'destructive' : 'warning'}>
                    {String(f.severity)}
                  </Badge>
                  <span className="font-mono">{String(f.rule_id)}</span>
                </div>
                <p className="mt-1">{String(f.message)}</p>
                <p className="text-muted-foreground">
                  {String(f.scanner)} · {String(f.file_path)}
                  {f.line != null && `:${String(f.line)}`}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="surface-card rounded-lg">
        <div className="border-b border-border px-5 py-4">
          <h3 className="text-sm font-semibold">Gaps — declared vs observed</h3>
        </div>
        <div className="divide-y divide-border">
          {analysis.gaps.length === 0 ? (
            <p className="px-5 py-4 text-sm text-muted-foreground">No gaps detected.</p>
          ) : (
            analysis.gaps.map((gap) => (
              <div key={gap.id} className="px-5 py-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={severityVariant[gap.severity]}>{gap.severity}</Badge>
                  <Badge variant="outline">{levelLabels[gap.level] ?? gap.level}</Badge>
                  <span className="text-sm font-medium">{gap.service}</span>
                  <span className="font-mono text-[10px] text-muted-foreground">{gap.rule}</span>
                </div>
                <p className="mt-2 text-sm">{gap.message}</p>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="text-[10px] font-medium uppercase text-muted-foreground">Declared</p>
                    <ul className="mt-1 space-y-1 text-xs text-muted-foreground">
                      {gap.declared_evidence.map((e, i) => (
                        <li key={i}>{e}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-[10px] font-medium uppercase text-muted-foreground">Observed</p>
                    <ul className="mt-1 space-y-1 text-xs text-muted-foreground">
                      {gap.observed_evidence.map((e, i) => (
                        <li key={i}>{e}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="surface-card rounded-lg">
        <div className="border-b border-border px-5 py-4">
          <h3 className="text-sm font-semibold">Blue suggestions</h3>
        </div>
        <div className="divide-y divide-border">
          {analysis.blue_suggestions.length === 0 ? (
            <p className="px-5 py-4 text-sm text-muted-foreground">No suggestions yet.</p>
          ) : (
            analysis.blue_suggestions.map((s) => (
              <div key={s.finding_id + s.target_path} className="px-5 py-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{s.artifact_type}</Badge>
                  <Badge variant="secondary">{levelLabels[s.level] ?? s.level}</Badge>
                  <span className="text-sm font-medium">{s.title}</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{s.action}</p>
                <pre className="mt-3 max-h-48 overflow-auto rounded-md bg-muted p-3 font-mono text-[11px]">
                  {s.suggested_diff}
                </pre>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  )
}

export function ContextPage() {
  const context = useAppStore((s) => s.context)
  const [repoName, setRepoName] = useState('')
  const [githubPrefix, setGithubPrefix] = useState('')
  const [uploadedFiles, setUploadedFiles] = useState<Record<string, string>>({})
  const [terraform, setTerraform] = useState('')
  const [readme, setReadme] = useState('')
  const [code, setCode] = useState('')
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [problemStatement, setProblemStatement] = useState('')
  const [serviceScope, setServiceScope] = useState('')
  const [agentResult, setAgentResult] = useState<ContextAgentResult | null>(null)

  const { data: analysis, isLoading: analysisLoading } = useContextAnalysis(context.namespace, false)
  const { data: understanding, isLoading: understandingLoading } = useContextUnderstanding(
    context.namespace,
    selectedSnapshotId ?? undefined,
  )
  const { data: awsProbe } = useAwsProbe(context.namespace, context.id)
  const { data: latestAgentRun } = useLatestContextAgentRun(context.namespace)
  const { data: snapshots } = useContextSnapshots(context.namespace)
  const { data: infrastructure } = useInfrastructure()
  const { data: integrations } = useIntegrations()
  const ingestMutation = useIngestContext()
  const pullMutation = usePullGitHubContext()
  const deleteMutation = useDeleteContextSnapshot()
  const refreshMutation = useRefreshContextAnalysis()
  const agentMutation = useRunContextAgent()

  const github = integrations?.find((i) => i.id === 'github')
  const githubConnected = github?.status === 'connected'

  const busy =
    ingestMutation.isPending ||
    pullMutation.isPending ||
    deleteMutation.isPending ||
    refreshMutation.isPending ||
    agentMutation.isPending

  const liveSnapshot = infrastructure?.snapshot
  const hasAnySource = Boolean(
    Object.keys(uploadedFiles).length || terraform.trim() || readme.trim() || code.trim(),
  )

  const uploadedSummary = useMemo(() => {
    const paths = Object.keys(uploadedFiles)
    return {
      total: paths.length,
      terraform: paths.filter((p) => p.endsWith('.tf') || p.endsWith('.tfvars')).length,
      manifests: paths.filter((p) => p.endsWith('.yaml') || p.endsWith('.yml')).length,
      docs: paths.filter((p) => /readme|\.md$|\.txt$/i.test(p)).length,
      code: paths.filter(
        (p) => !p.endsWith('.tf') && !p.endsWith('.yaml') && !p.endsWith('.yml') && !/readme|\.md$|\.txt$/i.test(p),
      ).length,
    }
  }, [uploadedFiles])

  const handleFileUpload = async (files: FileList | null) => {
    if (!files?.length) return
    const next: Record<string, string> = { ...uploadedFiles }
    await Promise.all(
      Array.from(files).map(async (file) => {
        const path = file.webkitRelativePath || file.name
        next[path] = await file.text()
      }),
    )
    setUploadedFiles(next)
    toast.success(`Loaded ${files.length} file(s)`)
  }

  const handleIngest = () => {
    const rawFiles = { ...uploadedFiles }
    if (terraform.trim()) rawFiles['pasted/terraform.tf'] = terraform
    if (readme.trim()) rawFiles['pasted/README.md'] = readme
    if (code.trim()) rawFiles['pasted/code.txt'] = code
    if (Object.keys(rawFiles).length === 0) {
      toast.error('Add files or paste source content first')
      return
    }
    ingestMutation.mutate(
      {
        repo_name: repoName.trim() || `${context.cluster}-${context.namespace}`,
        namespace: context.namespace,
        raw_files: rawFiles,
      },
      {
        onSuccess: () => {
          setActiveTab('overview')
          toast.success('Context ingested and analyzed')
        },
        onError: () => toast.error('Ingest failed'),
      },
    )
  }

  const handleGitHubPull = () => {
    pullMutation.mutate(
      {
        namespace: context.namespace,
        path_prefix: githubPrefix.trim(),
        repo_name: repoName.trim() || undefined,
      },
      {
        onSuccess: () => {
          setActiveTab('overview')
          toast.success('Pulled context from GitHub')
        },
        onError: (err) => toast.error(err instanceof Error ? err.message : 'GitHub pull failed'),
      },
    )
  }

  const handleRunAgent = () => {
    agentMutation.mutate(
      {
        problem_statement: problemStatement.trim() || 'Understand this environment for chaos engineering.',
        namespace: context.namespace,
        context_id: context.id,
        service: serviceScope.trim() || undefined,
      },
      {
        onSuccess: (result) => {
          setAgentResult(result)
          setActiveTab('agent')
          toast.success(`Context agent finished (${result.mode}, ${result.iterations} steps)`)
        },
        onError: () => toast.error('Context agent failed'),
      },
    )
  }

  const handleRefresh = () => {
    refreshMutation.mutate(context.namespace, {
      onSuccess: () => toast.success('Analysis refreshed'),
      onError: () => toast.error('Refresh failed'),
    })
  }

  const handleDelete = (snapshotId: string) => {
    deleteMutation.mutate(
      { snapshotId, namespace: context.namespace },
      {
        onSuccess: () => {
          if (selectedSnapshotId === snapshotId) setSelectedSnapshotId(null)
          toast.success('Snapshot deleted')
        },
        onError: () => toast.error('Delete failed'),
      },
    )
  }

  if (analysisLoading && understandingLoading) {
    return (
      <PageShell>
        <Skeleton className="h-24 rounded-lg" />
        <Skeleton className="mt-6 h-96 rounded-lg" />
      </PageShell>
    )
  }

  const u = understanding?.understanding
  const displayedAgentResult = agentResult ?? latestAgentRun ?? null

  return (
    <PageShell>
      <SecurityDisclaimer compact />

      <PageHeader
        title="Agent context"
        description="Read declared intent from repos and files, compare against live infrastructure, and ground experiments."
        badge={
          <>
            <Badge variant="outline" className="font-mono text-[10px]">
              {context.cluster} / {context.namespace}
            </Badge>
            {infrastructure?.live_data === false && <Badge variant="warning">observed seed data</Badge>}
            {infrastructure?.live_data && <Badge variant="success">live observed data</Badge>}
          </>
        }
        action={
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleRunAgent} disabled={busy}>
              {agentMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Agent running…
                </>
              ) : (
                'Run context agent'
              )}
            </Button>
            <Button variant="outline" onClick={handleRefresh} disabled={busy || !analysis}>
              {refreshMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              Refresh analysis
            </Button>
          </div>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-4">
        <StatCard icon={Database} label="Observed apps" value={liveSnapshot?.applications?.length ?? 0} accent="amber" />
        <StatCard icon={GitBranch} label="Dependencies" value={liveSnapshot?.dependencies?.length ?? 0} accent="teal" />
        <StatCard
          icon={FileCode2}
          label="Declared files"
          value={
            u
              ? u.declared.terraform_file_count +
                u.declared.manifest_file_count +
                u.declared.code_file_count +
                u.declared.document_count
              : '—'
          }
          accent="sky"
        />
        <StatCard icon={History} label="Snapshots" value={snapshots?.length ?? 0} accent="rose" />
      </div>

      <section className="surface-card mb-6 space-y-3 rounded-lg p-5">
        <h2 className="text-sm font-semibold">Problem statement</h2>
        <p className="text-xs text-muted-foreground">
          Describe what you want to test or understand. The agent will call integration tools in a loop until it
          grounds on real infrastructure.
        </p>
        <Textarea
          value={problemStatement}
          onChange={(e) => setProblemStatement(e.target.value)}
          placeholder="e.g. Can checkout survive payments-db failover during peak traffic?"
          className="min-h-[80px] text-sm"
        />
        <Input
          value={serviceScope}
          onChange={(e) => setServiceScope(e.target.value)}
          placeholder="Optional service scope, e.g. checkout or payments-api"
        />
      </section>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="agent">Agent summary</TabsTrigger>
          <TabsTrigger value="overview">Understanding</TabsTrigger>
          <TabsTrigger value="sources">Read sources</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="agent" className="mt-4 space-y-4">
          {!displayedAgentResult ? (
            <section className="surface-card rounded-lg p-6 text-sm text-muted-foreground">
              Run the context agent to get an LLM-grounded infrastructure summary. It will probe K8s, AWS,
              integrations, posture, and declared context via tools before summarizing.
            </section>
          ) : (
            <>
              <section className="surface-card rounded-lg p-5">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-sm font-semibold">Infrastructure summary</h2>
                  <Badge variant="outline">{displayedAgentResult.mode}</Badge>
                  <Badge variant="secondary">{displayedAgentResult.confidence} confidence</Badge>
                  <Badge variant="outline">{displayedAgentResult.iterations} iterations</Badge>
                  {displayedAgentResult.service && (
                    <Badge variant="outline">service: {displayedAgentResult.service}</Badge>
                  )}
                  {displayedAgentResult.created_at && (
                    <Badge variant="outline">
                      saved {new Date(displayedAgentResult.created_at).toLocaleString()}
                    </Badge>
                  )}
                </div>
                <p className="mt-3 text-sm leading-relaxed">{displayedAgentResult.summary}</p>
                <div className="mt-4 grid gap-4 lg:grid-cols-2">
                  <div>
                    <p className="text-[10px] font-semibold uppercase text-muted-foreground">Infrastructure</p>
                    <pre className="mt-2 whitespace-pre-wrap rounded-md bg-muted p-3 text-xs leading-relaxed">
                      {displayedAgentResult.infrastructure_overview}
                    </pre>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold uppercase text-muted-foreground">Problem framing</p>
                    <p className="mt-2 text-sm text-muted-foreground">{displayedAgentResult.problem_framing}</p>
                    {displayedAgentResult.data_gaps.length > 0 && (
                      <div className="mt-4">
                        <p className="text-[10px] font-semibold uppercase text-muted-foreground">Data gaps</p>
                        <ul className="mt-2 space-y-1 text-xs text-amber-600">
                          {displayedAgentResult.data_gaps.map((g) => (
                            <li key={g}>• {g}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </section>
              <div className="grid gap-4 lg:grid-cols-2">
                <section className="surface-card rounded-lg p-5">
                  <h3 className="text-sm font-semibold">Top risks</h3>
                  <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                    {displayedAgentResult.top_risks.length ? (
                      displayedAgentResult.top_risks.map((r) => <li key={r}>• {r}</li>)
                    ) : (
                      <li>None identified</li>
                    )}
                  </ul>
                </section>
                <section className="surface-card rounded-lg p-5">
                  <h3 className="text-sm font-semibold">Recommended chaos focus</h3>
                  <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                    {displayedAgentResult.recommended_chaos_focus.map((f) => (
                      <li key={f}>• {f}</li>
                    ))}
                  </ul>
                </section>
              </div>
              <section className="surface-card rounded-lg p-5">
                <h3 className="text-sm font-semibold">Progress</h3>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {(displayedAgentResult.progress_steps ?? []).map((step, i) => (
                    <div key={`${step.tool}-${i}`} className="rounded-md border border-border px-3 py-2 text-xs">
                      <p className="font-medium">{step.label}</p>
                      <p className="text-muted-foreground">step {step.iteration} · {step.tool}</p>
                    </div>
                  ))}
                </div>
              </section>
              <section className="surface-card rounded-lg p-5">
                <h3 className="text-sm font-semibold">Tool trace</h3>
                <p className="mt-1 text-xs text-muted-foreground">
                  Tools the agent called while building understanding
                </p>
                <div className="mt-3 max-h-64 space-y-2 overflow-auto">
                  {displayedAgentResult.tool_trace.map((t, i) => (
                    <div key={`${t.tool}-${i}`} className="rounded-md border border-border px-3 py-2 text-xs">
                      <span className="font-mono font-medium">{t.tool}</span>
                      <span className="text-muted-foreground"> · step {t.iteration}</span>
                      {t.result_preview && (
                        <p className="mt-1 truncate text-muted-foreground">{t.result_preview}</p>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}
        </TabsContent>

        <TabsContent value="overview" className="mt-4 space-y-4">
          {!u ? (
            <section className="surface-card rounded-lg p-6 text-sm text-muted-foreground">
              No context ingested yet. Pull from GitHub or upload repo files on the <strong>Read sources</strong> tab.
            </section>
          ) : (
            <>
              <section className="surface-card rounded-lg p-5">
                <h2 className="text-sm font-semibold">What the agent read</h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  {understanding?.repo_name} · snapshot {understanding?.snapshot_id}
                </p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-md border border-border px-3 py-2 text-sm">
                    <p className="text-[10px] uppercase text-muted-foreground">Terraform</p>
                    <p className="font-semibold tabular-nums">{u.declared.terraform_file_count} files</p>
                  </div>
                  <div className="rounded-md border border-border px-3 py-2 text-sm">
                    <p className="text-[10px] uppercase text-muted-foreground">Manifests</p>
                    <p className="font-semibold tabular-nums">{u.declared.manifest_file_count} files</p>
                  </div>
                  <div className="rounded-md border border-border px-3 py-2 text-sm">
                    <p className="text-[10px] uppercase text-muted-foreground">Documents</p>
                    <p className="font-semibold tabular-nums">{u.declared.document_count}</p>
                  </div>
                  <div className="rounded-md border border-border px-3 py-2 text-sm">
                    <p className="text-[10px] uppercase text-muted-foreground">Code</p>
                    <p className="font-semibold tabular-nums">{u.declared.code_file_count} files</p>
                  </div>
                </div>
                {u.declared.claims.length > 0 && (
                  <div className="mt-4">
                    <p className="text-[10px] font-semibold uppercase text-muted-foreground">Declared claims</p>
                    <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                      {u.declared.claims.map((c) => (
                        <li key={c}>• {c}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>

              <div className="grid gap-4 lg:grid-cols-2">
                <section className="surface-card rounded-lg p-5">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold">Observed live (K8s + apps)</h3>
                  </div>
                  <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
                    <li>Apps: {u.observed.applications.join(', ') || '—'}</li>
                    <li>Dependencies: {u.observed.dependencies.join(', ') || '—'}</li>
                  </ul>
                </section>
                <section className="surface-card rounded-lg p-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-semibold">Observed AWS</h3>
                    {awsProbe?.source === 'live' && <Badge variant="success">live</Badge>}
                    {awsProbe?.source === 'seed' && <Badge variant="warning">seed fallback</Badge>}
                  </div>
                  {awsProbe ? (
                    <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
                      <li>
                        Region {awsProbe.region}
                        {awsProbe.account_id ? ` · account ${awsProbe.account_id}` : ''}
                      </li>
                      <li>
                        RDS ({awsProbe.counts.rds}):{' '}
                        {awsProbe.rds.map((r) => r.id).join(', ') || 'none in this account/region'}
                      </li>
                      <li>
                        SQS ({awsProbe.counts.sqs_queues}):{' '}
                        {awsProbe.sqs_queues.map((q) => q.name).join(', ') || 'none'}
                      </li>
                      <li>
                        ELB ({awsProbe.counts.load_balancers}) · ElastiCache ({awsProbe.counts.elasticache})
                      </li>
                      {awsProbe.account_match === false && (
                        <li className="text-amber-600">
                          Account mismatch — expected {awsProbe.expected_account}
                        </li>
                      )}
                      {awsProbe.fallback_reason && (
                        <li className="text-amber-600">{awsProbe.fallback_reason}</li>
                      )}
                    </ul>
                  ) : (
                    <p className="mt-3 text-xs text-muted-foreground">Probing AWS…</p>
                  )}
                  <p className="mt-3 text-[10px] text-muted-foreground">
                    Configure profile/region in Integrations → AWS, or set <code>aws_region</code> on the target context.
                  </p>
                </section>
              </div>

              <section className="surface-card rounded-lg p-5">
                <h3 className="text-sm font-semibold">Alignment</h3>
                <div className="mt-3 space-y-2 text-xs">
                  <p>
                    <span className="text-muted-foreground">Matched:</span>{' '}
                    {u.alignment.matched_resources.join(', ') || 'none'}
                  </p>
                  <p>
                    <span className="text-muted-foreground">Declared only:</span>{' '}
                    {u.alignment.declared_not_observed.join(', ') || 'none'}
                  </p>
                  <p>
                    <span className="text-muted-foreground">Observed only:</span>{' '}
                    {u.alignment.observed_not_declared.join(', ') || 'none'}
                  </p>
                </div>
              </section>

              {(u.declared.manifest_hints.length > 0 || u.declared.code_hints.length > 0) && (
                <section className="surface-card rounded-lg p-5">
                  <h3 className="text-sm font-semibold">Signals extracted</h3>
                  <ul className="mt-3 max-h-48 space-y-1 overflow-auto text-xs text-muted-foreground">
                    {[...u.declared.manifest_hints, ...u.declared.code_hints].map((h) => (
                      <li key={h}>{h}</li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="sources" className="mt-4">
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="surface-card space-y-4 rounded-lg p-5">
              <h2 className="text-sm font-semibold">Pull from GitHub</h2>
              {githubConnected ? (
                <>
                  <p className="text-xs text-muted-foreground">Connected to {github?.detail}</p>
                  <Input
                    value={githubPrefix}
                    onChange={(e) => setGithubPrefix(e.target.value)}
                    placeholder="Path prefix (optional) e.g. infra/terraform"
                  />
                  <Button onClick={handleGitHubPull} disabled={busy}>
                    {pullMutation.isPending ? 'Pulling…' : 'Pull repo context'}
                  </Button>
                </>
              ) : (
                <p className="text-xs text-muted-foreground">
                  GitHub not connected.{' '}
                  <Link to="/integrations" className="text-primary underline">
                    Configure in Integrations
                  </Link>
                </p>
              )}
            </section>

            <section className="surface-card space-y-4 rounded-lg p-5">
              <h2 className="text-sm font-semibold">Upload files</h2>
              <Input type="file" multiple onChange={(e) => void handleFileUpload(e.target.files)} />
              {uploadedSummary.total > 0 && (
                <p className="text-xs text-muted-foreground">
                  {uploadedSummary.total} files — {uploadedSummary.terraform} tf, {uploadedSummary.manifests} yaml,{' '}
                  {uploadedSummary.docs} docs, {uploadedSummary.code} code
                </p>
              )}
              <Input
                value={repoName}
                onChange={(e) => setRepoName(e.target.value)}
                placeholder={`Repo name (default: ${context.cluster}-${context.namespace})`}
              />
            </section>
          </div>

          <section className="surface-card mt-6 space-y-4 rounded-lg p-5">
            <h2 className="text-sm font-semibold">Or paste source content</h2>
            <div className="grid gap-4 lg:grid-cols-3">
              <Textarea
                value={terraform}
                onChange={(e) => setTerraform(e.target.value)}
                className="min-h-[120px] font-mono text-xs"
                placeholder="Terraform"
              />
              <Textarea
                value={readme}
                onChange={(e) => setReadme(e.target.value)}
                className="min-h-[120px] font-mono text-xs"
                placeholder="README / docs"
              />
              <Textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="min-h-[120px] font-mono text-xs"
                placeholder="Code / manifests"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={handleIngest} disabled={busy || !hasAnySource}>
                {ingestMutation.isPending ? 'Analyzing…' : 'Ingest & understand'}
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={busy}
                onClick={() => {
                  setTerraform(SAMPLE_TF)
                  setReadme(SAMPLE_README)
                  setCode(SAMPLE_CODE)
                  setRepoName('payments-service')
                }}
              >
                Load sample demo
              </Button>
            </div>
          </section>
        </TabsContent>

        <TabsContent value="analysis" className="mt-4">
          {!analysis ? (
            <section className="surface-card rounded-lg p-6 text-sm text-muted-foreground">
              No analysis yet. Ingest context from the Read sources tab first.
            </section>
          ) : (
            <AnalysisSections analysis={analysis} />
          )}
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          <section className="surface-card rounded-lg">
            <div className="border-b border-border px-5 py-4">
              <h3 className="text-sm font-semibold">Ingestion history</h3>
            </div>
            <div className="divide-y divide-border">
              {!snapshots?.length ? (
                <p className="px-5 py-4 text-sm text-muted-foreground">No snapshots yet.</p>
              ) : (
                snapshots.map((s) => (
                  <div key={s.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                    <div>
                      <p className="text-sm font-medium">{s.repo_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {s.id} · {new Date(s.ingested_at).toLocaleString()}
                        {s.has_analysis && ' · analyzed'}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedSnapshotId(s.id)
                          setActiveTab('overview')
                        }}
                      >
                        View
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleDelete(s.id)} disabled={busy}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>
        </TabsContent>
      </Tabs>
    </PageShell>
  )
}
