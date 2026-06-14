import { useState } from 'react'
import { FileCode2, Loader2, RefreshCw, Upload } from 'lucide-react'
import { toast } from 'sonner'
import { PageHeader, PageShell, StatCard } from '@/components/layout/PageChrome'
import { SecurityDisclaimer } from '@/components/shared/SecurityDisclaimer'
import { useAppStore } from '@/store/appStore'
import { useContextAnalysis, useIngestContext, useRefreshContextAnalysis } from '@/hooks/useContext'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'

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

# src/config/database.py
POOL_SIZE = 10
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

export function ContextPage() {
  const context = useAppStore((s) => s.context)
  const { data: analysis, isLoading, isError } = useContextAnalysis(context.namespace)
  const ingestMutation = useIngestContext()
  const refreshMutation = useRefreshContextAnalysis()

  const [repoName, setRepoName] = useState('payments-service')
  const [terraform, setTerraform] = useState(SAMPLE_TF)
  const [readme, setReadme] = useState(SAMPLE_README)
  const [code, setCode] = useState(SAMPLE_CODE)

  const handleIngest = () => {
    ingestMutation.mutate(
      {
        repo_name: repoName,
        namespace: context.namespace,
        terraform_files: { 'infra/rds.tf': terraform },
        readme_content: readme,
        code_files: { 'src/payments/client.py': code },
      },
      {
        onSuccess: () => toast.success('Context ingested and analyzed'),
        onError: () => toast.error('Ingest failed'),
      },
    )
  }

  const handleRefresh = () => {
    refreshMutation.mutate(context.namespace, {
      onSuccess: () => toast.success('Analysis refreshed'),
      onError: () => toast.error('Refresh failed'),
    })
  }

  const busy = ingestMutation.isPending || refreshMutation.isPending

  if (isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-24 rounded-lg" />
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-96 rounded-lg" />
          <Skeleton className="h-96 rounded-lg" />
        </div>
      </PageShell>
    )
  }

  return (
    <PageShell>
      <SecurityDisclaimer compact />

      <PageHeader
        title="Context ingestion"
        description="Upload Terraform, README, and code snippets. Agents compare declared intent against live infrastructure and posture."
        badge={
          <Badge variant="outline" className="font-mono text-[10px]">
            {context.namespace}
          </Badge>
        }
        action={
          <Button variant="outline" onClick={handleRefresh} disabled={busy}>
            {refreshMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Refresh analysis
          </Button>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard
          icon={FileCode2}
          label="TF resources"
          value={analysis?.declared_summary.terraform_resources ?? 0}
          accent="amber"
        />
        <StatCard
          icon={Upload}
          label="Documents"
          value={analysis?.declared_summary.documents ?? 0}
          accent="teal"
        />
        <StatCard
          icon={FileCode2}
          label="Code hints"
          value={analysis?.declared_summary.code_hints ?? 0}
          accent="sky"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="surface-card space-y-4 rounded-lg p-5">
          <h2 className="text-sm font-semibold">Provide context</h2>
          <p className="text-xs text-muted-foreground">
            Cluster {context.cluster} · namespace {context.namespace}
          </p>
          <div>
            <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Repository name
            </label>
            <Input value={repoName} onChange={(e) => setRepoName(e.target.value)} className="mt-1" />
          </div>
          <div>
            <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Terraform
            </label>
            <Textarea
              value={terraform}
              onChange={(e) => setTerraform(e.target.value)}
              className="mt-1 min-h-[140px] font-mono text-xs"
            />
          </div>
          <div>
            <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              README
            </label>
            <Textarea
              value={readme}
              onChange={(e) => setReadme(e.target.value)}
              className="mt-1 min-h-[100px] font-mono text-xs"
            />
          </div>
          <div>
            <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Code snippets
            </label>
            <Textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="mt-1 min-h-[100px] font-mono text-xs"
            />
          </div>
          <Button onClick={handleIngest} disabled={busy || !repoName.trim()}>
            {ingestMutation.isPending ? 'Analyzing…' : 'Ingest & analyze'}
          </Button>
        </section>

        <section className="surface-card rounded-lg p-5">
          <h2 className="text-sm font-semibold">Declared summary</h2>
          {isError || !analysis ? (
            <p className="mt-4 text-sm text-muted-foreground">
              No context ingested yet. Use the sample data and click Ingest & analyze.
            </p>
          ) : (
            <div className="mt-4 space-y-4">
              <p className="text-xs text-muted-foreground">
                {analysis.repo_name} · scanned {new Date(analysis.scanned_at).toLocaleString()} ·{' '}
                {analysis.gaps.length} gaps · {analysis.blue_suggestions.length} Blue suggestions
              </p>
              {Object.entries(analysis.posture_summary).map(([scope, count]) => (
                <div key={scope} className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm">
                  <span className="capitalize text-muted-foreground">{scope}</span>
                  <span className="font-semibold tabular-nums">{count} posture gaps</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {analysis && (
        <div className="mt-6 space-y-6">
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
                      {f.cwe != null && f.cwe !== '' && (
                        <span className="text-muted-foreground">{String(f.cwe)}</span>
                      )}
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
              {analysis.gaps.map((gap) => (
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
              ))}
            </div>
          </section>

          <section className="surface-card rounded-lg">
            <div className="border-b border-border px-5 py-4">
              <h3 className="text-sm font-semibold">Blue suggestions</h3>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Rule-based prescriptions with Terraform, manifest, and code diffs
              </p>
            </div>
            <div className="divide-y divide-border">
              {analysis.blue_suggestions.map((s) => (
                <div key={s.finding_id + s.target_path} className="px-5 py-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline">{s.artifact_type}</Badge>
                    <Badge variant="secondary">{levelLabels[s.level] ?? s.level}</Badge>
                    <span className="text-sm font-medium">{s.title}</span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{s.action}</p>
                  <p className="mt-1 font-mono text-[10px] text-muted-foreground">{s.target_path}</p>
                  <pre className="mt-3 max-h-48 overflow-auto rounded-md bg-muted p-3 font-mono text-[11px]">
                    {s.suggested_diff}
                  </pre>
                  {s.requires_approval && (
                    <Badge variant="warning" className="mt-2">
                      Requires approval
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </PageShell>
  )
}
